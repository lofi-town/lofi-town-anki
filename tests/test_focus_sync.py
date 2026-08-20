from __future__ import annotations

import json

import pytest

from addon.focus_sync import (
    FocusIntent,
    decode_focus_state,
    normalize_focus_request,
    normalize_focus_state,
)

REVIEW_SESSION_ID = "00000000-0000-4000-8000-000000000001"
SECOND_REVIEW_SESSION_ID = "00000000-0000-4000-8000-000000000002"


def test_focus_intent_is_idempotent_and_rotates_after_end() -> None:
    identifiers = iter((REVIEW_SESSION_ID, SECOND_REVIEW_SESSION_ID))
    intent = FocusIntent(identifier_factory=lambda: next(identifiers))

    first = intent.start(25)
    repeated = intent.start(25)
    paused = intent.pause()
    ended = intent.end()
    restarted = intent.start(50)

    assert first == repeated
    assert paused and paused["desiredState"] == "paused"
    assert ended and ended["desiredState"] == "ended"
    assert restarted == {
        "reviewSessionId": SECOND_REVIEW_SESSION_ID,
        "desiredState": "focusing",
        "focusMinutes": 50,
    }


def test_request_schema_rejects_review_data_and_invalid_lengths() -> None:
    valid = {
        "reviewSessionId": REVIEW_SESSION_ID,
        "desiredState": "focusing",
        "focusMinutes": 25,
    }
    assert normalize_focus_request(valid) == valid

    for field in ("card", "deck", "answer", "rating", "remaining"):
        with pytest.raises(ValueError):
            normalize_focus_request({**valid, field: "private"})
    with pytest.raises(ValueError):
        normalize_focus_request({**valid, "focusMinutes": 30})
    with pytest.raises(ValueError):
        normalize_focus_request({**valid, "desiredState": {}})
    with pytest.raises(ValueError):
        normalize_focus_request({**valid, "focusMinutes": []})


def test_focus_state_schema_is_strict_and_bounded() -> None:
    valid = {
        "reviewSessionId": REVIEW_SESSION_ID,
        "status": "focusing",
        "ownedByAnki": True,
        "lofiSessionId": "focus-session-1",
        "focusedMs": 12_000,
        "message": "Synced with Lofi Town",
    }

    assert normalize_focus_state(valid) == valid
    assert decode_focus_state(json.dumps(valid)) == valid
    with pytest.raises(ValueError):
        normalize_focus_state({**valid, "answers": 12})
    with pytest.raises(ValueError):
        normalize_focus_state({**valid, "focusedMs": -1})
    with pytest.raises(ValueError):
        decode_focus_state("not json")
