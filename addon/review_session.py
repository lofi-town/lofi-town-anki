from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .session import SessionSummary, StudySession


@dataclass(frozen=True, slots=True)
class ReviewSessionConfig:
    enabled: bool
    session_hud: bool
    focus_minutes: int
    target_answers: int

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ReviewSessionConfig:
        return cls(
            enabled=config["enabled"],
            session_hud=config["session_hud"],
            focus_minutes=config["focus_minutes"],
            target_answers=config["session_target_answers"],
        )

    @property
    def active(self) -> bool:
        return self.enabled and self.session_hud


@dataclass(frozen=True, slots=True)
class CommandOutcome:
    show_town: bool = False


class ReviewSessionController:
    def __init__(
        self,
        *,
        session: StudySession | None = None,
    ) -> None:
        self.session = session or StudySession()
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
        return True

    def finish(self, config: ReviewSessionConfig) -> None:
        if self.session.answers:
            self._pending_summary = self.session.summary(
                config.focus_minutes,
                config.target_answers,
            )
        self.session.reset()

    def close(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.session.reset()
        self._pending_summary = None

    def apply_config_change(self, current: ReviewSessionConfig) -> None:
        if not current.active:
            self.session.reset()

    def handle_command(
        self,
        command: str,
        config: ReviewSessionConfig,
    ) -> CommandOutcome | None:
        if not config.active:
            return None
        handler = self._commands.get(command)
        return handler(config) if handler is not None else None

    def payload(self) -> dict[str, object]:
        return dict(self.session.payload())

    def take_summary(self) -> SessionSummary | None:
        summary = self._pending_summary
        self._pending_summary = None
        return summary

    def peek_summary(self) -> SessionSummary | None:
        return self._pending_summary

    def _pause(self, config: ReviewSessionConfig) -> CommandOutcome:
        self.session.pause_focus()
        return CommandOutcome()

    def _resume(self, config: ReviewSessionConfig) -> CommandOutcome:
        self.session.resume_focus()
        return CommandOutcome()

    def _restart_focus(self, config: ReviewSessionConfig) -> CommandOutcome:
        self.session.restart_focus_block(config.focus_minutes)
        return CommandOutcome()

    def _start_break(self, config: ReviewSessionConfig) -> CommandOutcome:
        self.session.start_break()
        return CommandOutcome()

    def _restart_target(self, config: ReviewSessionConfig) -> CommandOutcome:
        self.session.restart_answer_target(config.target_answers)
        return CommandOutcome()

    def _take_break(self, config: ReviewSessionConfig) -> CommandOutcome:
        self._start_break(config)
        return CommandOutcome(show_town=True)
