from __future__ import annotations

from addon.configuration import (
    DEFAULT_CONFIG,
    is_hex_color,
    mix_colors,
    normalize_config,
    theme_tokens,
)


def test_invalid_values_fall_back_and_numbers_are_bounded() -> None:
    config = normalize_config(
        {
            "enabled": "yes",
            "palette": "unknown",
            "font_scale": 4,
            "corner_radius": -3,
            "custom_accent": "red",
        }
    )

    assert config["enabled"] == DEFAULT_CONFIG["enabled"]
    assert config["palette"] == DEFAULT_CONFIG["palette"]
    assert config["font_scale"] == 1.2
    assert config["corner_radius"] == 8
    assert config["custom_accent"] == DEFAULT_CONFIG["custom_accent"]


def test_valid_custom_accent_is_normalized_and_used() -> None:
    config = normalize_config(
        {
            "custom_accent_enabled": True,
            "custom_accent": "#12abef",
        }
    )

    assert config["custom_accent"] == "#12ABEF"
    assert theme_tokens(config, "light")["accent"] == "#12ABEF"


def test_booleans_are_not_treated_as_numbers() -> None:
    config = normalize_config({"font_scale": True, "corner_radius": False})
    assert config["font_scale"] == 1.0
    assert config["corner_radius"] == 16


def test_color_helpers_validate_and_mix() -> None:
    assert is_hex_color("#A1b2C3")
    assert not is_hex_color("#FFF")
    assert not is_hex_color("rgb(1, 2, 3)")
    assert mix_colors("#123456", "#ABCDEF", 0) == "#123456"
    assert mix_colors("#123456", "#ABCDEF", 1) == "#ABCDEF"
