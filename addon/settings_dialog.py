from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

from aqt.qt import (
    QButtonGroup,
    QCheckBox,
    QColor,
    QColorDialog,
    QComboBox,
    QDialog,
    QFont,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSize,
    QSlider,
    Qt,
    QVBoxLayout,
    QWidget,
)

from .configuration import DEFAULT_CONFIG, PALETTES, normalize_config, theme_tokens
from .fonts import load_cozy_font_family
from .mascot import CozyBunnyLabel
from .study_settings import StudyCompanionSettings, StudyCompanionValues


class ThemeSettingsDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        config: dict[str, Any],
        dark_mode: bool,
        ankihub_installed: bool,
        save: Callable[[dict[str, Any]], None],
    ) -> None:
        super().__init__(parent)
        self._saved = normalize_config(config)
        self._draft = deepcopy(self._saved)
        self._dark_mode = dark_mode
        self._save = save
        self._palette_buttons: dict[str, QPushButton] = {}
        self._resources_path = Path(__file__).resolve().parent / "resources"
        self._loading_controls = False

        self.setObjectName("lofiTownSettings")
        self.setWindowTitle("Lofi Town Settings")
        self.setMinimumSize(820, 610)
        self.resize(900, 650)
        if font_family := load_cozy_font_family():
            self.setFont(QFont(font_family))

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(18)
        root.addWidget(self._build_preview(), 5)
        root.addWidget(self._build_controls(ankihub_installed), 6)
        self._load_controls(self._draft)
        self._connect_controls()
        self._update_preview()

    def _build_preview(self) -> QFrame:
        panel = QFrame(self)
        panel.setObjectName("previewPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("PREVIEW", panel)
        title.setObjectName("previewEyebrow")
        self._preview_mascot = CozyBunnyLabel(
            self._resources_path,
            QSize(68, 80),
            panel,
        )
        self._preview_mascot.set_motion(self._draft["motion"])
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self._preview_mascot)
        layout.addLayout(header)

        scene = QFrame(panel)
        scene.setObjectName("windowScene")
        scene_layout = QVBoxLayout(scene)
        scene_layout.setContentsMargins(18, 16, 18, 18)
        scene_layout.setSpacing(10)

        window_header = QHBoxLayout()
        room = QLabel("Decks", scene)
        room.setObjectName("sceneTitle")
        count = QLabel("12 due", scene)
        count.setObjectName("sceneBadge")
        window_header.addWidget(room)
        window_header.addStretch(1)
        window_header.addWidget(count)
        scene_layout.addLayout(window_header)

        for name, counts in (
            ("Default", "6"),
            ("Languages", "4"),
            ("Science", "2"),
        ):
            row = QFrame(scene)
            row.setObjectName("previewDeck")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(13, 10, 13, 10)
            name_label = QLabel(name, row)
            name_label.setObjectName("previewDeckName")
            count_label = QLabel(counts, row)
            count_label.setObjectName("previewDeckCount")
            row_layout.addWidget(name_label)
            row_layout.addStretch(1)
            row_layout.addWidget(count_label)
            scene_layout.addWidget(row)

        study = QPushButton("Start review", scene)
        study.setObjectName("previewStudy")
        study.setEnabled(False)
        scene_layout.addWidget(study)

        self._preview_session = QFrame(scene)
        self._preview_session.setObjectName("previewSession")
        session_layout = QHBoxLayout(self._preview_session)
        session_layout.setContentsMargins(11, 8, 11, 8)
        session_layout.setSpacing(8)
        self._preview_session_brand = QLabel("LOFI.TOWN FOCUS", self._preview_session)
        self._preview_session_brand.setObjectName("previewSessionBrand")
        self._preview_session_facts = QLabel(
            "7 answers · 12 remaining", self._preview_session
        )
        self._preview_session_facts.setObjectName("previewSessionFacts")
        self._preview_session_time = QLabel("25:00 focus", self._preview_session)
        self._preview_session_time.setObjectName("previewSessionTime")
        session_layout.addWidget(self._preview_session_brand)
        session_layout.addWidget(self._preview_session_facts)
        session_layout.addStretch(1)
        session_layout.addWidget(self._preview_session_time)
        scene_layout.addWidget(self._preview_session)
        layout.addWidget(scene, 1)

        self._preview_panel = panel
        return panel

    def _build_controls(self, ankihub_installed: bool) -> QFrame:
        shell = QFrame(self)
        shell.setObjectName("controlsShell")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        scroll = QScrollArea(shell)
        scroll.setObjectName("settingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget(scroll)
        content.setObjectName("settingsContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 22, 24, 16)
        layout.setSpacing(16)

        title = QLabel("Study room", content)
        title.setObjectName("title")
        layout.addWidget(title)
        if ankihub_installed:
            status = QLabel("AnkiHub views are excluded from theming.", content)
            status.setObjectName("compatibilityBadge")
            layout.addWidget(status, 0, Qt.AlignmentFlag.AlignLeft)

        self._enabled = QCheckBox("Study room enabled", content)
        self._enabled.setObjectName("masterToggle")
        layout.addWidget(self._enabled)

        layout.addWidget(self._section_label("Accent color", content))
        palette_row = QHBoxLayout()
        palette_row.setSpacing(8)
        self._palette_group = QButtonGroup(self)
        self._palette_group.setExclusive(True)
        for key, palette in PALETTES.items():
            button = QPushButton(palette["label"], content)
            button.setCheckable(True)
            button.setProperty("palette", key)
            button.setAccessibleName(f"{palette['label']} palette")
            self._palette_group.addButton(button)
            self._palette_buttons[key] = button
            palette_row.addWidget(button)
        layout.addLayout(palette_row)

        custom_row = self._setting_row(
            "Custom accent",
            "Overrides the selected accent.",
            content,
        )
        self._custom_accent_enabled = QCheckBox("Custom", custom_row)
        self._accent_button = QPushButton("Choose…", custom_row)
        custom_layout = cast(QHBoxLayout, custom_row.layout())
        custom_layout.addWidget(self._custom_accent_enabled)
        custom_layout.addWidget(self._accent_button)
        layout.addWidget(custom_row)

        self._study_settings = StudyCompanionSettings(content)
        layout.addWidget(self._study_settings)

        layout.addWidget(self._section_label("Appearance", content))
        self._color_mode = QComboBox(content)
        self._color_mode.addItem("Light", "light")
        self._color_mode.addItem("Follow Anki", "follow_anki")
        self._color_mode.addItem("Dark", "dark")
        layout.addWidget(
            self._row_with_control(
                "Color mode",
                "Light, dark, or match Anki.",
                self._color_mode,
                content,
            )
        )

        self._density = QComboBox(content)
        self._density.addItem("Comfortable", "cozy")
        self._density.addItem("Compact", "compact")
        layout.addWidget(
            self._row_with_control(
                "Deck spacing",
                "Adjust deck row height.",
                self._density,
                content,
            )
        )

        self._motion = QComboBox(content)
        self._motion.addItem("System", "system")
        self._motion.addItem("On", "full")
        self._motion.addItem("Reduced", "reduced")
        layout.addWidget(
            self._row_with_control(
                "Motion",
                "Use system preference or override it.",
                self._motion,
                content,
            )
        )

        self._font_scale = QSlider(Qt.Orientation.Horizontal, content)
        self._font_scale.setRange(90, 120)
        self._font_scale.setSingleStep(5)
        self._font_scale.setTickInterval(5)
        layout.addWidget(
            self._row_with_control(
                "Text size",
                "Does not affect card content.",
                self._font_scale,
                content,
            )
        )

        self._corner_radius = QSlider(Qt.Orientation.Horizontal, content)
        self._corner_radius.setRange(8, 24)
        self._corner_radius.setSingleStep(2)
        layout.addWidget(
            self._row_with_control(
                "Roundness",
                "Adjust panel and control corners.",
                self._corner_radius,
                content,
            )
        )

        layout.addWidget(self._section_label("Details", content))
        self._texture = QCheckBox("Paper texture", content)
        self._native_window = QCheckBox("Theme native window", content)
        self._review_backdrop = QCheckBox("Review backdrop", content)
        self._low_resource = QCheckBox("Low-resource mode", content)
        self._review_backdrop.setToolTip(
            "Styles only the area around the card."
        )
        layout.addWidget(self._texture)
        layout.addWidget(self._native_window)
        layout.addWidget(self._review_backdrop)
        layout.addWidget(self._low_resource)
        layout.addStretch(1)

        scroll.setWidget(content)
        shell_layout.addWidget(scroll, 1)

        footer = QFrame(shell)
        footer.setObjectName("footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(18, 13, 18, 16)
        reset = QPushButton("Defaults", footer)
        reset.setObjectName("resetButton")
        cancel = QPushButton("Cancel", footer)
        cancel.setObjectName("cancelButton")
        self._footer_status = QLabel("No unsaved changes", footer)
        self._footer_status.setObjectName("footerStatus")
        self._save_button = QPushButton("Save", footer)
        self._save_button.setObjectName("saveButton")
        self._save_button.setDefault(True)
        reset.clicked.connect(self._restore_defaults)
        cancel.clicked.connect(self.reject)
        self._save_button.clicked.connect(self._save_and_close)
        footer_layout.addWidget(reset)
        footer_layout.addWidget(self._footer_status)
        footer_layout.addStretch(1)
        footer_layout.addWidget(cancel)
        footer_layout.addWidget(self._save_button)
        shell_layout.addWidget(footer)
        return shell

    def _section_label(self, text: str, parent: QWidget) -> QLabel:
        label = QLabel(text.upper(), parent)
        label.setObjectName("sectionLabel")
        return label

    def _setting_row(self, title: str, description: str, parent: QWidget) -> QFrame:
        row = QFrame(parent)
        row.setObjectName("settingRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(13, 11, 13, 11)
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
        parent: QWidget,
    ) -> QFrame:
        row = self._setting_row(title, description, parent)
        control.setMinimumWidth(128)
        row_layout = cast(QHBoxLayout, row.layout())
        row_layout.addWidget(control)
        return row

    def _connect_controls(self) -> None:
        self._enabled.toggled.connect(self._on_control_change)
        for key, button in self._palette_buttons.items():
            button.clicked.connect(
                lambda _checked=False, value=key: self._select_palette(value)
            )
        self._custom_accent_enabled.toggled.connect(self._on_control_change)
        self._accent_button.clicked.connect(self._choose_accent)
        self._study_settings.changed.connect(self._on_control_change)
        for combo in (self._color_mode, self._density, self._motion):
            combo.currentIndexChanged.connect(self._on_control_change)
        for slider in (self._font_scale, self._corner_radius):
            slider.valueChanged.connect(self._on_control_change)
        for checkbox in (
            self._texture,
            self._native_window,
            self._review_backdrop,
            self._low_resource,
        ):
            checkbox.toggled.connect(self._on_control_change)

    def _load_controls(self, config: dict[str, Any]) -> None:
        self._loading_controls = True
        try:
            self._enabled.setChecked(config["enabled"])
            self._palette_buttons[config["palette"]].setChecked(True)
            self._custom_accent_enabled.setChecked(config["custom_accent_enabled"])
            self._study_settings.load(config)
            self._set_combo(self._color_mode, config["color_mode"])
            self._set_combo(self._density, config["density"])
            self._set_combo(self._motion, config["motion"])
            self._font_scale.setValue(round(config["font_scale"] * 100))
            self._corner_radius.setValue(config["corner_radius"])
            self._texture.setChecked(config["texture"])
            self._native_window.setChecked(config["native_window"])
            self._review_backdrop.setChecked(config["review_backdrop"])
            self._low_resource.setChecked(config["low_resource"])
        finally:
            self._loading_controls = False

    def _set_combo(self, combo: QComboBox, value: Any) -> None:
        index = combo.findData(value)
        combo.setCurrentIndex(max(0, index))

    def _select_palette(self, palette: str) -> None:
        self._draft["palette"] = palette
        self._on_control_change()

    def _choose_accent(self) -> None:
        initial = QColor(self._draft["custom_accent"])
        color = QColorDialog.getColor(initial, self, "Choose an accent color")
        if not color.isValid():
            return
        self._draft["custom_accent"] = color.name().upper()
        self._custom_accent_enabled.setChecked(True)
        self._on_control_change()

    def _on_control_change(self, *_args: Any) -> None:
        if self._loading_controls:
            return
        checked_palette = next(
            (
                key
                for key, button in self._palette_buttons.items()
                if button.isChecked()
            ),
            self._draft["palette"],
        )
        self._draft.update(
            enabled=self._enabled.isChecked(),
            palette=checked_palette,
            color_mode=self._color_mode.currentData(),
            custom_accent_enabled=self._custom_accent_enabled.isChecked(),
            density=self._density.currentData(),
            font_scale=self._font_scale.value() / 100,
            corner_radius=self._corner_radius.value(),
            motion=self._motion.currentData(),
            texture=self._texture.isChecked(),
            native_window=self._native_window.isChecked(),
            review_backdrop=self._review_backdrop.isChecked(),
            low_resource=self._low_resource.isChecked(),
        )
        self._draft.update(self._study_settings.values().to_config())
        self._draft = normalize_config(self._draft)
        self._update_preview()

    def _restore_defaults(self) -> None:
        self._draft = deepcopy(DEFAULT_CONFIG)
        self._load_controls(self._draft)
        self._update_preview()

    def _save_and_close(self) -> None:
        self._on_control_change()
        self._save(self._draft)
        self.accept()

    def _update_preview(self) -> None:
        mode = self._draft["color_mode"]
        if mode == "follow_anki":
            mode = "dark" if self._dark_mode else "light"
        tokens = theme_tokens(self._draft, mode)
        self._preview_mascot.set_motion(self._draft["motion"])
        radius = self._draft["corner_radius"]
        self._accent_button.setStyleSheet(
            f"background:{tokens['accent']}; color:{tokens['accent_text']}; "
            "border:0; "
            "border-radius:10px; padding:7px 10px;"
        )
        for key, button in self._palette_buttons.items():
            accent = PALETTES[key]["accent"]
            selected = key == self._draft["palette"]
            border_width = "3px" if selected else "1px"
            background = tokens["accent_soft"] if selected else tokens["surface"]
            button.setStyleSheet(
                f"QPushButton {{ background:{background}; color:{tokens['text']}; "
                f"border:{border_width} solid {accent}; "
                "border-radius:10px; padding:9px 6px; font-weight:700; }"
            )
        self.setStyleSheet(_dialog_stylesheet(tokens, radius, self._draft["density"]))
        enabled = self._draft["enabled"]
        study = StudyCompanionValues.from_config(self._draft)
        session_enabled = enabled and study.session_hud
        self._preview_panel.setEnabled(enabled)
        self._preview_session.setVisible(session_enabled)
        self._preview_session_brand.setVisible(not study.hud_compact)
        facts = []
        if study.hud_show_answers:
            if study.session_target_answers:
                facts.append(f"7/{study.session_target_answers} answers")
            else:
                facts.append("7 answers")
        if study.hud_show_remaining:
            facts.append("12 remaining")
        self._preview_session_facts.setText(" · ".join(facts))
        self._preview_session_facts.setVisible(bool(facts))
        self._preview_session_time.setVisible(study.hud_show_timer)
        if study.focus_minutes:
            self._preview_session_time.setText(f"{study.focus_minutes}:00 focus")
        else:
            self._preview_session_time.setText("elapsed time")
        self._study_settings.set_available(enabled)
        self._texture.setEnabled(enabled and not self._draft["low_resource"])
        dirty = self._draft != self._saved
        self._footer_status.setText(
            "Unsaved changes" if dirty else "No unsaved changes"
        )
        self._save_button.setEnabled(dirty)


def _dialog_stylesheet(tokens: dict[str, str], radius: int, density: str) -> str:
    row_padding = 7 if density == "compact" else 11
    return f"""
QDialog#lofiTownSettings {{
    background: {tokens["bg"]};
    color: {tokens["text"]};
}}
QFrame#previewPanel, QFrame#controlsShell {{
    background: {tokens["surface"]};
    border: 1px solid {tokens["border"]};
    border-radius: {radius + 7}px;
}}
QFrame#previewPanel {{
    background: {tokens["raised"]};
}}
QLabel#previewEyebrow, QLabel#sectionLabel {{
    color: {tokens["accent"]};
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.5px;
}}
QFrame#windowScene {{
    background: {tokens["card"]};
    border: 1px solid {tokens["border"]};
    border-radius: {radius + 5}px;
}}
QLabel#sceneTitle {{
    color: {tokens["text"]};
    font-size: 18px;
    font-weight: 800;
}}
QLabel#sceneBadge {{
    background: {tokens["accent_soft"]};
    color: {tokens["accent"]};
    border-radius: 9px;
    font-size: 11px;
    font-weight: 800;
    padding: 4px 8px;
}}
QFrame#previewDeck {{
    background: {tokens["surface"]};
    border: 1px solid {tokens["border"]};
    border-radius: {max(8, radius - 4)}px;
}}
QLabel#previewDeckName {{ color: {tokens["text"]}; font-weight: 750; }}
QLabel#previewDeckCount {{
    background: {tokens["accent_soft"]};
    color: {tokens["accent"]};
    border-radius: 9px;
    font-weight: 800;
    padding: 3px 7px;
}}
QPushButton#previewStudy {{
    background: {tokens["accent"]};
    color: {tokens["accent_text"]};
    border: 0;
    border-bottom: 4px solid {tokens["accent_drop"]};
    border-radius: {max(10, radius - 2)}px;
    font-size: 14px;
    font-weight: 800;
    padding: 13px;
}}
QFrame#previewSession {{
    background: {tokens["surface"]};
    border: 1px solid {tokens["border"]};
    border-radius: {max(8, radius - 5)}px;
}}
QLabel#previewSessionBrand {{
    color: {tokens["accent"]};
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.8px;
}}
QLabel#previewSessionFacts {{
    color: {tokens["text_soft"]};
    font-size: 11px;
}}
QLabel#previewSessionTime {{
    color: {tokens["text"]};
    font-size: 11px;
    font-weight: 750;
}}
QLabel#settingDescription {{
    color: {tokens["text_soft"]};
}}
QLabel#title {{
    color: {tokens["text"]};
    font-size: 24px;
    font-weight: 800;
}}
QLabel#compatibilityBadge {{
    background: {tokens["accent_soft"]};
    color: {tokens["accent"]};
    border-radius: 11px;
    font-size: 12px;
    font-weight: 750;
    padding: 7px 10px;
}}
QScrollArea#settingsScroll, QWidget#settingsContent {{
    background: transparent;
    border: 0;
}}
QFrame#settingRow {{
    background: {tokens["card"]};
    border: 1px solid {tokens["border"]};
    border-radius: {max(10, radius - 3)}px;
}}
QWidget#settingCopy {{ background: transparent; }}
QFrame#settingRow {{ padding-top: {row_padding}px; padding-bottom: {row_padding}px; }}
QLabel#settingTitle {{ color: {tokens["text"]}; font-weight: 750; }}
QLabel#settingDescription {{ font-size: 11px; }}
QCheckBox {{ color: {tokens["text"]}; font-weight: 650; spacing: 8px; }}
QCheckBox::indicator {{
    background: {tokens["card"]};
    border: 2px solid {tokens["border"]};
    border-radius: 7px;
    height: 20px;
    width: 20px;
}}
QCheckBox::indicator:checked {{
    background: {tokens["accent"]};
    border-color: {tokens["accent"]};
}}
QCheckBox:disabled, QLabel:disabled {{ color: {tokens["text_muted"]}; }}
QCheckBox#masterToggle {{
    background: {tokens["hover"]};
    border: 1px solid {tokens["border"]};
    border-radius: {max(10, radius - 2)}px;
    color: {tokens["text"]};
    font-size: 14px;
    font-weight: 800;
    padding: 11px;
}}
QComboBox {{
    background: {tokens["surface"]};
    color: {tokens["text"]};
    border: 1px solid {tokens["border"]};
    border-radius: 10px;
    min-height: 30px;
    padding: 2px 9px;
}}
QComboBox QAbstractItemView {{
    background: {tokens["card"]};
    color: {tokens["text"]};
    selection-background-color: {tokens["accent_soft"]};
}}
QComboBox:disabled {{
    background: {tokens["secondary"]};
    color: {tokens["text_muted"]};
}}
QSlider::groove:horizontal {{
    background: {tokens["secondary"]};
    border-radius: 3px;
    height: 6px;
}}
QSlider::handle:horizontal {{
    background: {tokens["accent"]};
    border: 3px solid {tokens["card"]};
    border-radius: 10px;
    height: 17px;
    margin: -7px 0;
    width: 17px;
}}
QFrame#footer {{
    background: {tokens["card"]};
    border-top: 1px solid {tokens["border"]};
    border-bottom-left-radius: {radius + 7}px;
    border-bottom-right-radius: {radius + 7}px;
}}
QLabel#footerStatus {{
    color: {tokens["text_muted"]};
    font-size: 11px;
}}
QPushButton#resetButton, QPushButton#cancelButton, QPushButton#saveButton {{
    border-radius: 999px;
    font-weight: 750;
    padding: 9px 14px;
}}
QPushButton#resetButton, QPushButton#cancelButton {{
    background: {tokens["surface"]};
    color: {tokens["text_soft"]};
    border: 1px solid {tokens["border"]};
}}
QPushButton#saveButton {{
    background: {tokens["accent"]};
    color: {tokens["accent_text"]};
    border: 0;
    border-bottom: 4px solid {tokens["accent_drop"]};
}}
QPushButton#saveButton:disabled {{
    background: {tokens["secondary"]};
    color: {tokens["text_muted"]};
    border: 1px solid {tokens["border"]};
}}
"""
