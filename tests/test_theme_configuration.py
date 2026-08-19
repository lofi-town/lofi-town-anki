from __future__ import annotations

from addon.configuration import (
    DEFAULT_CONFIG,
    contrast_text,
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
            "focus_minutes": 30,
        }
    )

    assert config["enabled"] == DEFAULT_CONFIG["enabled"]
    assert config["palette"] == DEFAULT_CONFIG["palette"]
    assert config["font_scale"] == 1.2
    assert config["corner_radius"] == 8
    assert config["custom_accent"] == DEFAULT_CONFIG["custom_accent"]
    assert config["focus_minutes"] == DEFAULT_CONFIG["focus_minutes"]


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
    assert config["corner_radius"] == 14


def test_legacy_default_migrates_to_game_palette_in_light_mode() -> None:
    config = normalize_config(
        {
            "config_version": 1,
            "palette": "sunroom",
            "color_mode": "follow_anki",
            "custom_accent_enabled": False,
            "custom_accent": "#E66B2E",
            "corner_radius": 16,
            "texture": True,
        }
    )

    assert config["config_version"] == 4
    assert config["palette"] == "tangerine"
    assert config["color_mode"] == "light"
    assert config["custom_accent"] == "#F2762E"
    assert config["corner_radius"] == 14
    assert config["texture"] is False


def test_game_accents_share_the_warm_neutral_base() -> None:
    tangerine = theme_tokens({"config_version": 2, "palette": "tangerine"}, "light")
    grape = theme_tokens({"config_version": 2, "palette": "grape"}, "light")

    assert tangerine["bg"] == grape["bg"] == "#F6E6C4"
    assert tangerine["surface"] == grape["surface"] == "#FFF7E6"
    assert tangerine["text"] == grape["text"] == "#4A2E12"
    assert tangerine["accent"] == "#F2762E"
    assert tangerine["accent_drop"] == "#C4551A"


def test_color_helpers_validate_and_mix() -> None:
    assert is_hex_color("#A1b2C3")
    assert not is_hex_color("#FFF")
    assert not is_hex_color("rgb(1, 2, 3)")
    assert mix_colors("#123456", "#ABCDEF", 0) == "#123456"
    assert mix_colors("#123456", "#ABCDEF", 1) == "#ABCDEF"
    assert contrast_text("#F4B72A") == "#24170D"


def test_study_flow_settings_are_normalized() -> None:
    config = normalize_config(
        {
            "session_hud": False,
            "sync_focus_with_lofi_town": True,
            "focus_minutes": 50,
            "review_focus_mode": True,
            "show_rating_shortcuts": False,
            "lofi_town_breaks": False,
            "low_resource": True,
        }
    )

    assert config["session_hud"] is False
    assert config["sync_focus_with_lofi_town"] is True
    assert config["focus_minutes"] == 50
    assert config["review_focus_mode"] is True
    assert config["show_rating_shortcuts"] is False
    assert config["lofi_town_breaks"] is False
    assert config["low_resource"] is True


def test_v3_config_migrates_focus_sync_to_opt_in() -> None:
    config = normalize_config({"config_version": 3, "session_hud": True})

    assert config["config_version"] == 4
    assert config["sync_focus_with_lofi_town"] is False
