from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from aqt.qt import QFontDatabase


@lru_cache(maxsize=1)
def load_cozy_font_family() -> str | None:
    path = (
        Path(__file__).resolve().parent
        / "resources/fonts/BricolageGrotesque.ttf"
    )
    font_id = QFontDatabase.addApplicationFont(str(path))
    families = QFontDatabase.applicationFontFamilies(font_id)
    return families[0] if families else None
