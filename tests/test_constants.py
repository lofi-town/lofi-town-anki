from __future__ import annotations

import pytest

from addon.constants import _app_endpoints


def test_app_endpoints_default_to_production() -> None:
    assert _app_endpoints(None) == (
        "https://app.lofi.town/?ref=anki",
        "https://app.lofi.town",
    )


@pytest.mark.parametrize(
    ("value", "origin"),
    [
        ("http://localhost:3000", "http://localhost:3000"),
        ("http://127.0.0.1:3000/", "http://127.0.0.1:3000"),
        ("http://[::1]:3000", "http://[::1]:3000"),
    ],
)
def test_app_endpoints_allow_loopback_development_origins(
    value: str, origin: str
) -> None:
    assert _app_endpoints(value) == (f"{origin}/?ref=anki", origin)


@pytest.mark.parametrize(
    "value",
    [
        "https://localhost:3000",
        "http://lofi.test:3000",
        "http://192.168.1.4:3000",
        "http://user:password@localhost:3000",
        "http://localhost:3000/path",
        "http://localhost:3000?token=value",
        "http://localhost:3000#fragment",
        "http://localhost:not-a-port",
        "http://localhost:70000",
    ],
)
def test_app_endpoints_reject_non_loopback_or_credentialed_origins(
    value: str,
) -> None:
    with pytest.raises(ValueError, match="plain HTTP loopback origin"):
        _app_endpoints(value)
