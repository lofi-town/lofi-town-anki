from __future__ import annotations

import re
from typing import Any

from .configuration import normalize_config, theme_tokens

_START = "/* lofi-town-theme:start */"
_END = "/* lofi-town-theme:end */"
_BLOCK = re.compile(re.escape(_START) + r".*?" + re.escape(_END), re.DOTALL)


def apply_native_style(
    main_window: Any, config: dict[str, Any], dark_mode: bool
) -> None:
    normalized = normalize_config(config)
    current = _BLOCK.sub("", main_window.styleSheet()).rstrip()
    enabled = normalized["enabled"] and normalized["native_window"]
    main_window.setProperty("lofiTownTheme", enabled)
    if not enabled:
        main_window.setStyleSheet(current)
        return

    mode = _effective_mode(normalized["color_mode"], dark_mode)
    tokens = theme_tokens(normalized, mode)
    block = f"""
{_START}
QMainWindow[lofiTownTheme="true"] {{
    background-color: {tokens["bg"]};
}}
QMainWindow[lofiTownTheme="true"] QStatusBar {{
    background-color: {tokens["surface"]};
    color: {tokens["text_soft"]};
    border-top: 1px solid {tokens["border"]};
}}
{_END}
""".strip()
    main_window.setStyleSheet(f"{current}\n{block}".strip())


def _effective_mode(configured: str, dark_mode: bool) -> str:
    if configured == "dark":
        return "dark"
    if configured == "light":
        return "light"
    return "dark" if dark_mode else "light"
