from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .focus_sync import (
    FOCUS_MINUTES,
    FocusIntent,
    FocusRequest,
    FocusState,
    decode_focus_state,
)
from .session import SessionPhase, SessionSummary, StudySession


@dataclass(frozen=True, slots=True)
class ReviewSessionConfig:
    enabled: bool
    session_hud: bool
    sync_focus: bool
    focus_minutes: int
    target_answers: int

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ReviewSessionConfig:
        return cls(
            enabled=config["enabled"],
            session_hud=config["session_hud"],
            sync_focus=config["sync_focus_with_lofi_town"],
            focus_minutes=config["focus_minutes"],
            target_answers=config["session_target_answers"],
        )

    @property
    def active(self) -> bool:
        return self.enabled and self.session_hud

    @property
    def sync_enabled(self) -> bool:
        return self.active and self.sync_focus

    @property
    def sync_minutes(self) -> int:
        return self.focus_minutes if self.focus_minutes in FOCUS_MINUTES else 0


@dataclass(frozen=True, slots=True)
class CommandOutcome:
    show_town: bool = False


class ReviewSessionController:
    def __init__(
        self,
        publish_focus_request: Callable[[FocusRequest | None], None],
        *,
        session: StudySession | None = None,
        focus_intent: FocusIntent | None = None,
    ) -> None:
        self._publish_focus_request = publish_focus_request
        self.session = session or StudySession()
        self.focus_intent = focus_intent or FocusIntent()
        self.focus_state: FocusState | None = None
        self._pending_summary: SessionSummary | None = None
        self._commands: dict[
            str, Callable[[ReviewSessionConfig], CommandOutcome]
        ] = {
            "lofi-town:pause-focus": self._pause,
            "lofi-town:resume-focus": self._resume,
            "lofi-town:restart-focus": self._restart_focus,
            "lofi-town:start-break": self._start_break,
            "lofi-town:restart-target": self._restart_target,
            "lofi-town:take-break": self._take_break,
        }

    def record_answer(self, config: ReviewSessionConfig) -> bool:
        if not config.active:
            return False
        first_answer = self.session.answers == 0
        if first_answer:
            self._pending_summary = None
        self.session.record_answer()
        if first_answer and config.sync_enabled:
            request = self.focus_intent.start(config.sync_minutes)
            self.focus_state = {
                "reviewSessionId": request["reviewSessionId"],
                "status": "starting",
                "ownedByAnki": False,
                "lofiSessionId": None,
                "focusedMs": 0,
                "message": "Connecting to Lofi Town",
            }
            self._publish_focus_request(request)
        return True

    def finish(self, config: ReviewSessionConfig) -> None:
        if self.session.answers:
            self._pending_summary = self.session.summary(
                config.focus_minutes,
                config.target_answers,
            )
        self._end_focus_sync(config)
        self.session.reset()

    def close(self, config: ReviewSessionConfig) -> None:
        self._end_focus_sync(config)
        self.reset()

    def reset(self) -> None:
        self.session.reset()
        self.focus_intent.reset()
        self.focus_state = None
        self._pending_summary = None

    def apply_config_change(
        self,
        previous: ReviewSessionConfig,
        current: ReviewSessionConfig,
    ) -> None:
        if previous.sync_enabled and not current.sync_enabled:
            self._publish_focus_request(self.focus_intent.end())
        if not current.active:
            self.session.reset()

    def report_focus_state(
        self,
        raw: str,
        config: ReviewSessionConfig,
    ) -> bool:
        try:
            state = decode_focus_state(raw)
        except ValueError:
            return False
        if state["reviewSessionId"] != self.focus_intent.review_session_id:
            return False
        self.focus_state = state
        if state["ownedByAnki"] and state["status"] == "paused":
            self.session.pause_focus()
        elif state["ownedByAnki"] and state["status"] == "focusing":
            if self.session.phase is not SessionPhase.BREAK:
                self.session.resume_focus()
        elif state["status"] == "ended":
            self.session.pause_focus()
            self.focus_intent.end()
        return config.active

    def handle_command(
        self,
        command: str,
        config: ReviewSessionConfig,
    ) -> CommandOutcome | None:
        if not config.active:
            return None
        handler = self._commands.get(command)
        return handler(config) if handler is not None else None

    def payload(self, config: ReviewSessionConfig) -> dict[str, object]:
        payload: dict[str, object] = dict(self.session.payload())
        if not config.sync_enabled:
            sync_status = "disabled"
            sync_message = ""
        elif self.session.phase is SessionPhase.READY:
            sync_status = "ready"
            sync_message = "Starts after your first answer"
        elif self.focus_state is None:
            sync_status = "starting"
            sync_message = ""
        else:
            sync_status = self.focus_state["status"]
            sync_message = self.focus_state["message"]
        payload.update(
            syncEnabled=config.sync_enabled,
            syncStatus=sync_status,
            syncMessage=sync_message,
        )
        return payload

    def take_summary(self) -> SessionSummary | None:
        summary = self._pending_summary
        self._pending_summary = None
        return summary

    def peek_summary(self) -> SessionSummary | None:
        return self._pending_summary

    def _pause(self, config: ReviewSessionConfig) -> CommandOutcome:
        self.session.pause_focus()
        if self._can_control_remote(config):
            self._publish_focus_request(self.focus_intent.pause())
        return CommandOutcome()

    def _resume(self, config: ReviewSessionConfig) -> CommandOutcome:
        if not self.session.resume_focus():
            return CommandOutcome()
        if self._can_control_remote(config):
            self._publish_focus_request(self.focus_intent.resume())
        return CommandOutcome()

    def _restart_focus(self, config: ReviewSessionConfig) -> CommandOutcome:
        self.session.restart_focus_block(config.focus_minutes)
        if (
            self.focus_intent.desired_state == "paused"
            and self._can_control_remote(config)
        ):
            self._publish_focus_request(self.focus_intent.resume())
        return CommandOutcome()

    def _start_break(self, config: ReviewSessionConfig) -> CommandOutcome:
        self.session.start_break()
        if self._can_control_remote(config):
            self._publish_focus_request(self.focus_intent.pause())
        return CommandOutcome()

    def _restart_target(self, config: ReviewSessionConfig) -> CommandOutcome:
        self.session.restart_answer_target(config.target_answers)
        return CommandOutcome()

    def _take_break(self, config: ReviewSessionConfig) -> CommandOutcome:
        self._start_break(config)
        return CommandOutcome(show_town=True)

    def _can_control_remote(self, config: ReviewSessionConfig) -> bool:
        if not config.sync_enabled:
            return False
        return self.focus_state is None or self.focus_state["status"] != "external"

    def _end_focus_sync(self, config: ReviewSessionConfig) -> None:
        if not config.sync_enabled:
            return
        request = self.focus_intent.end()
        if request is None:
            return
        if self.focus_state is not None:
            self.focus_state["status"] = "ending"
            self.focus_state["message"] = "Saving focus time"
        self._publish_focus_request(request)
