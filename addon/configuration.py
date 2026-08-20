from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "config_version": 5,
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
    "session_hud": True,
    "sync_focus_with_lofi_town": False,
    "focus_minutes": 25,
    "break_minutes": 5,
    "session_target_answers": 0,
    "hud_show_answers": True,
    "hud_show_remaining": True,
    "hud_show_timer": True,
    "hud_show_progress": True,
    "hud_show_sync_status": True,
    "hud_compact": False,
    "hud_position": "top",
    "review_focus_mode": False,
    "show_rating_shortcuts": True,
    "lofi_town_breaks": True,
    "low_resource": False,
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

_ENUM_FIELDS = {
    "palette": frozenset(PALETTES),
    "color_mode": frozenset({"follow_anki", "light", "dark"}),
    "density": frozenset({"cozy", "compact"}),
    "motion": frozenset({"system", "full", "reduced"}),
    "hud_position": frozenset({"top", "bottom"}),
}
_INTEGER_BOUNDS = {
    "corner_radius": (8, 24),
    "focus_minutes": (0, 180),
    "break_minutes": (0, 60),
    "session_target_answers": (0, 5_000),
}
_BOOLEAN_FIELDS = (
    "enabled",
    "custom_accent_enabled",
    "texture",
    "review_backdrop",
    "native_window",
    "session_hud",
    "sync_focus_with_lofi_town",
    "hud_show_answers",
    "hud_show_remaining",
    "hud_show_timer",
    "hud_show_progress",
    "hud_show_sync_status",
    "hud_compact",
    "review_focus_mode",
    "show_rating_shortcuts",
    "lofi_town_breaks",
    "low_resource",
)


def normalize_config(raw: Any) -> dict[str, Any]:
    config = deepcopy(DEFAULT_CONFIG)
    if not isinstance(raw, dict):
        return config
    raw = _migrate_config(raw)

    for key, accepted in _ENUM_FIELDS.items():
        value = raw.get(key)
        if isinstance(value, str) and value in accepted:
            config[key] = value
    if is_hex_color(raw.get("custom_accent")):
        config["custom_accent"] = raw["custom_accent"].upper()
    config["font_scale"] = _bounded_number(
        raw.get("font_scale"),
        0.9,
        1.2,
        DEFAULT_CONFIG["font_scale"],
    )
    for key, (minimum, maximum) in _INTEGER_BOUNDS.items():
        config[key] = round(
            _bounded_number(
                raw.get(key),
                minimum,
                maximum,
                DEFAULT_CONFIG[key],
            )
        )
    for key in _BOOLEAN_FIELDS:
        if isinstance(raw.get(key), bool):
            config[key] = raw[key]
    return config


def _migrate_config(raw: dict[str, Any]) -> dict[str, Any]:
    migrated = dict(raw)
    version = raw.get("config_version")
    if isinstance(version, int) and not isinstance(version, bool) and version >= 3:
        return migrated

    legacy_palette = raw.get("palette")
    if isinstance(legacy_palette, str) and legacy_palette in _LEGACY_PALETTES:
        migrated["palette"] = _LEGACY_PALETTES[legacy_palette]

    uses_legacy_default = (
        (legacy_palette is None or legacy_palette == "sunroom")
        and raw.get("color_mode") in (None, "follow_anki")
        and raw.get("custom_accent_enabled") in (None, False)
        and raw.get("custom_accent") in (None, "#E66B2E")
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
        accent_ink=_readable_accent(accent, tokens["surface"]),
        accent_text=contrast_text(accent),
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


def contrast_text(background: str) -> str:
    options = ("#24170D", "#FFFAF0")
    return max(options, key=lambda color: _contrast_ratio(background, color))


def _readable_accent(accent: str, background: str) -> str:
    target = contrast_text(background)
    for step in range(21):
        candidate = mix_colors(accent, target, step / 20)
        if _contrast_ratio(candidate, background) >= 4.5:
            return candidate
    return target


def _contrast_ratio(first: str, second: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(first), _relative_luminance(second)),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


def _relative_luminance(color: str) -> float:
    channels = []
    for channel in _hex_to_rgb(color):
        normalized = channel / 255
        channels.append(
            normalized / 12.92
            if normalized <= 0.04045
            else ((normalized + 0.055) / 1.055) ** 2.4
        )
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]


def _bounded_number(
    value: Any, minimum: float, maximum: float, fallback: float
) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return fallback
    return max(minimum, min(maximum, float(value)))
