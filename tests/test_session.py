from __future__ import annotations

from addon.session import StudySession


def test_tracks_answers_and_independent_focus_time() -> None:
    now = [100.0]
    session = StudySession(clock=lambda: now[0])

    assert session.payload() == {
        "startedAt": 0,
        "focusStartedAt": 0,
        "focusPausedAt": 0,
        "focusPausedTotal": 0,
        "answers": 0,
    }

    now[0] = 105.0
    session.record_answer()
    session.record_answer()
    now[0] = 110.0
    session.restart_focus_block()

    assert session.answers == 2
    assert session.started_at_ms == 105_000
    assert session.focus_started_at_ms == 110_000


def test_pause_resume_and_reset_are_idempotent() -> None:
    now = [20.0]
    session = StudySession(clock=lambda: now[0])
    session.start()

    now[0] = 25.0
    session.pause_focus()
    session.pause_focus()
    now[0] = 31.0
    session.resume_focus()
    session.resume_focus()

    assert session.focus_paused_at_ms == 0
    assert session.focus_paused_total_ms == 6_000

    session.reset()
    assert session.started_at_ms == 0
    assert session.focus_started_at_ms == 0
    assert session.answers == 0
