from __future__ import annotations

from addon.review_session import ReviewSessionConfig, ReviewSessionController
from addon.session import SessionPhase, StudySession


def config(
    *,
    focus_minutes: int = 25,
    target_answers: int = 0,
) -> ReviewSessionConfig:
    return ReviewSessionConfig(
        enabled=True,
        session_hud=True,
        focus_minutes=focus_minutes,
        target_answers=target_answers,
    )


def controller(now: list[float]) -> ReviewSessionController:
    return ReviewSessionController(
        session=StudySession(clock=lambda: now[0]),
    )


def test_first_answer_starts_local_session() -> None:
    now = [10.0]
    review = controller(now)

    assert review.record_answer(config(focus_minutes=37)) is True
    review.record_answer(config(focus_minutes=37))

    assert review.session.started_at_ms == 10_000
    assert review.session.answers == 2


def test_break_controls_are_local_and_non_modal() -> None:
    now = [10.0]
    review = controller(now)
    settings = config()
    review.record_answer(settings)
    now[0] = 20.0

    outcome = review.handle_command("lofi-town:take-break", settings)

    assert outcome is not None
    assert outcome.show_town is True
    assert review.session.phase is SessionPhase.BREAK
    assert review.session.focused_ms() == 10_000


def test_finish_exposes_one_typed_summary() -> None:
    now = [10.0]
    review = controller(now)
    settings = config(focus_minutes=1, target_answers=1)
    review.record_answer(settings)
    now[0] = 70.0

    review.finish(settings)
    summary = review.take_summary()

    assert summary is not None
    assert summary.to_payload() == {
        "answers": 1,
        "focusedMs": 60_000,
        "blocksCompleted": 1,
        "targetAnswers": 1,
        "targetProgress": 1,
        "targetsCompleted": 1,
    }
    assert review.take_summary() is None
    assert review.session.phase is SessionPhase.READY


def test_unknown_or_disabled_commands_are_not_claimed() -> None:
    review = controller([10.0])
    disabled = ReviewSessionConfig(
        enabled=True,
        session_hud=False,
        focus_minutes=25,
        target_answers=0,
    )

    assert review.handle_command("lofi-town:unknown", config()) is None
    assert review.handle_command("lofi-town:pause-focus", disabled) is None


def test_disabling_hud_resets_local_session() -> None:
    review = controller([10.0])
    review.record_answer(config())
    disabled = ReviewSessionConfig(
        enabled=True,
        session_hud=False,
        focus_minutes=25,
        target_answers=0,
    )

    review.apply_config_change(disabled)

    assert review.session.phase is SessionPhase.READY
    assert review.session.answers == 0


def test_reviewer_payload_contains_only_aggregate_session_state() -> None:
    review = controller([10.0])
    review.record_answer(config())

    payload = review.payload()

    assert set(payload) == {
        "phase",
        "startedAt",
        "focusStartedAt",
        "focusPausedAt",
        "focusPausedTotal",
        "completedFocusMs",
        "breakStartedAt",
        "answers",
        "targetStartedAnswers",
    }
    for forbidden in ("card", "deck", "rating", "remaining"):
        assert forbidden not in {key.lower() for key in payload}
