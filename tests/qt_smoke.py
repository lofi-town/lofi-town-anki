from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")

from aqt.qt import QApplication, QMainWindow, QMovie, QTimer, QUrl, QWebEnginePage

from addon.configuration import DEFAULT_CONFIG
from addon.dock import LofiTownDock
from addon.fonts import load_cozy_font_family
from addon.settings_dialog import ThemeSettingsDialog
from addon.state import DEFAULT_STATE


def main() -> None:
    app = QApplication.instance() or QApplication(["lofi-town-anki-smoke"])
    failures: list[BaseException] = []
    with tempfile.TemporaryDirectory() as directory:
        window: QMainWindow | None = None
        dock: LofiTownDock | None = None

        def construct_and_dispose() -> None:
            nonlocal dock, window
            try:
                window = QMainWindow()
                addon_path = Path(directory)
                (addon_path / "user_files").mkdir()
                resources = Path(__file__).parents[1] / "addon" / "resources"
                (addon_path / "resources").symlink_to(resources)
                dock = LofiTownDock(
                    DEFAULT_STATE.copy(),
                    addon_path,
                    lambda _state: None,
                    window,
                )
                font_family = load_cozy_font_family()
                assert font_family
                assert dock.font().family() == font_family
                assert dock.loading_mascot.movie().isValid()
                assert dock.loading_mascot.movie().frameCount() > 1
                dock.set_motion("reduced")
                assert (
                    dock.loading_mascot.movie().state()
                    == QMovie.MovieState.NotRunning
                )
                assert dock.webview.page() is not None
                assert any(
                    script.name() == "lofi-town-anki-bridge"
                    for script in dock.webview.profile.scripts().toList()
                )
                dock.stack.setCurrentWidget(dock.webview)
                dock._on_load_started()
                assert dock.stack.currentWidget() is dock.loading_view
                accepted = dock.webview.trusted_page.acceptNavigationRequest(
                    QUrl("javascript:alert(1)"),
                    QWebEnginePage.NavigationType.NavigationTypeLinkClicked,
                    True,
                )
                assert not accepted
                dock._on_load_finished(False)
                assert dock.stack.currentWidget() is dock.webview
                dock.webview.bridge.getOAuthCallbackUrl()
                assert dock.webview.bridge._callback_server.running

                saved_themes: list[dict[str, object]] = []
                settings = ThemeSettingsDialog(
                    window,
                    DEFAULT_CONFIG,
                    dark_mode=True,
                    ankihub_installed=False,
                    save=saved_themes.append,
                )
                assert settings.font().family() == font_family
                assert settings._preview_mascot.movie().isValid()
                settings._set_combo(settings._motion, "reduced")
                assert (
                    settings._preview_mascot.movie().state()
                    == QMovie.MovieState.NotRunning
                )
                settings._palette_buttons["grape"].click()
                assert settings._draft["palette"] == "grape"
                settings._set_combo(settings._focus_minutes, 50)
                settings._on_control_change()
                assert settings._draft["focus_minutes"] == 50
                assert not settings._preview_session.isHidden()
                settings._save_and_close()
                assert saved_themes[0]["palette"] == "grape"
                settings.deleteLater()

                dock.dispose()
                assert not dock.webview.bridge._callback_server.running
                dock.deleteLater()
                window.deleteLater()
            except BaseException as error:
                failures.append(error)
            finally:
                QTimer.singleShot(250, app.quit)

        QTimer.singleShot(0, construct_and_dispose)
        app.exec()
    if failures:
        raise failures[0]


if __name__ == "__main__":
    main()
