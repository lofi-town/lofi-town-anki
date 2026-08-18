from __future__ import annotations

from pathlib import Path

from addon.configuration import DEFAULT_CONFIG
from addon.web_assets import build_bootstrap, build_dynamic_bootstrap

ROOT = Path(__file__).resolve().parents[1]


def test_bootstrap_scopes_the_view_and_both_color_modes() -> None:
    script = build_bootstrap(DEFAULT_CONFIG, "deck-browser")
    assert '"view":"deck-browser"' in script
    assert '"colorMode":"light"' in script
    assert '"bg":"#F6E6C4"' in script
    assert '"accent":"#F2762E"' in script
    assert "--lofi-${mode}-${name.replaceAll" in script
    assert 'root.classList.add("lofi-town-theme")' in script


def test_dynamic_bootstrap_is_limited_to_finished_deck_page() -> None:
    script = build_dynamic_bootstrap(
        DEFAULT_CONFIG,
        "congrats",
        "/_addons/lofi_town_anki/web/cozy.css",
    )
    assert '!== "/congrats"' in script
    assert '"view":"congrats"' in script
    assert "/_addons/lofi_town_anki/web/cozy.css" in script


def test_card_descendants_and_ankihub_controls_are_protected() -> None:
    css = (ROOT / "addon" / "web" / "cozy.css").read_text(encoding="utf-8")
    assert "#qa *" not in css
    assert "button:not(#ankihub-view-note-button)" in css
    assert "#ankihub-view-note-button" in css
    assert "card_will_show" not in css


def test_top_toolbar_overrides_ankis_dark_fancy_layer() -> None:
    css = (ROOT / "addon" / "web" / "cozy.css").read_text(encoding="utf-8")
    assert 'body.fancy:not(.flat) .toolbar' in css
    assert 'body.fancy:not(.flat)\n    :is(#decks' in css
