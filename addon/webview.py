from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from aqt.qt import (
    QDesktopServices,
    QObject,
    Qt,
    QUrl,
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineView,
    pyqtSignal,
)

from .bridge import NativeBridge, install_bridge
from .constants import APP_ORIGIN, APP_URL
from .security import is_allowed_app_url, is_safe_external_url


class TrustedPage(QWebEnginePage):
    def __init__(
        self,
        profile: QWebEngineProfile,
        allowed_origin: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(profile, parent)
        self._allowed_origin = allowed_origin

    def acceptNavigationRequest(
        self,
        url: QUrl,
        navigation_type: QWebEnginePage.NavigationType,
        is_main_frame: bool,
    ) -> bool:
        value = url.toString()
        if not is_main_frame:
            if value == "about:blank" or url.scheme() in {"data", "blob"}:
                return True
            return is_allowed_app_url(
                value, self._allowed_origin
            ) or is_safe_external_url(value)

        if value == "about:blank":
            return True
        if is_allowed_app_url(value, self._allowed_origin):
            return True
        if is_safe_external_url(value):
            QDesktopServices.openUrl(url)
        return False


class LofiWebView(QWebEngineView):
    processFailed = pyqtSignal()

    def __init__(
        self,
        user_files_path: Path,
        zoom_factor: float,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAcceptDrops(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        profile_path = user_files_path / "web-profile"
        cache_path = user_files_path / "web-cache"
        profile_path.mkdir(parents=True, exist_ok=True)
        cache_path.mkdir(parents=True, exist_ok=True)

        self.profile = QWebEngineProfile("lofi-town-anki", self)
        self.profile.setPersistentStoragePath(str(profile_path))
        self.profile.setCachePath(str(cache_path))
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        self.profile.downloadRequested.connect(lambda download: download.cancel())

        self.bridge = NativeBridge(self)
        self.trusted_page = TrustedPage(self.profile, APP_ORIGIN, self)
        self.channel = install_bridge(self.trusted_page, self.bridge)
        self.setPage(self.trusted_page)
        self.setZoomFactor(zoom_factor)
        self._configure_settings()
        self._configure_permissions()

        self.trusted_page.newWindowRequested.connect(self._open_new_window)
        self.trusted_page.renderProcessTerminated.connect(
            lambda *_args: self.processFailed.emit()
        )

    def load_app(self) -> None:
        self.load(QUrl(APP_URL))

    def dispose(self) -> None:
        self.bridge.shutdown()
        self.stop()
        old_page = self.page()
        self.setPage(QWebEnginePage(self))
        old_page.deleteLater()
        self.profile.deleteLater()

    def _configure_settings(self) -> None:
        settings = self.settings()
        attributes = QWebEngineSettings.WebAttribute
        values = {
            attributes.JavascriptEnabled: True,
            attributes.LocalStorageEnabled: True,
            attributes.WebGLEnabled: True,
            attributes.Accelerated2dCanvasEnabled: True,
            attributes.PlaybackRequiresUserGesture: True,
            attributes.AllowRunningInsecureContent: False,
            attributes.LocalContentCanAccessRemoteUrls: False,
            attributes.JavascriptCanAccessClipboard: False,
            attributes.ScreenCaptureEnabled: False,
        }
        for attribute, enabled in values.items():
            settings.setAttribute(attribute, enabled)

    def _configure_permissions(self) -> None:
        permission_requested = getattr(self.trusted_page, "permissionRequested", None)
        if permission_requested is not None:
            permission_requested.connect(lambda permission: permission.deny())

        feature_requested = getattr(
            self.trusted_page, "featurePermissionRequested", None
        )
        if feature_requested is not None:
            feature_requested.connect(
                lambda origin, feature: self.trusted_page.setFeaturePermission(
                    origin,
                    feature,
                    QWebEnginePage.PermissionPolicy.PermissionDeniedByUser,
                )
            )

        full_screen_requested = getattr(self.trusted_page, "fullScreenRequested", None)
        if full_screen_requested is not None:
            full_screen_requested.connect(lambda request: request.reject())

    @staticmethod
    def _open_new_window(request: object) -> None:
        requested_url: Callable[[], QUrl] | None = getattr(
            request, "requestedUrl", None
        )
        if requested_url is None:
            return
        url = requested_url()
        if is_safe_external_url(url.toString()):
            QDesktopServices.openUrl(url)
