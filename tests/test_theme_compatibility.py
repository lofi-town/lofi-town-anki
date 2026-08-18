from __future__ import annotations

from addon.compatibility import classify_context, is_ankihub_context


def context(module: str, name: str, base: type = object) -> object:
    return type(name, (base,), {"__module__": module})()


def test_known_anki_contexts_are_classified() -> None:
    expected = {
        ("aqt.deckbrowser", "DeckBrowser"): "deck-browser",
        ("aqt.deckbrowser", "DeckBrowserBottomBar"): "bottom-toolbar",
        ("aqt.overview", "Overview"): "overview",
        ("aqt.overview", "OverviewBottomBar"): "overview-controls",
        ("aqt.reviewer", "Reviewer"): "reviewer",
        ("aqt.reviewer", "ReviewerBottomBar"): "review-controls",
        ("aqt.toolbar", "TopToolbar"): "top-toolbar",
        ("aqt.toolbar", "BottomToolbar"): "bottom-toolbar",
    }
    for (module, name), view in expected.items():
        assert classify_context(context(module, name)) == view


def test_unknown_and_none_contexts_are_skipped() -> None:
    assert classify_context(None) is None
    assert classify_context(context("some_addon.dialog", "Dialog")) is None


def test_ankihub_contexts_and_subclasses_are_skipped() -> None:
    base = type("AnkiHubWebView", (), {"__module__": "ankihub.gui.webview"})
    child = context("third_party.wrapper", "WrappedView", base)
    assert is_ankihub_context(child)
    assert classify_context(child) is None
