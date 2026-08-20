from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from aqt.qt import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    pyqtSignal,
)


@dataclass(frozen=True, slots=True)
class StudyCompanionValues:
    session_hud: bool
    sync_focus_with_lofi_town: bool
    focus_minutes: int
    break_minutes: int
    session_target_answers: int
    review_focus_mode: bool
    show_rating_shortcuts: bool
    lofi_town_breaks: bool
    hud_position: str
    hud_compact: bool
    hud_show_answers: bool
    hud_show_remaining: bool
    hud_show_timer: bool
    hud_show_progress: bool
    hud_show_sync_status: bool

    @classmethod
    def from_config(
        cls, config: dict[str, Any]
    ) -> StudyCompanionValues:
        return cls(
            session_hud=config["session_hud"],
            sync_focus_with_lofi_town=config["sync_focus_with_lofi_town"],
            focus_minutes=config["focus_minutes"],
            break_minutes=config["break_minutes"],
            session_target_answers=config["session_target_answers"],
            review_focus_mode=config["review_focus_mode"],
            show_rating_shortcuts=config["show_rating_shortcuts"],
            lofi_town_breaks=config["lofi_town_breaks"],
            hud_position=config["hud_position"],
            hud_compact=config["hud_compact"],
            hud_show_answers=config["hud_show_answers"],
            hud_show_remaining=config["hud_show_remaining"],
            hud_show_timer=config["hud_show_timer"],
            hud_show_progress=config["hud_show_progress"],
            hud_show_sync_status=config["hud_show_sync_status"],
        )

    def to_config(self) -> dict[str, object]:
        return {
            "session_hud": self.session_hud,
            "sync_focus_with_lofi_town": self.sync_focus_with_lofi_town,
            "focus_minutes": self.focus_minutes,
            "break_minutes": self.break_minutes,
            "session_target_answers": self.session_target_answers,
            "review_focus_mode": self.review_focus_mode,
            "show_rating_shortcuts": self.show_rating_shortcuts,
            "lofi_town_breaks": self.lofi_town_breaks,
            "hud_position": self.hud_position,
            "hud_compact": self.hud_compact,
            "hud_show_answers": self.hud_show_answers,
            "hud_show_remaining": self.hud_show_remaining,
            "hud_show_timer": self.hud_show_timer,
            "hud_show_progress": self.hud_show_progress,
            "hud_show_sync_status": self.hud_show_sync_status,
        }


