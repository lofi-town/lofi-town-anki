from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aqt import mw
else:
    try:
        from aqt import mw
    except ImportError:
        mw = None

if mw is not None:
    from .plugin import initialize

    initialize()
