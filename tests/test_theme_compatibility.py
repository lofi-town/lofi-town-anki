from __future__ import annotations

from addon.compatibility import (
    classify_context,
    is_ankihub_context,
    is_trusted_lofi_command,
)


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


def test_review_controls_are_the_only_source_for_session_commands() -> None:
    controls = context("aqt.reviewer", "ReviewerBottomBar")
    reviewer = context("aqt.reviewer", "Reviewer")
    commands = {
        "lofi-town:open",
        "lofi-town:pause-focus",
        "lofi-town:resume-focus",
        "lofi-town:restart-focus",
    }

    for command in commands:
        assert is_trusted_lofi_command(command, controls)
        assert not is_trusted_lofi_command(command, reviewer)


def test_completion_screen_only_accepts_open_command() -> None:
    overview = context("aqt.overview", "Overview")

    assert is_trusted_lofi_command(
        "lofi-town:open",
        overview,
        completion_view=True,
    )
    assert not is_trusted_lofi_command("lofi-town:open", overview)
    assert not is_trusted_lofi_command(
        "lofi-town:pause-focus",
        overview,
        completion_view=True,
    )


def test_unknown_commands_and_contexts_are_rejected() -> None:
    controls = context("aqt.reviewer", "ReviewerBottomBar")
    unknown = context("some_addon.dialog", "Dialog")

    assert not is_trusted_lofi_command("lofi-town:unknown", controls)
    assert not is_trusted_lofi_command("lofi-town:open", unknown)
