from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")

from aqt.qt import (
    QApplication,
    QEventLoop,
    QMainWindow,
    QMovie,
    Qt,
    QTimer,
    QUrl,
    QWebEnginePage,
)

from addon.configuration import DEFAULT_CONFIG
from addon.dock import LofiTownDock
from addon.fonts import load_cozy_font_family
from addon.settings_dialog import ThemeSettingsDialog
from addon.state import DEFAULT_STATE
from addon.web_assets import build_recap_bootstrap, build_session_bootstrap

WEB_ROOT = Path(__file__).resolve().parents[1] / "addon" / "web"


def run_web_script(
    window: QMainWindow,
    html: str,
    url: str,
    expression: str,
) -> dict[str, object]:
    page = QWebEnginePage(window)
    result: list[dict[str, object]] = []
    loop = QEventLoop()
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)

    def finish(value: dict[str, object]) -> None:
        result.append(value)
        loop.quit()

    def capture(loaded: bool) -> None:
        if not loaded:
            result.append({"loaded": False})
            loop.quit()
            return
        page.runJavaScript(expression, finish)

    page.loadFinished.connect(capture)
    page.setHtml(html, QUrl(url))
    timeout.start(5_000)
    loop.exec()
    page.deleteLater()
    assert result
    return result[0]


def check_session_hud(window: QMainWindow) -> None:
    config = {
        **DEFAULT_CONFIG,
        "focus_minutes": 37,
        "session_target_answers": 10,
        "hud_show_remaining": False,
        "hud_show_timer": False,
        "hud_position": "bottom",
    }
    session = {
        "phase": "focusing",
        "startedAt": 1_000,
        "focusStartedAt": 1_000,
        "focusPausedAt": 0,
        "focusPausedTotal": 0,
        "completedFocusMs": 0,
        "breakStartedAt": 0,
        "answers": 7,
        "targetAnswers": 10,
        "targetStartedAnswers": 0,
    }
    script = build_session_bootstrap(config, session)
    runtime = (WEB_ROOT / "review_session.js").read_text(encoding="utf-8")
    html = f"""
    <html><body>
      <div id="outer">
        <span class="new-count">3</span>
        <span class="learn-count">2</span>
        <span class="review-count">5</span>
      </div>
      {script}
      <script>{runtime}</script>
    </body></html>
    """

    result = run_web_script(
        window,
        html,
        "https://anki.local/reviewer",
        """
        (() => {
          window.pycmd = (command) => { window.__lofiCommand = command; };
          const answerText = document
            .getElementById("lofi-session-answers")?.textContent;
          const progress = document
            .getElementById("lofi-session-progress-fill")?.style.width;
          window.__lofiTownSession.update({
            targetAnswers: 0,
            targetStartedAnswers: 7,
          });
          document.getElementById("lofi-session-answers")?.click();
          const goalPickerOpened = !document
            .getElementById("lofi-session-goal-picker")?.hidden;
          const goalChoice = document.getElementById("lofi-session-goal-choice");
          goalChoice.value = "50";
          goalChoice.dispatchEvent(new Event("change"));
          const customGoalDisabled = document
            .getElementById("lofi-session-goal-custom")?.disabled;
          document.getElementById("lofi-session-goal-picker")?.requestSubmit();
          return {
            loaded: true,
            hud: Boolean(document.getElementById("lofi-session-hud")),
            position: document.getElementById("outer").nextElementSibling?.id,
            answers: answerText,
            customGoalDisabled,
            goalPickerOpened,
            goalPickerHiddenAfterChoice: document
              .getElementById("lofi-session-goal-picker")?.hidden,
            goalCommand: window.__lofiCommand,
            remainingHidden: document.getElementById("lofi-session-workload")?.hidden,
            timerHidden: document.getElementById("lofi-session-time")?.hidden,
            progress,
          };
        })()
        """,
    )
    expected = {
        "loaded": True,
        "hud": True,
        "position": "lofi-session-hud",
        "answers": "3 to goal",
        "customGoalDisabled": True,
        "goalPickerOpened": True,
        "goalPickerHiddenAfterChoice": True,
        "goalCommand": "lofi-town:set-target:50",
        "remainingHidden": True,
        "timerHidden": True,
        "progress": "70%",
    }
    assert result == expected, result


