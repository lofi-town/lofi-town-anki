from __future__ import annotations

import ipaddress
from urllib.parse import SplitResult, urlsplit

_PRIVATE_HOST_SUFFIXES = (
    ".localhost",
    ".local",
    ".lan",
    ".home",
    ".internal",
    ".test",
    ".invalid",
    ".example",
    ".onion",
)
_SUPABASE_HOST_SUFFIXES = (".supabase.co", ".supabase.in")


def _parse_url(value: str) -> SplitResult | None:
    try:
        parsed = urlsplit(value)
        _ = parsed.port
        return parsed
    except (TypeError, ValueError):
        return None


def _has_credentials(parsed: SplitResult) -> bool:
    return parsed.username is not None or parsed.password is not None


def _is_private_hostname(hostname: str) -> bool:
    normalized = hostname.lower().rstrip(".")
    if normalized == "localhost" or normalized.endswith(_PRIVATE_HOST_SUFFIXES):
        return True
    if "." not in normalized and ":" not in normalized:
        return True

    try:
        return not ipaddress.ip_address(normalized).is_global
    except ValueError:
        return False


def is_safe_external_url(value: str) -> bool:
    parsed = _parse_url(value)
    if not parsed or parsed.scheme.lower() != "https" or not parsed.hostname:
        return False
    return not _has_credentials(parsed) and not _is_private_hostname(parsed.hostname)


def is_safe_oauth_authorization_url(value: str) -> bool:
    if not is_safe_external_url(value):
        return False

    parsed = urlsplit(value)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    return (
        hostname.endswith(_SUPABASE_HOST_SUFFIXES)
        and parsed.path == "/auth/v1/authorize"
    )


def is_allowed_app_url(value: str, allowed_origin: str) -> bool:
    parsed = _parse_url(value)
    origin = _parse_url(allowed_origin)
    if not parsed or not origin or not parsed.hostname or not origin.hostname:
        return False
    if _has_credentials(parsed):
        return False

    parsed_port = parsed.port or (443 if parsed.scheme == "https" else 80)
    origin_port = origin.port or (443 if origin.scheme == "https" else 80)
    return (
        parsed.scheme.lower() == origin.scheme.lower()
        and parsed.hostname.lower().rstrip(".")
        == origin.hostname.lower().rstrip(".")
        and parsed_port == origin_port
    )
