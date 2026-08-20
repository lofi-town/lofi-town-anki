from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TypedDict


class SessionPhase(str, Enum):
    READY = "ready"
    FOCUSING = "focusing"
    PAUSED = "paused"
    BREAK = "break"


class SessionPayload(TypedDict):
    phase: str
    startedAt: int
    focusStartedAt: int
    focusPausedAt: int
    focusPausedTotal: int
    completedFocusMs: int
    breakStartedAt: int
    answers: int
    targetStartedAnswers: int


class SessionSummaryPayload(TypedDict):
    answers: int
    focusedMs: int
    blocksCompleted: int
    targetAnswers: int
    targetProgress: int
    targetsCompleted: int


@dataclass(frozen=True, slots=True)
class SessionSnapshot:
    phase: SessionPhase
    started_at_ms: int
    focus_started_at_ms: int
    focus_paused_at_ms: int
    focus_paused_total_ms: int
    completed_focus_ms: int
    break_started_at_ms: int
    answers: int
    target_started_answers: int

    def to_payload(self) -> SessionPayload:
        return {
            "phase": self.phase.value,
            "startedAt": self.started_at_ms,
            "focusStartedAt": self.focus_started_at_ms,
            "focusPausedAt": self.focus_paused_at_ms,
            "focusPausedTotal": self.focus_paused_total_ms,
            "completedFocusMs": self.completed_focus_ms,
            "breakStartedAt": self.break_started_at_ms,
            "answers": self.answers,
            "targetStartedAnswers": self.target_started_answers,
        }


@dataclass(frozen=True, slots=True)
class SessionSummary:
    answers: int
    focused_ms: int
    blocks_completed: int
    target_answers: int
    target_progress: int
    targets_completed: int

    def to_payload(self) -> SessionSummaryPayload:
        return {
            "answers": self.answers,
            "focusedMs": self.focused_ms,
            "blocksCompleted": self.blocks_completed,
            "targetAnswers": self.target_answers,
            "targetProgress": self.target_progress,
            "targetsCompleted": self.targets_completed,
        }


@dataclass(slots=True)
class StudySession:
    clock: Callable[[], float] = time.time
    phase: SessionPhase = SessionPhase.READY
    started_at_ms: int = 0
    focus_started_at_ms: int = 0
    focus_paused_at_ms: int = 0
    focus_paused_total_ms: int = 0
    completed_focus_ms: int = 0
    completed_blocks: int = 0
    completed_targets: int = 0
    break_started_at_ms: int = 0
    answers: int = 0
    target_started_answers: int = 0

    def start(self) -> None:
        if self.phase is SessionPhase.READY:
            now = self._now_ms()
            self.started_at_ms = now
            self.focus_started_at_ms = now
            self.phase = SessionPhase.FOCUSING

    def record_answer(self) -> None:
        self.start()
        self.answers += 1

    def pause_focus(self) -> bool:
        self.start()
        if self.phase is not SessionPhase.FOCUSING:
            return False
        self.focus_paused_at_ms = self._now_ms()
        self.phase = SessionPhase.PAUSED
        return True

    def resume_focus(self) -> bool:
        if self.phase is not SessionPhase.PAUSED:
            return False
        now = self._now_ms()
        self.focus_paused_total_ms += max(0, now - self.focus_paused_at_ms)
        self.focus_paused_at_ms = 0
        self.phase = SessionPhase.FOCUSING
        return True

    def restart_focus_block(self, focus_minutes: int = 0) -> None:
        self.start()
        now = self._now_ms()
        block_ms = self.current_block_focused_ms(now)
        self.completed_focus_ms += block_ms
        if focus_minutes and block_ms >= focus_minutes * 60 * 1000:
            self.completed_blocks += 1
        self.focus_started_at_ms = now
        self.focus_paused_at_ms = 0
        self.focus_paused_total_ms = 0
        self.break_started_at_ms = 0
        self.phase = SessionPhase.FOCUSING

    def restart_answer_target(self, target_answers: int = 0) -> None:
        target_progress = max(0, self.answers - self.target_started_answers)
        if target_answers and target_progress >= target_answers:
            self.completed_targets += 1
        self.target_started_answers = self.answers

    def start_break(self) -> None:
        self.pause_focus()
        if self.phase is not SessionPhase.BREAK:
            self.break_started_at_ms = self._now_ms()
            self.phase = SessionPhase.BREAK

    def current_block_focused_ms(self, now_ms: int | None = None) -> int:
        if not self.focus_started_at_ms:
            return 0
        now = now_ms if now_ms is not None else self._now_ms()
        effective_now = self.focus_paused_at_ms or now
        return max(
            0,
            effective_now - self.focus_started_at_ms - self.focus_paused_total_ms,
        )

    def focused_ms(self, now_ms: int | None = None) -> int:
        return self.completed_focus_ms + self.current_block_focused_ms(now_ms)

    def summary(self, focus_minutes: int, target_answers: int) -> SessionSummary:
        now = self._now_ms()
        current_block_ms = self.current_block_focused_ms(now)
        blocks_completed = self.completed_blocks
        if focus_minutes and current_block_ms >= focus_minutes * 60 * 1000:
            blocks_completed += 1
        target_progress = max(0, self.answers - self.target_started_answers)
        target_reached = target_answers > 0 and target_progress >= target_answers
        return SessionSummary(
            answers=self.answers,
            focused_ms=self.focused_ms(now),
            blocks_completed=blocks_completed,
            target_answers=target_answers,
            target_progress=target_progress,
            targets_completed=self.completed_targets + int(target_reached),
        )

    def reset(self) -> None:
        self.phase = SessionPhase.READY
        self.started_at_ms = 0
        self.focus_started_at_ms = 0
        self.focus_paused_at_ms = 0
        self.focus_paused_total_ms = 0
        self.completed_focus_ms = 0
        self.completed_blocks = 0
        self.completed_targets = 0
        self.break_started_at_ms = 0
        self.answers = 0
        self.target_started_answers = 0

    def snapshot(self) -> SessionSnapshot:
        return SessionSnapshot(
            phase=self.phase,
            started_at_ms=self.started_at_ms,
            focus_started_at_ms=self.focus_started_at_ms,
            focus_paused_at_ms=self.focus_paused_at_ms,
            focus_paused_total_ms=self.focus_paused_total_ms,
            completed_focus_ms=self.completed_focus_ms,
            break_started_at_ms=self.break_started_at_ms,
            answers=self.answers,
            target_started_answers=self.target_started_answers,
        )

    def payload(self) -> SessionPayload:
        return self.snapshot().to_payload()

    def _now_ms(self) -> int:
        return round(self.clock() * 1000)