def check_session_recap(window: QMainWindow) -> None:
    bootstrap = build_recap_bootstrap(
        DEFAULT_CONFIG,
        {
            "answers": 60,
            "focusedMs": 1_500_000,
            "blocksCompleted": 1,
            "targetAnswers": 60,
            "targetProgress": 60,
            "targetsCompleted": 1,
        },
    )
    runtime = (WEB_ROOT / "session_recap.js").read_text(encoding="utf-8")
    html = f"""
    <html><body>
      <main class="congrats"></main>
      {bootstrap}
      <script>{runtime}</script>
    </body></html>
    """

    result = run_web_script(
        window,
        html,
        "https://anki.local/congrats",
        """
        (() => ({
          loaded: true,
          recap: Boolean(document.getElementById("lofi-town-recap")),
          text: document.getElementById("lofi-town-recap")?.textContent,
          dismiss: Boolean(document.getElementById("lofi-town-recap-dismiss")),
          open: Boolean(document.getElementById("lofi-town-completion-open")),
        }))()
        """,
    )
    assert result["loaded"] is True
    assert result["recap"] is True
    assert "60 answers" in result["text"]
    assert "25 min focused" in result["text"]
    assert result["dismiss"] is True
    assert result["open"] is True


def run_smoke(addon_path: Path) -> None:
    app = QApplication.instance() or QApplication(["lofi-town-anki-smoke"])
    failures: list[BaseException] = []
    window: QMainWindow | None = None
    dock: LofiTownDock | None = None

    def construct_and_dispose() -> None:
        nonlocal dock, window
        try:
            window = QMainWindow()
            (addon_path / "user_files").mkdir()
            resources = Path(__file__).parents[1] / "addon" / "resources"
            (addon_path / "resources").symlink_to(resources)
            dock = LofiTownDock(
                DEFAULT_STATE.copy(),
                addon_path,
                lambda _state: None,
                window,
            )
            window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            font_family = load_cozy_font_family()
            assert font_family
            assert dock.font().family() == font_family
            assert dock.loading_mascot.movie().isValid()
            assert dock.loading_mascot.movie().frameCount() > 1
            dock.set_motion("reduced")
            assert (
                dock.loading_mascot.movie().state() == QMovie.MovieState.NotRunning
            )
            assert dock.webview.page() is not None
            assert any(
                script.name() == "lofi-town-anki-bridge"
                for script in dock.webview.profile.scripts().toList()
            )
            assert dock.title_bar.floating_button.toolTip() == "Pop Lofi Town out"
            dock.title_bar.floating_button.click()
            assert dock.isFloating()
            assert dock.title_bar.floating_button.toolTip() == "Dock Lofi Town in Anki"
            dock.title_bar.floating_button.click()
            assert not dock.isFloating()
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
            check_session_hud(window)
            check_session_recap(window)

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
            study = settings._study_settings
            study.focus_minutes.setValue(40)
            study.break_minutes.setValue(8)
            study.session_target_answers.setValue(60)
            study._set_combo(study.hud_position, "bottom")
            study.hud_compact.click()
            settings._on_control_change()
            assert settings._draft["focus_minutes"] == 40
            assert settings._draft["break_minutes"] == 8
            assert settings._draft["session_target_answers"] == 60
            assert settings._draft["hud_position"] == "bottom"
            assert settings._draft["hud_compact"] is True
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


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        subprocess.run(
            [sys.executable, __file__, "--worker", directory],
            check=True,
        )


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        run_smoke(Path(sys.argv[2]))
    else:
        main()
