from __future__ import annotations

from pathlib import Path
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import QAction, Qt, QTimer

from .constants import ADDON_NAME
from .dock import LofiTownDock
from .state import DockState, normalize_state


class AddonController:
    def __init__(self) -> None:
        self.dock: LofiTownDock | None = None
        self.action = QAction(ADDON_NAME, mw)
        self.action.setCheckable(True)
        self.action.setEnabled(False)
        self.action.setToolTip("Show or hide Lofi Town")
        self.action.triggered.connect(self._toggle_dock)
        mw.form.menuTools.addAction(self.action)

    def start(self) -> None:
        gui_hooks.profile_did_open.append(self.on_profile_open)
        gui_hooks.profile_will_close.append(self.on_profile_close)

    def on_profile_open(self) -> None:
        if self.dock is not None:
            return

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
