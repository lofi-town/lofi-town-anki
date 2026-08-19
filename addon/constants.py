from __future__ import annotations

import os
from urllib.parse import urlsplit

_PRODUCTION_APP_URL = "https://app.lofi.town/?ref=anki"
_PRODUCTION_APP_ORIGIN = "https://app.lofi.town"
_INVALID_DEV_URL = "LOFI_TOWN_ANKI_DEV_URL must be a plain HTTP loopback origin."


def _app_endpoints(dev_url: str | None) -> tuple[str, str]:
    if not dev_url:
        return _PRODUCTION_APP_URL, _PRODUCTION_APP_ORIGIN

    try:
        parsed = urlsplit(dev_url)
        _ = parsed.port
    except ValueError as exc:
        raise ValueError(_INVALID_DEV_URL) from exc

    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(_INVALID_DEV_URL)

    origin = f"{parsed.scheme}://{parsed.netloc}"
    return f"{origin}/?ref=anki", origin


APP_URL, APP_ORIGIN = _app_endpoints(os.environ.get("LOFI_TOWN_ANKI_DEV_URL"))
ADDON_NAME = "Lofi Town"
DOCK_OBJECT_NAME = "lofi-town-anki-dock"
BRIDGE_API_VERSION = 2
OAUTH_TIMEOUT_SECONDS = 5 * 60
