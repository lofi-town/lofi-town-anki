from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

from aqt.qt import (
    QDesktopServices,
    QFile,
    QIODevice,
    QObject,
    QUrl,
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineScript,
    QWebEngineScriptCollection,
    pyqtSignal,
    pyqtSlot,
)

if TYPE_CHECKING:
    from PyQt6.QtWebChannel import QWebChannel
else:
    from aqt.qt import QWebChannel

from .constants import BRIDGE_API_VERSION, OAUTH_TIMEOUT_SECONDS
from .focus_sync import (
    decode_focus_state,
    normalize_focus_request,
)
from .oauth_callback import OAuthCallbackServer
from .security import is_safe_external_url, is_safe_oauth_authorization_url


class NativeBridge(QObject):
    oauthCallback = pyqtSignal(str)
    focusRequestChanged = pyqtSignal(str)
    focusStateReported = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._callback_server = OAuthCallbackServer(
            self.oauthCallback.emit,
            timeout_seconds=OAUTH_TIMEOUT_SECONDS,
        )
        self._focus_request: dict[str, object] | None = None

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

    @pyqtSlot(result="QString")
    def getFocusRequest(self) -> str:
        return _result(ok=True, value=self._focus_request)

    @pyqtSlot(str, result="QString")
    def reportFocusState(self, raw: str) -> str:
        try:
            state = decode_focus_state(raw)
        except ValueError:
            return _result(ok=False, message="The focus state was rejected.")
        encoded = json.dumps(state, separators=(",", ":"), sort_keys=True)
        self.focusStateReported.emit(encoded)
        return _result(ok=True)

    def set_focus_request(self, request: dict[str, object] | None) -> None:
        self._focus_request = normalize_focus_request(request)
        encoded = json.dumps(
            self._focus_request,
            separators=(",", ":"),
            sort_keys=True,
        )
        self.focusRequestChanged.emit(encoded)

    def shutdown(self) -> None:
        self._callback_server.cancel()


def install_bridge(page: QWebEnginePage, bridge: NativeBridge) -> QWebChannel:
    channel = QWebChannel(page)
    channel.registerObject("lofiTownAnki", bridge)
    page.setWebChannel(channel)
    profile = cast(QWebEngineProfile, page.profile())
    scripts = cast(QWebEngineScriptCollection, profile.scripts())
    scripts.insert(_bridge_script())
    return channel


def _result(
    *,
    ok: bool,
    value: Any = None,
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
  const oauthListeners = new Set();
  const focusListeners = new Set();
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
            for (const listener of [...oauthListeners]) listener(value);
          }});
          nativeBridge.focusRequestChanged.connect(raw => {{
            try {{
              const request = typeof raw === 'string' ? JSON.parse(raw) : raw;
              for (const listener of [...focusListeners]) listener(request);
            }} catch {{
              // Native payloads are validated before emission.
            }}
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
      oauthListeners.add(listener);
      void ready.catch(() => oauthListeners.delete(listener));
      return () => oauthListeners.delete(listener);
    }},
    getFocusRequest: async () =>
      (await requireSuccess('getFocusRequest')).value ?? null,
    onFocusRequest: listener => {{
      if (typeof listener !== 'function') return () => {{}};
      focusListeners.add(listener);
      void ready.catch(() => focusListeners.delete(listener));
      return () => focusListeners.delete(listener);
    }},
    reportFocusState: state =>
      call('reportFocusState', [JSON.stringify(state)])
  }});

  Object.defineProperty(window, '__LOFI_TOWN_ANKI__', {{
    value: bridge,
    configurable: false,
    enumerable: false,
    writable: false
  }});
}})();
"""
