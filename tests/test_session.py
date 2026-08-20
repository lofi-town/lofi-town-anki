from __future__ import annotations

from addon.session import SessionPhase, SessionSummary, StudySession


def test_tracks_answers_and_independent_focus_time() -> None:
    now = [100.0]
    session = StudySession(clock=lambda: now[0])

    assert session.payload() == {
        "phase": "ready",
        "startedAt": 0,
        "focusStartedAt": 0,
        "focusPausedAt": 0,
        "focusPausedTotal": 0,
        "completedFocusMs": 0,
        "breakStartedAt": 0,
        "answers": 0,
        "targetStartedAnswers": 0,
    }

    now[0] = 105.0
    session.record_answer()
    session.record_answer()
    now[0] = 110.0
    session.restart_focus_block(5)

    assert session.answers == 2
    assert session.started_at_ms == 105_000
    assert session.focus_started_at_ms == 110_000
    assert session.completed_focus_ms == 5_000
    assert session.completed_blocks == 0


def test_pause_resume_and_reset_are_idempotent() -> None:
    now = [20.0]
    session = StudySession(clock=lambda: now[0])
    session.start()
    assert session.phase is SessionPhase.FOCUSING

    now[0] = 25.0
    session.pause_focus()
    session.pause_focus()
    assert session.phase is SessionPhase.PAUSED
    now[0] = 31.0
    session.resume_focus()
    session.resume_focus()
    assert session.phase is SessionPhase.FOCUSING

    assert session.focus_paused_at_ms == 0
    assert session.focus_paused_total_ms == 6_000

    session.reset()
    assert session.started_at_ms == 0
    assert session.focus_started_at_ms == 0
    assert session.answers == 0


def test_tracks_targets_breaks_blocks_and_summary() -> None:
    now = [100.0]
    session = StudySession(clock=lambda: now[0])
    session.record_answer()
    session.record_answer()

    now[0] = 400.0
    session.start_break()
    assert session.break_started_at_ms == 400_000
    assert session.focus_paused_at_ms == 400_000

    summary = session.summary(focus_minutes=5, target_answers=2)
    assert session.phase is SessionPhase.BREAK
    assert summary == SessionSummary(
        answers=2,
        focused_ms=300_000,
        blocks_completed=1,
        target_answers=2,
        target_progress=2,
        targets_completed=1,
    )

    session.restart_focus_block(5)
    session.restart_answer_target(2)
    assert session.completed_focus_ms == 300_000
    assert session.completed_blocks == 1
    assert session.break_started_at_ms == 0
    assert session.target_started_answers == 2
    assert session.completed_targets == 1

    session.record_answer()
    partial = session.summary(focus_minutes=5, target_answers=2)
    assert partial.target_progress == 1
    assert partial.targets_completed == 1


def test_focus_summary_accumulates_across_blocks() -> None:
    now = [10.0]
    session = StudySession(clock=lambda: now[0])
    session.record_answer()
    now[0] = 70.0
    session.restart_focus_block(1)
    now[0] = 100.0

    summary = session.summary(focus_minutes=1, target_answers=0)
    assert summary.focused_ms == 90_000
    assert summary.blocks_completed == 1


def test_break_rejects_stale_resume_transition() -> None:
    now = [10.0]
    session = StudySession(clock=lambda: now[0])
    session.record_answer()
    now[0] = 20.0
    session.start_break()

    now[0] = 40.0
    assert session.resume_focus() is False
    assert session.phase is SessionPhase.BREAK
    assert session.focus_paused_at_ms == 20_000
    assert session.focused_ms() == 10_000
