from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, TypedDict, cast
from uuid import UUID, uuid4

FOCUS_DESIRED_STATES = frozenset({"focusing", "paused", "ended"})
FOCUS_STATUSES = frozenset(
    {
        "signed_out",
        "unavailable",
        "external",
        "starting",
        "focusing",
        "paused",
        "ending",
        "ended",
        "error",
    }
)
FOCUS_MINUTES = frozenset({0, 15, 25, 50})

_REQUEST_KEYS = frozenset({"reviewSessionId", "desiredState", "focusMinutes"})
_STATE_KEYS = frozenset(
    {
        "reviewSessionId",
        "status",
        "ownedByAnki",
        "lofiSessionId",
        "focusedMs",
        "message",
    }
)

FocusDesiredState = Literal["focusing", "paused", "ended"]
FocusStatus = Literal[
    "signed_out",
    "unavailable",
    "external",
    "starting",
    "focusing",
    "paused",
    "ending",
    "ended",
    "error",
]


class FocusRequest(TypedDict):
    reviewSessionId: str
    desiredState: FocusDesiredState
    focusMinutes: int


class FocusState(TypedDict):
    reviewSessionId: str
    status: FocusStatus
    ownedByAnki: bool
    lofiSessionId: str | None
    focusedMs: int
    message: str


def normalize_focus_request(raw: Any) -> FocusRequest | None:
    if raw is None:
        return None
    if not isinstance(raw, dict) or set(raw) != _REQUEST_KEYS:
        raise ValueError("Invalid focus request fields.")
    review_session_id = _review_session_id(raw.get("reviewSessionId"))
    desired_state = raw.get("desiredState")
    focus_minutes = raw.get("focusMinutes")
    if (
        not isinstance(desired_state, str)
        or desired_state not in FOCUS_DESIRED_STATES
    ):
        raise ValueError("Invalid desired focus state.")
    if (
        isinstance(focus_minutes, bool)
        or not isinstance(focus_minutes, int)
        or focus_minutes not in FOCUS_MINUTES
    ):
        raise ValueError("Invalid focus length.")
    return {
        "reviewSessionId": review_session_id,
        "desiredState": cast(FocusDesiredState, desired_state),
        "focusMinutes": focus_minutes,
    }


def normalize_focus_state(raw: Any) -> FocusState:
    if not isinstance(raw, dict) or set(raw) != _STATE_KEYS:
        raise ValueError("Invalid focus state fields.")
    review_session_id = _review_session_id(raw.get("reviewSessionId"))
    status = raw.get("status")
    owned_by_anki = raw.get("ownedByAnki")
    lofi_session_id = raw.get("lofiSessionId")
    focused_ms = raw.get("focusedMs")
    message = raw.get("message")
    if not isinstance(status, str) or status not in FOCUS_STATUSES:
        raise ValueError("Invalid focus status.")
    if not isinstance(owned_by_anki, bool):
        raise ValueError("Invalid focus ownership.")
    if lofi_session_id is not None and (
        not isinstance(lofi_session_id, str)
        or not lofi_session_id
        or len(lofi_session_id) > 128
    ):
        raise ValueError("Invalid Lofi Town session identifier.")
    if (
        isinstance(focused_ms, bool)
        or not isinstance(focused_ms, int)
        or not 0 <= focused_ms <= 31_536_000_000
    ):
        raise ValueError("Invalid focused duration.")
    if not isinstance(message, str) or len(message) > 160:
        raise ValueError("Invalid focus status message.")
    return {
        "reviewSessionId": review_session_id,
        "status": cast(FocusStatus, status),
        "ownedByAnki": owned_by_anki,
        "lofiSessionId": lofi_session_id,
        "focusedMs": focused_ms,
        "message": message,
    }


def decode_focus_state(raw: str) -> FocusState:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("Invalid focus state JSON.") from error
    return normalize_focus_state(payload)


def _review_session_id(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("Invalid review session identifier.")
    try:
        parsed = UUID(value)
    except ValueError as error:
        raise ValueError("Invalid review session identifier.") from error
    if str(parsed) != value:
        raise ValueError("Invalid review session identifier.")
    return value


@dataclass(slots=True)
class FocusIntent:
    identifier_factory: Callable[[], str] = lambda: str(uuid4())
    review_session_id: str = ""
    desired_state: FocusDesiredState = "ended"
    focus_minutes: int = 0

    def start(self, focus_minutes: int) -> FocusRequest:
        if focus_minutes not in FOCUS_MINUTES:
            raise ValueError("Invalid focus length.")
        if not self.review_session_id or self.desired_state == "ended":
            self.review_session_id = self.identifier_factory()
            self.focus_minutes = focus_minutes
        self.desired_state = "focusing"
        return self._payload()

    def pause(self) -> FocusRequest | None:
        return self._set_active_state("paused")

    def resume(self) -> FocusRequest | None:
        return self._set_active_state("focusing")

    def end(self) -> FocusRequest | None:
        if not self.review_session_id or self.desired_state == "ended":
            return None
        self.desired_state = "ended"
        return self._payload()

    def reset(self) -> None:
        self.review_session_id = ""
        self.desired_state = "ended"
        self.focus_minutes = 0

    def _payload(self) -> FocusRequest:
        return {
            "reviewSessionId": self.review_session_id,
            "desiredState": self.desired_state,
            "focusMinutes": self.focus_minutes,
        }

    def _set_active_state(
        self, state: Literal["focusing", "paused"]
    ) -> FocusRequest | None:
        if not self.review_session_id or self.desired_state == "ended":
            return None
        self.desired_state = state
        return self._payload()
