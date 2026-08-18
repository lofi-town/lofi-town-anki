from __future__ import annotations

from pathlib import Path

from aqt.qt import QLabel, QMovie, QSize, Qt, QWidget


class CozyBunnyLabel(QLabel):
    def __init__(
        self,
        resources_path: Path,
        size: QSize,
        parent: QWidget,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("CozyBunny")
        self.setFixedSize(size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._movie = QMovie(
            str(resources_path / "animations" / "cozy-bunny.gif")
        )
        self._movie.setCacheMode(QMovie.CacheMode.CacheAll)
        self._movie.setScaledSize(size)
        self.setMovie(self._movie)
        self._motion = "system"
        self._active = True
        self._sync_playback()

    def set_motion(self, motion: str) -> None:
        self._motion = motion
        self._sync_playback()

    def set_active(self, active: bool) -> None:
        self._active = active
        self._sync_playback()

    def _sync_playback(self) -> None:
        if self._active and self._motion != "reduced":
            self._movie.start()
            return
        self._movie.stop()
        if self._motion == "reduced":
            self._movie.jumpToFrame(0)
