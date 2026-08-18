from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import QAction, Qt, QTimer
from aqt.theme import theme_manager
from aqt.webview import AnkiWebView, WebContent

from .compatibility import classify_context
from .configuration import normalize_config
from .constants import ADDON_NAME
from .dock import LofiTownDock
from .native_style import apply_native_style
from .settings_dialog import ThemeSettingsDialog
from .state import DockState, normalize_state
from .web_assets import build_bootstrap, build_dynamic_bootstrap


class AddonController:
    def __init__(self) -> None:
        self.dock: LofiTownDock | None = None
        self._theme_config = self._read_theme_config()
        self._package = mw.addonManager.addonFromModule(__name__)
        mw.addonManager.setWebExports(
            __name__,
            r"(web/.*\.css|resources/fonts/.*\.ttf)",
        )
        mw.addonManager.setConfigAction(__name__, self.open_theme_settings)

        self.action = QAction(ADDON_NAME, mw)
        self.action.setCheckable(True)
        self.action.setEnabled(False)
        self.action.setToolTip("Show or hide Lofi Town")
        self.action.triggered.connect(self._toggle_dock)
        mw.form.menuTools.addAction(self.action)

        self.appearance_action = QAction("Lofi Town Appearance...", mw)
        self.appearance_action.setObjectName("lofiTownAppearanceAction")
        self.appearance_action.setToolTip("Customize Anki's Lofi Town appearance")
        self.appearance_action.triggered.connect(self.open_theme_settings)
        mw.form.menuTools.addAction(self.appearance_action)

    def start(self) -> None:
        gui_hooks.profile_did_open.append(self.on_profile_open)
        gui_hooks.profile_will_close.append(self.on_profile_close)
        gui_hooks.webview_will_set_content.append(self.on_webview_will_set_content)
        gui_hooks.webview_did_inject_style_into_page.append(
            self.on_webview_did_inject_style_into_page
        )
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
        dock = LofiTownDock(state, addon_path, self._write_state, mw)
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

    def on_webview_did_inject_style_into_page(
        self,
        webview: AnkiWebView,
    ) -> None:
        if not self._theme_config["enabled"] or webview is not mw.web:
            return
        if webview.url().path().rstrip("/") != "/congrats":
            return
        stylesheet = f"/_addons/{self._package}/web/cozy.css"
        webview.eval(
            build_dynamic_bootstrap(
                self._theme_config,
                "congrats",
                stylesheet,
            )
        )

    def apply_native_style(self, *_args: Any) -> None:
        apply_native_style(mw, self._theme_config, theme_manager.night_mode)

    def _read_theme_config(self) -> dict[str, Any]:
        current: dict[str, Any] = mw.addonManager.getConfig(__name__) or {}
        return normalize_config(current.get("theme"))

    def _write_theme_config(self, config: dict[str, Any]) -> None:
        self._theme_config = normalize_config(config)
        current: dict[str, Any] = mw.addonManager.getConfig(__name__) or {}
        current["theme"] = self._theme_config
        mw.addonManager.writeConfig(__name__, current)
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
