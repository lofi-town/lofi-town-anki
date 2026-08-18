from __future__ import annotations

try:
    from aqt import mw
except ImportError:
    mw = None  # type: ignore[assignment]

if mw is not None:
    from .plugin import initialize

    initialize()