class StudyCompanionSettings(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("studyCompanionSettings")
        self._loading = False
        self._master_enabled = True
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(self._section_label("Study flow"))
        self._session_row, self.session_hud = self._toggle_setting(
            "Study companion",
            "Show session facts and enable focus controls.",
        )
        self.focus_minutes = QSpinBox(self)
        self.focus_minutes.setRange(0, 180)
        self.focus_minutes.setSpecialValueText("Elapsed time only")
        self.focus_minutes.setSuffix(" min")
        focus_row = self._row_with_control(
            "Focus block",
            "A non-modal reminder that never stops review.",
            self.focus_minutes,
        )
        self.break_minutes = QSpinBox(self)
        self.break_minutes.setRange(0, 60)
        self.break_minutes.setSpecialValueText("No break timer")
        self.break_minutes.setSuffix(" min")
        break_row = self._row_with_control(
            "Break timer",
            "Optional countdown after a completed focus block.",
            self.break_minutes,
        )
        self.session_target_answers = QSpinBox(self)
        self.session_target_answers.setRange(0, 5_000)
        self.session_target_answers.setSpecialValueText("Until deck is clear")
        self.session_target_answers.setSuffix(" answers")
        target_row = self._row_with_control(
            "Answer target",
            "A local session goal that never changes scheduling.",
            self.session_target_answers,
        )
        sync_row, self.sync_focus_with_lofi_town = self._toggle_setting(
            "Sync focus time and rewards with Lofi Town",
            "Starts a private Lofi Town stopwatch after your first answer.",
        )
        quiet_row, self.review_focus_mode = self._toggle_setting(
            "Quiet reviewer",
            "Reduce peripheral controls until you move to them.",
        )
        shortcut_row, self.show_rating_shortcuts = self._toggle_setting(
            "Rating key hints",
            "Show 1, 2, 3, and 4 on answer buttons.",
        )
        handoff_row, self.lofi_town_breaks = self._toggle_setting(
            "Lofi Town break handoff",
            "Reveal the town after a focus block or completed deck.",
        )
        self._study_rows = (
            focus_row,
            break_row,
            target_row,
            sync_row,
            quiet_row,
            shortcut_row,
            handoff_row,
        )
        layout.addWidget(self._session_row)
        for row in self._study_rows:
            layout.addWidget(row)

        layout.addWidget(self._section_label("Reviewer strip"))
        self.hud_position = QComboBox(self)
        self.hud_position.addItem("Above answer buttons", "top")
        self.hud_position.addItem("Below answer buttons", "bottom")
        position_row = self._row_with_control(
            "Position",
            "Place the session strip above or below Anki's controls.",
            self.hud_position,
        )
        compact_row, self.hud_compact = self._toggle_setting(
            "Compact layout",
            "Use less space and hide the strip label.",
        )
        answers_row, self.hud_show_answers = self._toggle_setting(
            "Answer count",
            "Show reviewer answers from this session.",
        )
        remaining_row, self.hud_show_remaining = self._toggle_setting(
            "Remaining count",
            "Use only the New, Learn, and Review counts Anki displays.",
        )
        timer_row, self.hud_show_timer = self._toggle_setting(
            "Timer",
            "Show focus, break, or elapsed time.",
        )
        progress_row, self.hud_show_progress = self._toggle_setting(
            "Progress bar",
            "Track the answer target or current focus block.",
        )
        status_row, self.hud_show_sync_status = self._toggle_setting(
            "Sync status",
            "Show the compact Lofi Town connection state.",
        )
        self._hud_rows = (
            position_row,
            compact_row,
            answers_row,
            remaining_row,
            timer_row,
            progress_row,
            status_row,
        )
        for row in self._hud_rows:
            layout.addWidget(row)

        self._connect_controls()

    def load(self, config: dict[str, Any]) -> None:
        values = StudyCompanionValues.from_config(config)
        self._loading = True
        try:
            self.session_hud.setChecked(values.session_hud)
            self.sync_focus_with_lofi_town.setChecked(
                values.sync_focus_with_lofi_town
            )
            self.focus_minutes.setValue(values.focus_minutes)
            self.break_minutes.setValue(values.break_minutes)
            self.session_target_answers.setValue(values.session_target_answers)
            self._set_combo(self.hud_position, values.hud_position)
            self.hud_compact.setChecked(values.hud_compact)
            self.hud_show_answers.setChecked(values.hud_show_answers)
            self.hud_show_remaining.setChecked(values.hud_show_remaining)
            self.hud_show_timer.setChecked(values.hud_show_timer)
            self.hud_show_progress.setChecked(values.hud_show_progress)
            self.hud_show_sync_status.setChecked(values.hud_show_sync_status)
            self.review_focus_mode.setChecked(values.review_focus_mode)
            self.show_rating_shortcuts.setChecked(values.show_rating_shortcuts)
            self.lofi_town_breaks.setChecked(values.lofi_town_breaks)
        finally:
            self._loading = False
        self._update_enabled_state()

    def values(self) -> StudyCompanionValues:
        return StudyCompanionValues(
            session_hud=self.session_hud.isChecked(),
            sync_focus_with_lofi_town=(
                self.sync_focus_with_lofi_town.isChecked()
            ),
            focus_minutes=self.focus_minutes.value(),
            break_minutes=self.break_minutes.value(),
            session_target_answers=self.session_target_answers.value(),
            review_focus_mode=self.review_focus_mode.isChecked(),
            show_rating_shortcuts=self.show_rating_shortcuts.isChecked(),
            lofi_town_breaks=self.lofi_town_breaks.isChecked(),
            hud_position=cast(str, self.hud_position.currentData()),
            hud_compact=self.hud_compact.isChecked(),
            hud_show_answers=self.hud_show_answers.isChecked(),
            hud_show_remaining=self.hud_show_remaining.isChecked(),
            hud_show_timer=self.hud_show_timer.isChecked(),
            hud_show_progress=self.hud_show_progress.isChecked(),
            hud_show_sync_status=self.hud_show_sync_status.isChecked(),
        )

    def set_available(self, enabled: bool) -> None:
        self._master_enabled = enabled
        self._update_enabled_state()

    def _connect_controls(self) -> None:
        self.hud_position.currentIndexChanged.connect(self._on_change)
        for spinbox in (
            self.focus_minutes,
            self.break_minutes,
            self.session_target_answers,
        ):
            spinbox.valueChanged.connect(self._on_change)
        for checkbox in (
            self.session_hud,
            self.sync_focus_with_lofi_town,
            self.hud_compact,
            self.hud_show_answers,
            self.hud_show_remaining,
            self.hud_show_timer,
            self.hud_show_progress,
            self.hud_show_sync_status,
            self.review_focus_mode,
            self.show_rating_shortcuts,
            self.lofi_town_breaks,
        ):
            checkbox.toggled.connect(self._on_change)

    def _on_change(self, *_args: Any) -> None:
        self._update_enabled_state()
        if not self._loading:
            self.changed.emit()

    def _update_enabled_state(self) -> None:
        self._session_row.setEnabled(self._master_enabled)
        session_enabled = self._master_enabled and self.session_hud.isChecked()
        for row in (*self._study_rows, *self._hud_rows):
            row.setEnabled(session_enabled)
        has_focus_block = session_enabled and self.focus_minutes.value() > 0
        self.break_minutes.setEnabled(has_focus_block)
        self.lofi_town_breaks.setEnabled(has_focus_block)

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text.upper(), self)
        label.setObjectName("sectionLabel")
        return label

    def _setting_row(self, title: str, description: str) -> QFrame:
        row = QFrame(self)
        row.setObjectName("settingRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(12, 12, 12, 12)
        row_layout.setSpacing(12)
        copy = QWidget(row)
        copy.setObjectName("settingCopy")
        copy_layout = QVBoxLayout(copy)
        copy_layout.setContentsMargins(0, 0, 0, 0)
        copy_layout.setSpacing(2)
        title_label = QLabel(title, copy)
        title_label.setObjectName("settingTitle")
        description_label = QLabel(description, copy)
        description_label.setObjectName("settingDescription")
        description_label.setWordWrap(True)
        copy_layout.addWidget(title_label)
        copy_layout.addWidget(description_label)
        row_layout.addWidget(copy, 1)
        return row

    def _row_with_control(
        self,
        title: str,
        description: str,
        control: QWidget,
    ) -> QFrame:
        row = self._setting_row(title, description)
        control.setMinimumWidth(160)
        cast(QHBoxLayout, row.layout()).addWidget(control)
        return row

    def _toggle_setting(
        self,
        title: str,
        description: str,
    ) -> tuple[QFrame, QCheckBox]:
        row = self._setting_row(title, description)
        toggle = QCheckBox("On", row)
        toggle.setObjectName("settingToggle")
        toggle.setAccessibleName(title)
        cast(QHBoxLayout, row.layout()).addWidget(toggle)
        return row, toggle

    @staticmethod
    def _set_combo(combo: QComboBox, value: str) -> None:
        combo.setCurrentIndex(max(0, combo.findData(value)))
