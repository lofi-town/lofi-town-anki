from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "config_version": 1,
    "enabled": True,
    "palette": "sunroom",
    "color_mode": "follow_anki",
    "custom_accent_enabled": False,
    "custom_accent": "#E66B2E",
    "density": "cozy",
    "font_scale": 1.0,
    "corner_radius": 16,
    "motion": "system",
    "texture": True,
    "review_backdrop": False,
    "native_window": True,
}

PALETTES: dict[str, dict[str, Any]] = {
    "sunroom": {
        "label": "Sunroom",
        "accent": "#E66B2E",
        "light": {
            "bg": "#F6E6C4",
            "surface": "#FFF7E6",
            "card": "#FFFDF5",
            "border": "#E7CFA0",
            "secondary": "#FFE7BF",
            "text": "#4A2E12",
            "text_soft": "#6E4E28",
            "text_muted": "#9A6B3C",
        },
        "dark": {
            "bg": "#241B17",
            "surface": "#30241D",
            "card": "#3A2B22",
            "border": "#5C4433",
            "secondary": "#4A3528",
            "text": "#FFF2D8",
            "text_soft": "#E6C9A6",
            "text_muted": "#BE9973",
        },
    },
    "matcha": {
        "label": "Matcha",
        "accent": "#5B9D55",
        "light": {
            "bg": "#E8E7CE",
            "surface": "#F8F5E5",
            "card": "#FFFDF3",
            "border": "#CCD2A9",
            "secondary": "#DEE8C8",
            "text": "#30432D",
            "text_soft": "#52624A",
            "text_muted": "#78836A",
        },
        "dark": {
            "bg": "#19231B",
            "surface": "#243027",
            "card": "#2D392F",
            "border": "#465C48",
            "secondary": "#354637",
            "text": "#EDF5DE",
            "text_soft": "#C5D6B9",
            "text_muted": "#97AE91",
        },
    },
    "rainy": {
        "label": "Rainy Day",
        "accent": "#2F91AE",
        "light": {
            "bg": "#DCE9ED",
            "surface": "#EEF5F5",
            "card": "#FAFDFB",
            "border": "#B8D0D5",
            "secondary": "#D3E8E9",
            "text": "#29444C",
            "text_soft": "#49626A",
            "text_muted": "#71888E",
        },
        "dark": {
            "bg": "#172329",
            "surface": "#213138",
            "card": "#293C43",
            "border": "#405C65",
            "secondary": "#304951",
            "text": "#E9F5F5",
            "text_soft": "#C0D6D9",
            "text_muted": "#8FADB3",
        },
    },
    "plum": {
        "label": "Plum Night",
        "accent": "#8665B5",
        "light": {
            "bg": "#E9E0EC",
            "surface": "#F7F0F3",
            "card": "#FFF9F5",
            "border": "#D5BED9",
            "secondary": "#E8D9EE",
            "text": "#46334F",
            "text_soft": "#66536D",
            "text_muted": "#8B758F",
        },
        "dark": {
            "bg": "#201B29",
            "surface": "#2B2437",
            "card": "#352C42",
            "border": "#554666",
            "secondary": "#413451",
            "text": "#F7EDFF",
            "text_soft": "#D8C4E5",
            "text_muted": "#A991B9",
        },
    },
}

_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def normalize_config(raw: Any) -> dict[str, Any]:
    config = deepcopy(DEFAULT_CONFIG)
    if not isinstance(raw, dict):
        return config

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
        _bounded_number(raw.get("corner_radius"), 8, 24, 16)
    )
    if raw.get("motion") in {"system", "full", "reduced"}:
        config["motion"] = raw["motion"]
    for key in ("texture", "review_backdrop", "native_window"):
        if isinstance(raw.get(key), bool):
            config[key] = raw[key]
    return config


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
        accent_drop=mix_colors(accent, "#000000", 0.25 if mode == "light" else 0.32),
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
