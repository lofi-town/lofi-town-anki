from __future__ import annotations

from typing import Any

_CONTEXT_VIEWS = {
    ("aqt.deckbrowser", "DeckBrowser"): "deck-browser",
    ("aqt.deckbrowser", "DeckBrowserBottomBar"): "bottom-toolbar",
    ("aqt.overview", "Overview"): "overview",
    ("aqt.overview", "OverviewBottomBar"): "overview-controls",
    ("aqt.reviewer", "Reviewer"): "reviewer",
    ("aqt.reviewer", "ReviewerBottomBar"): "review-controls",
    ("aqt.toolbar", "TopToolbar"): "top-toolbar",
    ("aqt.toolbar", "BottomToolbar"): "bottom-toolbar",
}

_REVIEW_CONTROL_COMMANDS = {
    "lofi-town:open",
    "lofi-town:pause-focus",
    "lofi-town:resume-focus",
    "lofi-town:restart-focus",
    "lofi-town:start-break",
    "lofi-town:restart-target",
    "lofi-town:take-break",
}


def classify_context(context: Any) -> str | None:
    if context is None or is_ankihub_context(context):
        return None
    context_type = type(context)
    return _CONTEXT_VIEWS.get((context_type.__module__, context_type.__name__))


def is_ankihub_context(context: Any) -> bool:
    for context_type in type(context).__mro__:
        module = getattr(context_type, "__module__", "").lower()
        name = getattr(context_type, "__name__", "").lower()
        if "ankihub" in module or name.startswith("ankihub"):
            return True
    return False


def is_trusted_lofi_command(
    message: str,
    context: Any,
    *,
    completion_view: bool = False,
) -> bool:
    view = classify_context(context)
    if view == "review-controls":
        return message in _REVIEW_CONTROL_COMMANDS
    return view == "overview" and completion_view and message == "lofi-town:open"
