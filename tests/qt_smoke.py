from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")

from aqt.qt import QApplication, QMainWindow, QTimer

from addon.dock import LofiTownDock
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
                assert dock.webview.page() is not None
                assert any(
                    script.name() == "lofi-town-anki-bridge"
                    for script in dock.webview.profile.scripts().toList()
                )
                dock.webview.bridge.getOAuthCallbackUrl()
                assert dock.webview.bridge._callback_server.running
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
