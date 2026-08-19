from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class StudySession:
    clock: Callable[[], float] = time.time
    started_at_ms: int = 0
    focus_started_at_ms: int = 0
    focus_paused_at_ms: int = 0
    focus_paused_total_ms: int = 0
    answers: int = 0

    def start(self) -> None:
        if not self.started_at_ms:
            now = round(self.clock() * 1000)
            self.started_at_ms = now
            self.focus_started_at_ms = now

    def record_answer(self) -> None:
        self.start()
        self.answers += 1

    def pause_focus(self) -> None:
        self.start()
        if not self.focus_paused_at_ms:
            self.focus_paused_at_ms = round(self.clock() * 1000)

    def resume_focus(self) -> None:
        if not self.focus_paused_at_ms:
            return
        now = round(self.clock() * 1000)
        self.focus_paused_total_ms += max(0, now - self.focus_paused_at_ms)
        self.focus_paused_at_ms = 0

    def restart_focus_block(self) -> None:
        self.start()
        self.focus_started_at_ms = round(self.clock() * 1000)
        self.focus_paused_at_ms = 0
        self.focus_paused_total_ms = 0

    def reset(self) -> None:
        self.started_at_ms = 0
        self.focus_started_at_ms = 0
        self.focus_paused_at_ms = 0
        self.focus_paused_total_ms = 0
        self.answers = 0

    def payload(self) -> dict[str, int]:
        return {
            "startedAt": self.started_at_ms,
            "focusStartedAt": self.focus_started_at_ms,
            "focusPausedAt": self.focus_paused_at_ms,
            "focusPausedTotal": self.focus_paused_total_ms,
            "answers": self.answers,
        }
