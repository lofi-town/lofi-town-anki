from __future__ import annotations

from pathlib import Path

from addon.configuration import DEFAULT_CONFIG
from addon.session import SessionSummaryPayload
from addon.web_assets import (
    build_bootstrap,
    build_dynamic_bootstrap,
    build_recap_bootstrap,
    build_session_bootstrap,
)

ROOT = Path(__file__).resolve().parents[1]
SESSION_JS = (ROOT / "addon" / "web" / "review_session.js").read_text(
    encoding="utf-8"
)
RECAP_JS = (ROOT / "addon" / "web" / "session_recap.js").read_text(
    encoding="utf-8"
)


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
        ("/_addons/lofi_town_anki/web/cozy.css",),
        "/_addons/lofi_town_anki/web/session_recap.js",
    )
    assert '!== "/congrats"' in script
    assert '"view":"congrats"' in script
    assert "/_addons/lofi_town_anki/web/cozy.css" in script
    assert script.count("const root = document.documentElement;") == 2
    assert 'attributeFilter: ["class"]' in script
    assert "session_recap.js" in script
    assert "window.__lofiTownRecapBootstrap" in script
    assert 'document.querySelector(".congrats")' in RECAP_JS
    assert "preserve.observe(document.documentElement" in RECAP_JS
    assert 'send("lofi-town:open")' in RECAP_JS


def test_recap_uses_only_aggregate_session_values() -> None:
    summary: SessionSummaryPayload = {
        "answers": 60,
        "focusedMs": 1_500_000,
        "blocksCompleted": 1,
        "targetAnswers": 60,
        "targetProgress": 60,
        "targetsCompleted": 1,
    }
    script = build_recap_bootstrap(DEFAULT_CONFIG, summary)

    assert '"answers":60' in script
    assert '"focusedMs":1500000' in script
    assert '"showDismissButton":true' in script
    assert "reached your ${summary.targetAnswers}-answer target" in RECAP_JS
    assert 'dismiss.id = "lofi-town-recap-dismiss"' in RECAP_JS
    for forbidden in ("cardId", "cardContent", "deckId", "deckName", "rating"):
        assert forbidden not in script


def test_finished_deck_includes_session_recap_when_available() -> None:
    summary: SessionSummaryPayload = {
        "answers": 12,
        "focusedMs": 59_000,
        "blocksCompleted": 0,
        "targetAnswers": 20,
        "targetProgress": 12,
        "targetsCompleted": 0,
    }
    script = build_dynamic_bootstrap(
        DEFAULT_CONFIG,
        "congrats",
        ("/_addons/lofi_town_anki/web/cozy.css",),
        "/_addons/lofi_town_anki/web/session_recap.js",
        summary,
    )

    assert '"answers":12' in script
    assert '"focusedMs":59000' in script
    assert "under 1 min" in RECAP_JS
    assert "You completed ${completed} of your" in RECAP_JS


def test_session_strip_uses_live_anki_counts_and_namespaced_actions() -> None:
    session: dict[str, object] = {
        "phase": "focusing",
        "startedAt": 1_000,
        "focusStartedAt": 1_000,
        "focusPausedAt": 0,
        "focusPausedTotal": 0,
        "completedFocusMs": 0,
        "breakStartedAt": 0,
        "answers": 7,
        "targetStartedAnswers": 0,
    }
    script = build_session_bootstrap(DEFAULT_CONFIG, session)

    assert '"answers":7' in script
    assert '".new-count", ".learn-count", ".review-count"' in SESSION_JS
    assert '"lofi-town:take-break"' in SESSION_JS
    assert '"lofi-town:pause-focus"' in SESSION_JS
    assert '"lofi-town:start-break"' in SESSION_JS
    assert '"lofi-town:restart-target"' in SESSION_JS
    assert 'timerText: "Ready"' in SESSION_JS
    assert "state.syncStatus" in SESSION_JS
    assert '"breakMinutes":5' in script
    assert '"showProgress":true' in script
    assert 'role="progressbar"' in SESSION_JS
    assert "collection" not in (script + SESSION_JS).lower()


def test_session_strip_supports_custom_targets_and_hidden_facts() -> None:
    config = {
        **DEFAULT_CONFIG,
        "focus_minutes": 37,
        "break_minutes": 8,
        "session_target_answers": 60,
        "hud_show_answers": False,
        "hud_show_remaining": False,
        "hud_show_timer": False,
        "hud_show_progress": True,
        "hud_compact": True,
        "hud_position": "bottom",
    }
    script = build_session_bootstrap(config, {"answers": 12})

    assert '"focusMinutes":37' in script
    assert '"breakMinutes":8' in script
    assert '"targetAnswers":60' in script
    assert '"showAnswers":false' in script
    assert '"showRemaining":false' in script
    assert '"showTimer":false' in script
    assert "time.hidden = !state.showTimer" in SESSION_JS
    assert '"compact":true' in script
    assert '"position":"bottom"' in script
    assert 'outer.insertAdjacentElement("afterend", hud)' in SESSION_JS


def test_card_descendants_and_ankihub_controls_are_protected() -> None:
    css = (ROOT / "addon" / "web" / "cozy.css").read_text(encoding="utf-8")
    review_css = (ROOT / "addon" / "web" / "review_session.css").read_text(
        encoding="utf-8"
    )
    recap_css = (ROOT / "addon" / "web" / "session_recap.css").read_text(
        encoding="utf-8"
    )
    for stylesheet in (css, review_css, recap_css):
        assert stylesheet.count("{") == stylesheet.count("}")
    assert "#qa *" not in css
    assert "button:not(#ankihub-view-note-button)" in css
    assert "#ankihub-view-note-button" in css
    assert "card_will_show" not in css
    assert "#lofi-session-hud" in review_css
    assert ".lofi-session-progress" in review_css
    assert "#lofi-town-recap" in recap_css
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
