from __future__ import annotations

import json
from typing import TYPE_CHECKING

from aqt.qt import (
    QDesktopServices,
    QFile,
    QIODevice,
    QObject,
    QUrl,
    QWebEnginePage,
    QWebEngineScript,
    pyqtSignal,
    pyqtSlot,
)

if TYPE_CHECKING:
    from PyQt6.QtWebChannel import QWebChannel
else:
    from aqt.qt import QWebChannel

from .constants import BRIDGE_API_VERSION, OAUTH_TIMEOUT_SECONDS
from .oauth_callback import OAuthCallbackServer
from .security import is_safe_external_url, is_safe_oauth_authorization_url


class NativeBridge(QObject):
    oauthCallback = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._callback_server = OAuthCallbackServer(
            self.oauthCallback.emit,
            timeout_seconds=OAUTH_TIMEOUT_SECONDS,
        )

    @pyqtSlot(result="QString")
    def getOAuthCallbackUrl(self) -> str:
        try:
            value = self._callback_server.start()
            return _result(ok=True, value=value)
        except OSError:
            return _result(
                ok=False,
                message="Could not start the local sign-in callback.",
            )

    @pyqtSlot(str, result="QString")
    def beginOAuth(self, authorization_url: str) -> str:
        if not is_safe_oauth_authorization_url(authorization_url):
            self._callback_server.cancel()
            return _result(ok=False, message="The sign-in URL was rejected.")
        if not self._callback_server.running:
            return _result(
                ok=False,
                message="The sign-in callback is no longer active.",
            )

        opened = QDesktopServices.openUrl(QUrl(authorization_url))
        if not opened:
            self._callback_server.cancel()
            return _result(ok=False, message="Could not open the system browser.")
        return _result(ok=True)

    @pyqtSlot(str, result="QString")
    def openExternal(self, value: str) -> str:
        if not is_safe_external_url(value):
            return _result(ok=False, message="The external link was rejected.")
        if not QDesktopServices.openUrl(QUrl(value)):
            return _result(ok=False, message="Could not open the system browser.")
        return _result(ok=True)

    def shutdown(self) -> None:
        self._callback_server.cancel()


def install_bridge(page: QWebEnginePage, bridge: NativeBridge) -> QWebChannel:
    channel = QWebChannel(page)
    channel.registerObject("lofiTownAnki", bridge)
    page.setWebChannel(channel)
    profile = page.profile()
    if profile is None:
        raise RuntimeError("Could not access the Lofi Town web profile.")
    scripts = profile.scripts()
    if scripts is None:
        raise RuntimeError("Could not access the Lofi Town web scripts.")
    scripts.insert(_bridge_script())
    return channel


def _result(
    *,
    ok: bool,
    value: str | None = None,
    message: str | None = None,
) -> str:
    payload: dict[str, object] = {"ok": ok}
    if value is not None:
        payload["value"] = value
    if message is not None:
        payload["message"] = message
    return json.dumps(payload)


def _bridge_script() -> QWebEngineScript:
    qwebchannel = QFile(":/qtwebchannel/qwebchannel.js")
    if not qwebchannel.open(QIODevice.OpenModeFlag.ReadOnly):
        raise RuntimeError("Could not load Qt WebChannel support.")
    source = qwebchannel.readAll().data().decode("utf-8")
    qwebchannel.close()

    script = QWebEngineScript()
    script.setName("lofi-town-anki-bridge")
    script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    script.setRunsOnSubFrames(False)
    script.setSourceCode(source + _bridge_javascript())
    return script


def _bridge_javascript() -> str:
    return f"""
(() => {{
  const listeners = new Set();
  let signalConnected = false;
  const ready = new Promise((resolve, reject) => {{
    try {{
      new QWebChannel(qt.webChannelTransport, channel => {{
        const nativeBridge = channel.objects.lofiTownAnki;
        if (!nativeBridge) {{
          reject(new Error('The Anki bridge is unavailable.'));
          return;
        }}
        if (!signalConnected) {{
          signalConnected = true;
          nativeBridge.oauthCallback.connect(value => {{
            for (const listener of [...listeners]) listener(value);
          }});
        }}
        resolve(nativeBridge);
      }});
    }} catch (error) {{
      reject(error);
    }}
  }});

  const call = (method, args = []) => ready.then(nativeBridge =>
    new Promise((resolve, reject) => {{
      const fn = nativeBridge[method];
      if (typeof fn !== 'function') {{
        reject(new Error(`The Anki bridge does not support ${{method}}.`));
        return;
      }}
      fn.apply(nativeBridge, [...args, raw => {{
        try {{
          resolve(typeof raw === 'string' ? JSON.parse(raw) : raw);
        }} catch {{
          reject(new Error('The Anki bridge returned an invalid response.'));
        }}
      }}]);
    }})
  );

  const requireSuccess = async (method, args = []) => {{
    const result = await call(method, args);
    if (!result?.ok) {{
      throw new Error(result?.message || 'The Anki bridge request failed.');
    }}
    return result;
  }};

  const bridge = Object.freeze({{
    apiVersion: {BRIDGE_API_VERSION},
    isAnkiApp: true,
    getOAuthCallbackUrl: async () =>
      (await requireSuccess('getOAuthCallbackUrl')).value,
    beginOAuth: url => call('beginOAuth', [url]),
    openExternal: url => call('openExternal', [url]),
    onOAuthCallback: listener => {{
      if (typeof listener !== 'function') return () => {{}};
      listeners.add(listener);
      void ready.catch(() => listeners.delete(listener));
      return () => listeners.delete(listener);
    }}
  }});

  Object.defineProperty(window, '__LOFI_TOWN_ANKI__', {{
    value: bridge,
    configurable: false,
    enumerable: false,
    writable: false
  }});
}})();
"""
