from __future__ import annotations

import html
import secrets
import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

MAX_REQUEST_TARGET_LENGTH = 4096
MAX_CALLBACK_VALUE_LENGTH = 2048


class CallbackResult(Enum):
    RETRY = auto()
    SUCCESS = auto()
    CANCELLED = auto()
    FAILED = auto()


@dataclass(frozen=True)
class CallbackOutcome:
    status: int
    message: str
    result: CallbackResult

    @property
    def consumed(self) -> bool:
        return self.result is not CallbackResult.RETRY

    @classmethod
    def retry(cls, status: int, message: str) -> CallbackOutcome:
        return cls(status, message, CallbackResult.RETRY)


class OAuthCallbackServer:
    def __init__(
        self,
        on_callback: Callable[[str], None],
        timeout_seconds: float,
    ) -> None:
        self._on_callback = on_callback
        self._timeout_seconds = timeout_seconds
        self._lock = threading.Lock()
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._timer: threading.Timer | None = None
        self._callback_path = ""
        self._completed = False

    @property
    def running(self) -> bool:
        with self._lock:
            return self._server is not None and not self._completed

    @property
    def callback_url(self) -> str:
        with self._lock:
            if self._server is None:
                raise RuntimeError("OAuth callback server is not running.")
            port = self._server.server_address[1]
            return f"http://127.0.0.1:{port}{self._callback_path}"

    def start(self) -> str:
        self.stop()
        token = secrets.token_urlsafe(32)
        callback_path = f"/lofi-town-anki/oauth/{token}"
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                outcome = owner._accept_request(self.path)
                payload = owner._response_page(outcome).encode("utf-8")
                self.send_response(outcome.status)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header(
                    "Content-Security-Policy",
                    "default-src 'none'; style-src 'unsafe-inline'; "
                    "base-uri 'none'; frame-ancestors 'none'",
                )
                self.end_headers()
                self.wfile.write(payload)
                if outcome.consumed:
                    threading.Thread(target=owner.stop, daemon=True).start()

            def log_message(self, _format: str, *_args: object) -> None:
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(
            target=server.serve_forever,
            name="lofi-town-anki-oauth",
            daemon=True,
        )
        timer = threading.Timer(self._timeout_seconds, self.stop)
        timer.daemon = True

        with self._lock:
            self._server = server
            self._thread = thread
            self._timer = timer
            self._callback_path = callback_path
            self._completed = False

        thread.start()
        timer.start()
        return self.callback_url

    def stop(self) -> None:
        with self._lock:
            server = self._server
            thread = self._thread
            timer = self._timer
            self._server = None
            self._thread = None
            self._timer = None
            self._callback_path = ""

        if timer is not None and timer is not threading.current_thread():
            timer.cancel()
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2)

    cancel = stop

    def _accept_request(self, request_target: str) -> CallbackOutcome:
        if len(request_target) > MAX_REQUEST_TARGET_LENGTH:
            return CallbackOutcome.retry(
                414, "The sign-in response was too large."
            )

        parsed = urlsplit(request_target)
        with self._lock:
            callback_path = self._callback_path
            completed = self._completed
            server = self._server

        if server is None or completed:
            return CallbackOutcome.retry(
                410, "This sign-in request has expired."
            )
        if parsed.path != callback_path:
            return CallbackOutcome.retry(
                404, "This is not the active Lofi Town sign-in request."
            )

        try:
            query = parse_qs(
                parsed.query,
                keep_blank_values=True,
                strict_parsing=False,
                max_num_fields=20,
            )
        except ValueError:
            return CallbackOutcome.retry(
                400, "The sign-in response was invalid."
            )

        code_values = query.get("code", [])
        error_values = query.get("error", [])
        if (len(code_values) != 1) == (len(error_values) != 1):
            return CallbackOutcome.retry(
                400, "The sign-in response was missing a code or error."
            )

        selected: dict[str, str] = {}
        if code_values:
            selected["code"] = code_values[0]
        else:
            selected["error"] = error_values[0]
            if len(query.get("error_description", [])) == 1:
                selected["error_description"] = query["error_description"][0]

        if any(
            not value or len(value) > MAX_CALLBACK_VALUE_LENGTH
            for value in selected.values()
        ):
            return CallbackOutcome.retry(
                400, "The sign-in response was invalid."
            )

        port = server.server_address[1]
        callback_url = urlunsplit(
            (
                "http",
                f"127.0.0.1:{port}",
                callback_path,
                urlencode(selected),
                "",
            )
        )

        with self._lock:
            if self._completed:
                return CallbackOutcome.retry(
                    410, "This sign-in request has already completed."
                )
            self._completed = True

        self._on_callback(callback_url)
        if error_values:
            result = (
                CallbackResult.CANCELLED
                if error_values[0] == "access_denied"
                else CallbackResult.FAILED
            )
            return CallbackOutcome(
                200,
                "No changes were made. You can close this tab and return to Anki.",
                result,
            )
        return CallbackOutcome(
            200,
            "You can close this tab and return to Anki.",
            CallbackResult.SUCCESS,
        )

    @staticmethod
    def _response_page(outcome: CallbackOutcome) -> str:
        if outcome.result is CallbackResult.SUCCESS:
            title = "Signed in"
            action = "Return to Anki"
            mark = "&#10003;"
        elif outcome.result is CallbackResult.CANCELLED:
            title = "Sign-in cancelled"
            action = "Return to Anki"
            mark = "&#10005;"
        elif outcome.result is CallbackResult.FAILED:
            title = "Sign-in failed"
            action = "Return to Anki"
            mark = "&#10005;"
        else:
            title = "Sign-in could not continue"
            action = "Close this tab and try again"
            mark = "&#10005;"
        style = "".join(
            (
                "html,body{height:100%;margin:0}",
                "body{display:grid;place-items:center;background:#f6e6c4;",
                "color:#4a2e12;font:600 16px/1.5 system-ui,sans-serif}",
                "main{width:min(420px,calc(100% - 40px));padding:34px;",
                "border:1px solid #f0e2c4;border-radius:24px;",
                "background:#fffdf5;text-align:center;",
                "box-shadow:0 18px 45px rgba(74,46,18,.16)}",
                ".mark{width:54px;height:54px;margin:0 auto 18px;",
                "border-radius:18px;background:#ffe7bf;display:grid;",
                "place-items:center;font-size:28px}",
                "h1{margin:0 0 8px;font-size:24px}",
                "p{margin:0;color:#6e4e28}",
                "small{display:block;margin-top:18px;color:#9a6b3c}",
            )
        )
        return (
            "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)}</title><style>{style}</style>"
            f'<main><div class="mark">{mark}</div>'
            f"<h1>{html.escape(title)}</h1><p>{html.escape(outcome.message)}</p>"
            f"<small>{html.escape(action)}</small></main></html>"
        )
