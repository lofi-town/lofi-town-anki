from __future__ import annotations

from pathlib import Path

from addon.configuration import DEFAULT_CONFIG
from addon.web_assets import (
    build_bootstrap,
    build_dynamic_bootstrap,
    build_session_bootstrap,
)

ROOT = Path(__file__).resolve().parents[1]


def test_bootstrap_scopes_the_view_and_both_color_modes() -> None:
    script = build_bootstrap(DEFAULT_CONFIG, "deck-browser")
    assert '"view":"deck-browser"' in script
    assert '"colorMode":"light"' in script
    assert '"bg":"#F6E6C4"' in script
    assert '"accent":"#F2762E"' in script
    assert "--lofi-${mode}-${name.replaceAll" in script
    assert 'root.classList.add("lofi-town-theme")' in script
    assert "root.dataset.lofiLowResource" in script
    assert "root.dataset.lofiRatingShortcuts" in script


def test_dynamic_bootstrap_is_limited_to_finished_deck_page() -> None:
    script = build_dynamic_bootstrap(
        DEFAULT_CONFIG,
        "congrats",
        "/_addons/lofi_town_anki/web/cozy.css",
    )
    assert '!== "/congrats"' in script
    assert '"view":"congrats"' in script
    assert "/_addons/lofi_town_anki/web/cozy.css" in script
    assert script.count("const root = document.documentElement;") == 2
    assert 'attributeFilter: ["class"]' in script
    assert 'document.querySelector(".congrats")' in script
    assert "preserveCompletion.observe(document.documentElement" in script
    assert 'pycmd("lofi-town:open")' in script


def test_session_strip_uses_live_anki_counts_and_namespaced_actions() -> None:
    session = {
        "startedAt": 1_000,
        "focusStartedAt": 1_000,
        "focusPausedAt": 0,
        "focusPausedTotal": 0,
        "answers": 7,
    }
    script = build_session_bootstrap(DEFAULT_CONFIG, session)

    assert '"answers":7' in script
    assert '".new-count", ".learn-count", ".review-count"' in script
    assert '"lofi-town:open"' in script
    assert '"lofi-town:pause-focus"' in script
    assert "collection" not in script.lower()


def test_card_descendants_and_ankihub_controls_are_protected() -> None:
    css = (ROOT / "addon" / "web" / "cozy.css").read_text(encoding="utf-8")
    assert css.count("{") == css.count("}")
    assert "#qa *" not in css
    assert "button:not(#ankihub-view-note-button)" in css
    assert "#ankihub-view-note-button" in css
    assert "card_will_show" not in css
    assert "#lofi-session-hud" in css
    assert '[data-lofi-low-resource="on"]' in css


def test_top_toolbar_overrides_ankis_dark_fancy_layer() -> None:
    css = (ROOT / "addon" / "web" / "cozy.css").read_text(encoding="utf-8")
    assert 'body.fancy:not(.flat) .toolbar' in css
    assert 'body.fancy:not(.flat)\n    :is(#decks' in css


def test_uses_lofi_towns_variable_font_without_fallback_soup() -> None:
    css = (ROOT / "addon" / "web" / "cozy.css").read_text(encoding="utf-8")
    assert 'font-family: "Bricolage Grotesque Variable"' in css
    assert "BricolageGrotesqueVariable.woff2" in css
    assert "font-weight: 200 800" in css
    assert "Avenir Next" not in css
    assert "Trebuchet" not in css
    assert "font-weight: 850" not in css
    assert "font-weight: 900" not in css
