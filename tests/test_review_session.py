from __future__ import annotations

import json

from addon.focus_sync import FocusIntent, FocusRequest
from addon.review_session import ReviewSessionConfig, ReviewSessionController
from addon.session import SessionPhase, StudySession

REVIEW_SESSION_ID = "00000000-0000-4000-8000-000000000001"


def config(
    *,
    sync: bool = True,
    focus_minutes: int = 25,
    target_answers: int = 0,
) -> ReviewSessionConfig:
    return ReviewSessionConfig(
        enabled=True,
        session_hud=True,
        sync_focus=sync,
        focus_minutes=focus_minutes,
        target_answers=target_answers,
    )


def controller(
    published: list[FocusRequest | None],
    now: list[float],
) -> ReviewSessionController:
    return ReviewSessionController(
        published.append,
        session=StudySession(clock=lambda: now[0]),
        focus_intent=FocusIntent(identifier_factory=lambda: REVIEW_SESSION_ID),
    )


def focus_state(status: str, *, owned: bool = True) -> str:
    return json.dumps(
        {
            "reviewSessionId": REVIEW_SESSION_ID,
            "status": status,
            "ownedByAnki": owned,
            "lofiSessionId": "lofi-session" if owned else None,
            "focusedMs": 10_000,
            "message": "",
        }
    )


def test_first_answer_starts_one_sync_request() -> None:
    published: list[FocusRequest | None] = []
    now = [10.0]
    review = controller(published, now)

    assert review.record_answer(config(focus_minutes=37)) is True
    review.record_answer(config(focus_minutes=37))

    assert review.session.answers == 2
    assert published == [
        {
            "reviewSessionId": REVIEW_SESSION_ID,
            "desiredState": "focusing",
            "focusMinutes": 0,
        }
    ]


def test_stale_focusing_report_cannot_end_a_local_break() -> None:
    published: list[FocusRequest | None] = []
    now = [10.0]
    review = controller(published, now)
    settings = config()
    review.record_answer(settings)
    now[0] = 20.0
    review.handle_command("lofi-town:start-break", settings)

    assert review.session.phase is SessionPhase.BREAK
    assert published[-1] and published[-1]["desiredState"] == "paused"

    now[0] = 40.0
    assert review.report_focus_state(focus_state("focusing"), settings) is True
    assert review.session.phase is SessionPhase.BREAK
    assert review.session.focused_ms() == 10_000


def test_external_session_blocks_remote_controls_but_not_local_timer() -> None:
    published: list[FocusRequest | None] = []
    now = [10.0]
    review = controller(published, now)
    settings = config()
    review.record_answer(settings)
    review.report_focus_state(focus_state("external", owned=False), settings)
    starts = len(published)

    outcome = review.handle_command("lofi-town:take-break", settings)

    assert outcome is not None
    assert outcome.show_town is True
    assert review.session.phase is SessionPhase.BREAK
    assert len(published) == starts
    assert review.focus_intent.desired_state == "focusing"


def test_finish_exposes_one_typed_summary_and_ends_sync() -> None:
    published: list[FocusRequest | None] = []
    now = [10.0]
    review = controller(published, now)
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
    assert published[-1] and published[-1]["desiredState"] == "ended"
    assert review.session.phase is SessionPhase.READY


def test_unknown_or_disabled_commands_are_not_claimed() -> None:
    published: list[FocusRequest | None] = []
    review = controller(published, [10.0])
    disabled = ReviewSessionConfig(
        enabled=True,
        session_hud=False,
        sync_focus=True,
        focus_minutes=25,
        target_answers=0,
    )

    assert review.handle_command("lofi-town:unknown", config()) is None
    assert review.handle_command("lofi-town:pause-focus", disabled) is None


def test_disabling_sync_ends_remote_intent_and_disabling_hud_resets_local() -> None:
    published: list[FocusRequest | None] = []
    review = controller(published, [10.0])
    active = config()
    review.record_answer(active)

    sync_disabled = config(sync=False)
    review.apply_config_change(active, sync_disabled)
    assert published[-1] and published[-1]["desiredState"] == "ended"
    assert review.session.answers == 1

    hud_disabled = ReviewSessionConfig(
        enabled=True,
        session_hud=False,
        sync_focus=False,
        focus_minutes=25,
        target_answers=0,
    )
    review.apply_config_change(sync_disabled, hud_disabled)
    assert review.session.phase is SessionPhase.READY
    assert review.session.answers == 0


def test_reviewer_payload_contains_only_aggregate_session_state() -> None:
    published: list[FocusRequest | None] = []
    review = controller(published, [10.0])
    review.record_answer(config(sync=False))

    payload = review.payload(config(sync=False))

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
        "syncEnabled",
        "syncStatus",
        "syncMessage",
    }
    for forbidden in ("card", "deck", "rating", "remaining"):
        assert forbidden not in {key.lower() for key in payload}
