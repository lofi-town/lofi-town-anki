from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import QAction, Qt, QTimer
from aqt.theme import theme_manager
from aqt.webview import AnkiWebView, WebContent

from .compatibility import classify_context, is_trusted_lofi_command
from .configuration import normalize_config
from .constants import ADDON_NAME
from .dock import LofiTownDock
from .native_style import apply_native_style
from .review_session import ReviewSessionConfig, ReviewSessionController
from .settings_dialog import ThemeSettingsDialog
from .state import DockState, normalize_state
from .web_assets import (
    build_bootstrap,
    build_dynamic_bootstrap,
    build_recap_bootstrap,
    build_session_bootstrap,
)


class AddonController:
    def __init__(self) -> None:
        self.dock: LofiTownDock | None = None
        self._review_session = ReviewSessionController()
        self._theme_config = self._read_theme_config()
        self._package = mw.addonManager.addonFromModule(__name__)
        mw.addonManager.setWebExports(
            __name__,
            r"(web/.*\.(css|js)|resources/fonts/.*\.woff2)",
        )
        mw.addonManager.setConfigAction(__name__, self.open_theme_settings)

        self.action = QAction(ADDON_NAME, mw)
        self.action.setCheckable(True)
        self.action.setEnabled(False)
        self.action.setToolTip("Show or hide Lofi Town")
        self.action.triggered.connect(self._toggle_dock)
        mw.form.menuTools.addAction(self.action)

        self.appearance_action = QAction("Lofi Town Settings...", mw)
        self.appearance_action.setObjectName("lofiTownAppearanceAction")
        self.appearance_action.setToolTip("Customize the Lofi Town study room")
        self.appearance_action.triggered.connect(self.open_theme_settings)
        mw.form.menuTools.addAction(self.appearance_action)

    def start(self) -> None:
        gui_hooks.profile_did_open.append(self.on_profile_open)
        gui_hooks.profile_will_close.append(self.on_profile_close)
        gui_hooks.webview_will_set_content.append(self.on_webview_will_set_content)
        gui_hooks.webview_did_inject_style_into_page.append(
            self.on_webview_did_inject_style_into_page
        )
        gui_hooks.webview_did_receive_js_message.append(self.on_js_message)
        gui_hooks.reviewer_did_answer_card.append(self.on_reviewer_did_answer_card)
        gui_hooks.reviewer_will_end.append(self.on_reviewer_will_end)
        gui_hooks.theme_did_change.append(self.apply_native_style)

    def on_profile_open(self) -> None:
        if self.dock is not None:
            return

        self._theme_config = self._read_theme_config()
        state = self._read_state()
        area = (
            Qt.DockWidgetArea.LeftDockWidgetArea
            if state["area"] == "left"
            else Qt.DockWidgetArea.RightDockWidgetArea
        )
        addon_path = Path(__file__).resolve().parent
        dock = LofiTownDock(
            state,
            addon_path,
            self._write_state,
            mw,
            motion=self._theme_config["motion"],
        )
        self.dock = dock
        mw.addDockWidget(area, dock)

        if state["floating"]:
            dock.setFloating(True)
            dock.restore_floating_geometry()
        else:
            QTimer.singleShot(
                0,
                lambda: mw.resizeDocks(
                    [dock], [state["width"]], Qt.Orientation.Horizontal
                ),
            )
        dock.setVisible(state["visible"])
        dock.visibilityChanged.connect(self.action.setChecked)
        self.action.setEnabled(True)
        self.action.setChecked(dock.isVisible())
        self.apply_native_style()

    def on_profile_close(self) -> None:
        self._review_session.close()
        dock = self.dock
        if dock is None:
            return
        self._write_state(dock.capture_state())
        self.dock = None
        self.action.setChecked(False)
        self.action.setEnabled(False)
        dock.dispose()
        mw.removeDockWidget(dock)
        dock.deleteLater()

    def _toggle_dock(self, visible: bool) -> None:
        if self.dock is not None:
            self.dock.setVisible(visible)

    def open_theme_settings(self, *_args: Any) -> None:
        self._theme_config = self._read_theme_config()
        dialog = ThemeSettingsDialog(
            parent=mw,
            config=self._theme_config,
            dark_mode=theme_manager.night_mode,
            ankihub_installed=self._ankihub_installed(),
            save=self._write_theme_config,
        )
        if dialog.exec():
            mw.reset()

    def on_webview_will_set_content(
        self,
        web_content: WebContent,
        context: object | None,
    ) -> None:
        if not self._theme_config["enabled"]:
            return
        view = classify_context(context)
        if view is None:
            return
        if view == "reviewer" and not self._theme_config["review_backdrop"]:
            return
        web_content.css.append(f"/_addons/{self._package}/web/cozy.css")
        web_content.head += build_bootstrap(self._theme_config, view)
        summary = self._review_session.peek_summary()
        if view in {"deck-browser", "overview"} and summary:
            web_content.css.append(
                f"/_addons/{self._package}/web/session_recap.css"
            )
            web_content.head += build_recap_bootstrap(
                self._theme_config,
                summary.to_payload(),
            )
            web_content.js.append(
                f"/_addons/{self._package}/web/session_recap.js"
            )
            self._review_session.take_summary()
        if view == "review-controls" and self._theme_config["session_hud"]:
            web_content.css.append(
                f"/_addons/{self._package}/web/review_session.css"
            )
            web_content.head += build_session_bootstrap(
                self._theme_config,
                self._review_session.payload(),
            )
            web_content.js.append(
                f"/_addons/{self._package}/web/review_session.js"
            )

    def on_webview_did_inject_style_into_page(
        self,
        webview: AnkiWebView,
    ) -> None:
        if not self._theme_config["enabled"] or webview is not mw.web:
            return
        if webview.url().path().rstrip("/") != "/congrats":
            return
        stylesheet = f"/_addons/{self._package}/web/cozy.css"
        recap_stylesheet = (
            f"/_addons/{self._package}/web/session_recap.css"
        )
        recap_script = f"/_addons/{self._package}/web/session_recap.js"
        summary = self._review_session.take_summary()
        webview.eval(
            build_dynamic_bootstrap(
                self._theme_config,
                "congrats",
                (stylesheet, recap_stylesheet),
                recap_script,
                summary.to_payload() if summary else None,
            )
        )

    def on_reviewer_did_answer_card(
        self,
        reviewer: Any,
        _card: Any,
        _ease: int,
    ) -> None:
        if self._review_session.record_answer(self._review_session_config()):
            self._update_session_web(reviewer)

    def on_reviewer_will_end(self, *_args: Any) -> None:
        self._review_session.finish(self._review_session_config())

    def on_js_message(
        self,
        handled: tuple[bool, Any],
        message: str,
        context: Any,
    ) -> tuple[bool, Any]:
        if handled[0] or not message.startswith("lofi-town:"):
            return handled
        completion_view = (
            getattr(context, "web", None) is mw.web
            and mw.web.url().path().rstrip("/") == "/congrats"
        )
        if not is_trusted_lofi_command(
            message,
            context,
            completion_view=completion_view,
        ):
            return handled
        if message == "lofi-town:open":
            self.show_lofi_town()
            return (True, None)
        outcome = self._review_session.handle_command(
            message,
            self._review_session_config(),
        )
        if outcome is None:
            return handled
        if outcome.show_town:
            self.show_lofi_town()
        self._update_session_web(context)
        return (True, None)

    def show_lofi_town(self) -> None:
        if self.dock is None:
            return
        self.dock.show()
        self.dock.raise_()
        self.action.setChecked(True)

    def _update_session_web(self, context: Any) -> None:
        bottom = getattr(context, "bottom", None)
        web = getattr(bottom, "web", None)
        if web is None:
            reviewer = getattr(mw, "reviewer", None)
            web = getattr(getattr(reviewer, "bottom", None), "web", None)
        if web is None:
            return
        payload = json.dumps(
            self._review_session.payload(),
            separators=(",", ":"),
        )
        web.eval(f"window.__lofiTownSession?.update({payload});")

    def _review_session_config(self) -> ReviewSessionConfig:
        return ReviewSessionConfig.from_config(self._theme_config)

    def apply_native_style(self, *_args: Any) -> None:
        apply_native_style(mw, self._theme_config, theme_manager.night_mode)

    def _read_theme_config(self) -> dict[str, Any]:
        current: dict[str, Any] = mw.addonManager.getConfig(__name__) or {}
        return normalize_config(current.get("theme"))

    def _write_theme_config(self, config: dict[str, Any]) -> None:
        self._theme_config = normalize_config(config)
        self._review_session.apply_config_change(self._review_session_config())
        current: dict[str, Any] = mw.addonManager.getConfig(__name__) or {}
        current["theme"] = self._theme_config
        mw.addonManager.writeConfig(__name__, current)
        if self.dock is not None:
            self.dock.set_motion(self._theme_config["motion"])
        self.apply_native_style()

    @staticmethod
    def _ankihub_installed() -> bool:
        if any(
            name == "ankihub" or name.startswith("ankihub.") for name in sys.modules
        ):
            return True
        for addon_id in mw.addonManager.allAddons():
            try:
                if "ankihub" in mw.addonManager.addonName(addon_id).lower():
                    return True
            except Exception:
                continue
        return False

    @staticmethod
    def _read_state() -> DockState:
        return normalize_state(mw.addonManager.getConfig(__name__))

    @staticmethod
    def _write_state(state: DockState) -> None:
        current: dict[str, Any] = mw.addonManager.getConfig(__name__) or {}
        current.update(state)
        mw.addonManager.writeConfig(__name__, current)


_controller: AddonController | None = None


def initialize() -> None:
    global _controller
    if _controller is not None:
        return
    _controller = AddonController()
    _controller.start()
