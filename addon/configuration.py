from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "config_version": 2,
    "enabled": True,
    "palette": "tangerine",
    "color_mode": "light",
    "custom_accent_enabled": False,
    "custom_accent": "#F2762E",
    "density": "cozy",
    "font_scale": 1.0,
    "corner_radius": 14,
    "motion": "system",
    "texture": False,
    "review_backdrop": False,
    "native_window": True,
}

_LIGHT_BASE = {
    "bg": "#F6E6C4",
    "surface": "#FFF7E6",
    "card": "#FFFDF5",
    "border": "#F0E2C4",
    "secondary": "#FFE7BF",
    "raised": "#FBEFD3",
    "hover": "#FFF3DC",
    "text": "#4A2E12",
    "text_soft": "#6E4E28",
    "text_muted": "#9A6B3C",
}

_DARK_BASE = {
    "bg": "#2A1E18",
    "surface": "#36271F",
    "card": "#3F2E24",
    "border": "#604936",
    "secondary": "#4B372A",
    "raised": "#453226",
    "hover": "#513B2C",
    "text": "#FFF2D8",
    "text_soft": "#E6C9A6",
    "text_muted": "#BE9973",
}

PALETTES: dict[str, dict[str, Any]] = {
    "tangerine": {
        "label": "Tangerine",
        "accent": "#F2762E",
        "accent_drop": "#C4551A",
        "light": _LIGHT_BASE,
        "dark": _DARK_BASE,
    },
    "honey": {
        "label": "Honey",
        "accent": "#F4B72A",
        "accent_drop": "#C9900F",
        "light": _LIGHT_BASE,
        "dark": _DARK_BASE,
    },
    "leaf": {
        "label": "Leaf",
        "accent": "#5BA84F",
        "accent_drop": "#3F8236",
        "light": _LIGHT_BASE,
        "dark": _DARK_BASE,
    },
    "grape": {
        "label": "Grape",
        "accent": "#8A63C4",
        "accent_drop": "#6A45A2",
        "light": _LIGHT_BASE,
        "dark": _DARK_BASE,
    },
}

_LEGACY_PALETTES = {
    "sunroom": "tangerine",
    "matcha": "leaf",
    "rainy": "grape",
    "plum": "grape",
}

_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def normalize_config(raw: Any) -> dict[str, Any]:
    config = deepcopy(DEFAULT_CONFIG)
    if not isinstance(raw, dict):
        return config
    raw = _migrate_config(raw)

    if isinstance(raw.get("enabled"), bool):
        config["enabled"] = raw["enabled"]
    if raw.get("palette") in PALETTES:
        config["palette"] = raw["palette"]
    if raw.get("color_mode") in {"follow_anki", "light", "dark"}:
        config["color_mode"] = raw["color_mode"]
    if isinstance(raw.get("custom_accent_enabled"), bool):
        config["custom_accent_enabled"] = raw["custom_accent_enabled"]
    if is_hex_color(raw.get("custom_accent")):
        config["custom_accent"] = raw["custom_accent"].upper()
    if raw.get("density") in {"cozy", "compact"}:
        config["density"] = raw["density"]
    config["font_scale"] = _bounded_number(raw.get("font_scale"), 0.9, 1.2, 1.0)
    config["corner_radius"] = round(
        _bounded_number(raw.get("corner_radius"), 8, 24, 14)
    )
    if raw.get("motion") in {"system", "full", "reduced"}:
        config["motion"] = raw["motion"]
    for key in ("texture", "review_backdrop", "native_window"):
        if isinstance(raw.get(key), bool):
            config[key] = raw[key]
    return config


def _migrate_config(raw: dict[str, Any]) -> dict[str, Any]:
    migrated = dict(raw)
    version = raw.get("config_version")
    if isinstance(version, int) and not isinstance(version, bool) and version >= 2:
        return migrated

    legacy_palette = raw.get("palette")
    if legacy_palette in _LEGACY_PALETTES:
        migrated["palette"] = _LEGACY_PALETTES[legacy_palette]

    uses_legacy_default = (
        legacy_palette in {None, "sunroom"}
        and raw.get("color_mode") in {None, "follow_anki"}
        and raw.get("custom_accent_enabled") in {None, False}
        and raw.get("custom_accent") in {None, "#E66B2E"}
    )
    if uses_legacy_default:
        migrated["color_mode"] = "light"
        migrated["custom_accent"] = DEFAULT_CONFIG["custom_accent"]
        migrated["corner_radius"] = DEFAULT_CONFIG["corner_radius"]
        migrated["texture"] = DEFAULT_CONFIG["texture"]
    return migrated


def is_hex_color(value: Any) -> bool:
    return isinstance(value, str) and bool(_HEX_COLOR.fullmatch(value))


def theme_tokens(config: dict[str, Any], mode: str) -> dict[str, str]:
    normalized = normalize_config(config)
    palette = PALETTES[normalized["palette"]]
    tokens = dict(palette[mode])
    accent = (
        normalized["custom_accent"]
        if normalized["custom_accent_enabled"]
        else palette["accent"]
    )
    tokens.update(
        accent=accent,
        accent_drop=(
            mix_colors(accent, "#000000", 0.28 if mode == "light" else 0.34)
            if normalized["custom_accent_enabled"]
            else palette["accent_drop"]
        ),
        accent_soft=mix_colors(accent, tokens["card"], 0.78),
        focus=mix_colors(accent, "#FFFFFF", 0.58),
        shadow="#2B1A0A" if mode == "light" else "#080607",
        positive="#5BA84F",
        warning="#D99A18",
        negative="#D95872",
        info="#2F91AE",
    )
    return tokens


def mix_colors(foreground: str, background: str, background_ratio: float) -> str:
    fg = _hex_to_rgb(foreground)
    bg = _hex_to_rgb(background)
    ratio = max(0.0, min(1.0, background_ratio))
    mixed = tuple(
        round(a * (1 - ratio) + b * ratio) for a, b in zip(fg, bg, strict=False)
    )
    return "#" + "".join(f"{channel:02X}" for channel in mixed)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]


def _bounded_number(
    value: Any, minimum: float, maximum: float, fallback: float
) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return fallback
    return max(minimum, min(maximum, float(value)))
