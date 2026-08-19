from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from aqt.qt import (
    QByteArray,
    QDockWidget,
    QFont,
    QHBoxLayout,
    QIcon,
    QLabel,
    QMainWindow,
    QMouseEvent,
    QPixmap,
    QProgressBar,
    QPushButton,
    QResizeEvent,
    QSize,
    QStackedWidget,
    Qt,
    QTimer,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .constants import ADDON_NAME, APP_URL, DOCK_OBJECT_NAME
from .fonts import load_cozy_font_family
from .mascot import CozyBunnyLabel
from .state import DockState
from .webview import LofiWebView


class CozyTitleBar(QWidget):
    def __init__(
        self,
        resources_path: Path,
        on_reload: Callable[[], None],
        on_toggle_floating: Callable[[], None],
        on_open_external: Callable[[], None],
        on_hide: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._resources_path = resources_path
        self.setObjectName("CozyTitleBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 10, 8)
        layout.setSpacing(8)

        icon_label = QLabel(self)
        icon_label.setObjectName("BrandIcon")
        icon_label.setFixedSize(32, 32)
        pixmap = QPixmap(str(resources_path / "lofitownicon.png"))
        icon_label.setPixmap(
            pixmap.scaled(
                30,
                30,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
        )

        name = QLabel("lofi.town", self)
        name.setObjectName("BrandName")

        layout.addWidget(icon_label)
        layout.addWidget(name)
        layout.addStretch(1)
        layout.addWidget(
            self._button(
                resources_path / "icons" / "reload.svg",
                "Reload Lofi Town",
                on_reload,
            )
        )
        self.floating_button = self._button(
            resources_path / "icons" / "pop-out.svg",
            "Pop Lofi Town out",
            on_toggle_floating,
        )
        layout.addWidget(self.floating_button)
        layout.addWidget(
            self._button(
                resources_path / "icons" / "external-link.svg",
                "Open Lofi Town in your browser",
                on_open_external,
            )
        )
        layout.addWidget(
            self._button(
                resources_path / "icons" / "close.svg",
                "Hide Lofi Town",
                on_hide,
                object_name="CloseButton",
            )
        )

    def set_floating(self, floating: bool) -> None:
        icon_name = "dock.svg" if floating else "pop-out.svg"
        tooltip = "Dock Lofi Town in Anki" if floating else "Pop Lofi Town out"
        self.floating_button.setIcon(
            QIcon(str(self._resources_path / "icons" / icon_name))
        )
        self.floating_button.setToolTip(tooltip)
        self.floating_button.setAccessibleName(tooltip)

    def mouseDoubleClickEvent(self, event: QMouseEvent | None) -> None:
        dock = self.parentWidget()
        if isinstance(dock, QDockWidget):
            dock.setFloating(not dock.isFloating())
        super().mouseDoubleClickEvent(event)

    def _button(
        self,
        icon_path: Path,
        tooltip: str,
        callback: Callable[[], None],
        object_name: str = "TitleButton",
    ) -> QToolButton:
        button = QToolButton(self)
        button.setObjectName(object_name)
        button.setIcon(QIcon(str(icon_path)))
        button.setIconSize(QSize(17, 17))
        button.setFixedSize(32, 32)
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        button.clicked.connect(callback)
        return button


class LofiTownDock(QDockWidget):
    def __init__(
        self,
        state: DockState,
        addon_path: Path,
        on_state_change: Callable[[DockState], None],
        parent: QMainWindow,
        motion: str = "system",
    ) -> None:
        super().__init__(ADDON_NAME, parent)
        self.setObjectName(DOCK_OBJECT_NAME)
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.setMinimumWidth(320)
        self._state = state
        self._on_state_change = on_state_change
        self._disposed = False
        self._navigation_rejected = False
        self._last_area = state["area"]
        self._resources_path = addon_path / "resources"
        self._motion = motion

        if font_family := load_cozy_font_family():
            self.setFont(QFont(font_family))
        self.setStyleSheet(_stylesheet())

        self.webview = LofiWebView(
            addon_path / "user_files",
            zoom_factor=state["zoom_factor"],
            parent=self,
        )
        self.stack = QStackedWidget(self)
        self.loading_view, self.progress = self._build_loading_view()
        self.error_view = self._build_error_view()
        self.stack.addWidget(self.loading_view)
        self.stack.addWidget(self.webview)
        self.stack.addWidget(self.error_view)
        self.setWidget(self.stack)

        self.title_bar = CozyTitleBar(
            self._resources_path,
            self.reload_app,
            self.toggle_floating,
            self.open_in_browser,
            self.hide,
            self,
        )
        self.setTitleBarWidget(self.title_bar)

        self.webview.loadStarted.connect(self._on_load_started)
        self.webview.loadProgress.connect(self.progress.setValue)
        self.webview.loadFinished.connect(self._on_load_finished)
        self.webview.navigationRejected.connect(self._on_navigation_rejected)
        self.webview.processFailed.connect(self._show_error)
        self.visibilityChanged.connect(lambda _visible: self._schedule_state_save())
        self.topLevelChanged.connect(self._on_top_level_changed)
        self.dockLocationChanged.connect(self._on_dock_location_changed)

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(250)
        self._save_timer.timeout.connect(self._save_state)
        self.stack.setCurrentWidget(self.loading_view)
        self.webview.load_app()

    def restore_floating_geometry(self) -> None:
        geometry = self._state["geometry"]
        if geometry:
            self.restoreGeometry(QByteArray.fromBase64(geometry.encode("ascii")))

    def reload_app(self) -> None:
        self.stack.setCurrentWidget(self.loading_view)
        self.loading_mascot.set_active(True)
        self.progress.setValue(0)
        self.webview.reload()

    def set_motion(self, motion: str) -> None:
        self._motion = motion
        self.loading_mascot.set_motion(motion)

    def open_in_browser(self) -> None:
        self.webview.bridge.openExternal(APP_URL)

    def toggle_floating(self) -> None:
        self.setFloating(not self.isFloating())

    def capture_state(self) -> DockState:
        width = self.width() if not self.isFloating() else self._state["width"]
        return {
            "visible": self.isVisible(),
            "area": self._last_area,
            "width": max(320, width),
            "floating": self.isFloating(),
            "geometry": self.saveGeometry().toBase64().data().decode("ascii")
            if self.isFloating()
            else self._state["geometry"],
            "zoom_factor": self.webview.zoomFactor(),
        }

    def dispose(self) -> None:
        self._disposed = True
        self._save_timer.stop()
        self.loading_mascot.set_active(False)
        self.webview.dispose()

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        super().resizeEvent(event)
        self._schedule_state_save()

    def _build_loading_view(self) -> tuple[QWidget, QProgressBar]:
        view = QWidget(self)
        view.setObjectName("StatusView")
        layout = QVBoxLayout(view)
        layout.setContentsMargins(34, 34, 34, 34)
        layout.setSpacing(12)
        layout.addStretch(2)

        self.loading_mascot = CozyBunnyLabel(
            self._resources_path,
            QSize(102, 120),
            view,
        )
        self.loading_mascot.set_motion(self._motion)
        title = QLabel("Loading Lofi Town", view)
        title.setObjectName("StatusTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress = QProgressBar(view)
        progress.setObjectName("LoadProgress")
        progress.setRange(0, 100)
        progress.setTextVisible(False)
        progress.setFixedHeight(8)

        layout.addWidget(self.loading_mascot, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addWidget(progress)
        layout.addStretch(3)
        return view, progress

    def _build_error_view(self) -> QWidget:
        view = QWidget(self)
        view.setObjectName("StatusView")
        layout = QVBoxLayout(view)
        layout.setContentsMargins(34, 34, 34, 34)
        layout.setSpacing(12)
        layout.addStretch(2)

        icon = QLabel("☁", view)
        icon.setObjectName("OfflineIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Lofi Town is unavailable", view)
        title.setObjectName("StatusTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copy = QLabel("Check your connection and try again.", view)
        copy.setObjectName("StatusCopy")
        copy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        retry = QPushButton("Try again", view)
        retry.setObjectName("PrimaryButton")
        retry.clicked.connect(self.reload_app)
        browser = QPushButton("Open in browser", view)
        browser.setObjectName("SecondaryButton")
        browser.clicked.connect(self.open_in_browser)

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(copy)
        layout.addSpacing(8)
        layout.addWidget(retry)
        layout.addWidget(browser)
        layout.addStretch(3)
        return view

    def _on_load_started(self) -> None:
        self._navigation_rejected = False
        self.progress.setValue(0)
        self.loading_mascot.set_active(True)
        self.stack.setCurrentWidget(self.loading_view)

    def _on_load_finished(self, succeeded: bool) -> None:
        self.loading_mascot.set_active(False)
        if self._navigation_rejected:
            self._navigation_rejected = False
            self.stack.setCurrentWidget(self.webview)
            return
        self.stack.setCurrentWidget(self.webview if succeeded else self.error_view)

    def _on_navigation_rejected(self) -> None:
        self._navigation_rejected = True
        self.stack.setCurrentWidget(self.webview)

    def _show_error(self) -> None:
        self.loading_mascot.set_active(False)
        self.stack.setCurrentWidget(self.error_view)

    def _on_dock_location_changed(self, area: Qt.DockWidgetArea) -> None:
        if area == Qt.DockWidgetArea.LeftDockWidgetArea:
            self._last_area = "left"
        elif area == Qt.DockWidgetArea.RightDockWidgetArea:
            self._last_area = "right"
        self._schedule_state_save()

    def _on_top_level_changed(self, floating: bool) -> None:
        self.title_bar.set_floating(floating)
        self._schedule_state_save()

    def _schedule_state_save(self) -> None:
        if not self._disposed and hasattr(self, "_save_timer"):
            self._save_timer.start()

    def _save_state(self) -> None:
        if self._disposed:
            return
        self._state = self.capture_state()
        self._on_state_change(self._state)


def _stylesheet() -> str:
    return """
#lofi-town-anki-dock {
    background: #f6e6c4;
    color: #4a2e12;
}
#CozyTitleBar {
    background: #fff7e6;
    border-bottom: 1px solid #f0e2c4;
}
#BrandIcon {
    background: #dfeaa0;
    border: 1px solid #d2df8a;
    border-radius: 10px;
}
#BrandName {
    color: #4a2e12;
    font-size: 15px;
    font-weight: 800;
}
QToolButton#TitleButton, QToolButton#CloseButton {
    background: #fffdf5;
    border: 1px solid #e3c98c;
    border-radius: 16px;
}
QToolButton#TitleButton:hover { background: #ffe7bf; }
QToolButton#CloseButton:hover { background: #fde4e0; border-color: #e986a1; }
QToolButton#TitleButton:pressed, QToolButton#CloseButton:pressed {
    background: #e3c388;
    padding-top: 2px;
}
#StatusView { background: #f6e6c4; }
#CozyBunny { background: transparent; }
#OfflineIcon {
    color: #2fa5c4;
    font-size: 54px;
    font-weight: 800;
}
#StatusTitle {
    color: #4a2e12;
    font-size: 22px;
    font-weight: 800;
}
#StatusCopy { color: #6e4e28; font-size: 13px; font-weight: 600; }
#LoadProgress {
    background: #ead9b2;
    border: 0;
    border-radius: 4px;
}
#LoadProgress::chunk { background: #f2762e; border-radius: 4px; }
QPushButton#PrimaryButton, QPushButton#SecondaryButton {
    min-height: 42px;
    border-radius: 14px;
    font-size: 14px;
    font-weight: 800;
    padding: 0 18px;
}
QPushButton#PrimaryButton {
    color: #fff7e6;
    background: #f2762e;
    border: 1px solid #c4551a;
}
QPushButton#PrimaryButton:hover { background: #e96923; }
QPushButton#PrimaryButton:pressed { padding-top: 3px; background: #c4551a; }
QPushButton#SecondaryButton {
    color: #6e4e28;
    background: #fffdf5;
    border: 1px solid #e3c98c;
}
QPushButton#SecondaryButton:hover { background: #ffe7bf; }
QPushButton#SecondaryButton:pressed { padding-top: 3px; background: #e3c388; }
"""
