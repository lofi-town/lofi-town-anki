from __future__ import annotations

import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import urlopen

import pytest

from addon.oauth_callback import OAuthCallbackServer


def _get(url: str) -> tuple[int, str]:
    try:
        with urlopen(url, timeout=2) as response:
            return response.status, response.read().decode("utf-8")
    except HTTPError as error:
        return error.code, error.read().decode("utf-8")


def _wait_until(predicate: object, timeout: float = 2) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if callable(predicate) and predicate():
            return
        time.sleep(0.01)
    raise AssertionError("Condition did not become true.")


def test_accepts_one_valid_code_without_logging(
    capsys: pytest.CaptureFixture[str],
) -> None:
    callbacks: list[str] = []
    server = OAuthCallbackServer(callbacks.append, timeout_seconds=2)
    callback_url = server.start()

    status, body = _get(f"{callback_url}?code=secret-code")
    assert status == 200
    assert "return to Anki" in body
    assert callbacks and "code=secret-code" in callbacks[0]
    _wait_until(lambda: not server.running)
    assert capsys.readouterr() == ("", "")


def test_keeps_listening_after_wrong_path_and_malformed_callback() -> None:
    callbacks: list[str] = []
    server = OAuthCallbackServer(callbacks.append, timeout_seconds=2)
    callback_url = server.start()
    parsed = urlsplit(callback_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    assert _get(f"{origin}/wrong?code=value")[0] == 404
    assert _get(f"{callback_url}?state=missing-code")[0] == 400
    assert server.running
    assert _get(f"{callback_url}?error=access_denied&error_description=No")[0] == 200
    assert len(callbacks) == 1
    assert "error=access_denied" in callbacks[0]
    server.stop()


def test_rejects_duplicate_callback() -> None:
    callbacks: list[str] = []
    server = OAuthCallbackServer(callbacks.append, timeout_seconds=2)
    callback_url = server.start()
    target = f"{urlsplit(callback_url).path}?code=first"
    assert server._accept_request(target)[0] == 200
    assert server._accept_request(target)[0] == 410
    assert len(callbacks) == 1
    server.stop()


def test_rejects_oversized_request_target() -> None:
    server = OAuthCallbackServer(lambda _url: None, timeout_seconds=2)
    callback_url = server.start()
    target = f"{urlsplit(callback_url).path}?code={'x' * 5000}"
    assert server._accept_request(target)[0] == 414
    server.stop()


def test_times_out_and_cancels_cleanly() -> None:
    server = OAuthCallbackServer(lambda _url: None, timeout_seconds=0.05)
    callback_url = server.start()
    _wait_until(lambda: not server.running)
    with pytest.raises(OSError):
        urlopen(f"{callback_url}?code=late", timeout=0.2)

    restarted = server.start()
    assert server.running
    server.cancel()
    assert not server.running
    with pytest.raises(OSError):
        urlopen(f"{restarted}?code=cancelled", timeout=0.2)
