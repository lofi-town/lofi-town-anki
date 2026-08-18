from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from aqt.qt import (
    QButtonGroup,
    QCheckBox,
    QColor,
    QColorDialog,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    Qt,
    QVBoxLayout,
    QWidget,
)

from .configuration import DEFAULT_CONFIG, PALETTES, normalize_config, theme_tokens


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
        self._draft = normalize_config(config)
        self._dark_mode = dark_mode
        self._save = save
        self._palette_buttons: dict[str, QPushButton] = {}

        self.setObjectName("lofiTownSettings")
        self.setWindowTitle("Lofi Town Theme")
        self.setMinimumSize(820, 610)
        self.resize(900, 650)

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
        title = QLabel("COZY STUDY", panel)
        title.setObjectName("previewEyebrow")
        moon = QLabel("♪", panel)
        moon.setObjectName("previewMoon")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(moon)
        layout.addLayout(header)

        scene = QFrame(panel)
        scene.setObjectName("windowScene")
        scene_layout = QVBoxLayout(scene)
        scene_layout.setContentsMargins(18, 16, 18, 18)
        scene_layout.setSpacing(10)

        window_header = QHBoxLayout()
        room = QLabel("today's decks", scene)
        room.setObjectName("sceneTitle")
        count = QLabel("12 due", scene)
        count.setObjectName("sceneBadge")
        window_header.addWidget(room)
        window_header.addStretch(1)
        window_header.addWidget(count)
        scene_layout.addLayout(window_header)

        for name, counts, tone in (
            ("Japanese", "6", "accent"),
            ("Biology", "4", "leaf"),
            ("Art history", "2", "blue"),
        ):
            row = QFrame(scene)
            row.setObjectName("previewDeck")
            row.setProperty("tone", tone)
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
        layout.addWidget(scene, 1)

        note = QLabel(
            "Original cozy styling built for Anki. "
            "Card templates stay untouched by default.",
            panel,
        )
        note.setObjectName("previewNote")
        note.setWordWrap(True)
        layout.addWidget(note)
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

        eyebrow = QLabel("LOFI TOWN FOR ANKI", content)
        eyebrow.setObjectName("eyebrow")
        title = QLabel("A calmer place to study.", content)
        title.setObjectName("title")
        title.setWordWrap(True)
        subtitle = QLabel(
            "Use Lofi Town's cozy palette, tune the spacing, and keep your cards "
            "exactly as their authors designed them.",
            content,
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        status = QLabel(content)
        status.setObjectName("compatibilityBadge")
        if ankihub_installed:
            status.setText("✓ AnkiHub detected, safe mode is active")
        else:
            status.setText("✓ AnkiHub-safe presentation hooks")
        layout.addWidget(status, 0, Qt.AlignmentFlag.AlignLeft)

        self._enabled = QCheckBox("Use the cozy theme", content)
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
            "Use one color for buttons, focus rings, and the active deck.",
            content,
        )
        self._custom_accent_enabled = QCheckBox("Custom", custom_row)
        self._accent_button = QPushButton("Choose color", custom_row)
        custom_layout = custom_row.layout()
        if custom_layout is None:
            raise RuntimeError("Custom accent row has no layout.")
        custom_layout.addWidget(self._custom_accent_enabled)
        custom_layout.addWidget(self._accent_button)
        layout.addWidget(custom_row)

        layout.addWidget(self._section_label("Appearance", content))
        self._color_mode = QComboBox(content)
        self._color_mode.addItem("Cozy light", "light")
        self._color_mode.addItem("Follow Anki", "follow_anki")
        self._color_mode.addItem("Cozy dark", "dark")
        layout.addWidget(
            self._row_with_control(
                "Color mode",
                "Use the game's light brown style or follow Anki.",
                self._color_mode,
                content,
            )
        )

        self._density = QComboBox(content)
        self._density.addItem("Cozy", "cozy")
        self._density.addItem("Compact", "compact")
        layout.addWidget(
            self._row_with_control(
                "Deck spacing",
                "Choose relaxed or information-dense deck rows.",
                self._density,
                content,
            )
        )

        self._motion = QComboBox(content)
        self._motion.addItem("Follow system", "system")
        self._motion.addItem("Full", "full")
        self._motion.addItem("Reduced", "reduced")
        layout.addWidget(
            self._row_with_control(
                "Motion",
                "Control the gentle entrance and press effects.",
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
                "Scale theme chrome without changing card content.",
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
                "Tune cards from tidy to extra soft.",
                self._corner_radius,
                content,
            )
        )

        layout.addWidget(self._section_label("Details", content))
        self._texture = QCheckBox("Subtle paper texture", content)
        self._native_window = QCheckBox("Match the main window frame", content)
        self._review_backdrop = QCheckBox(
            "Frame review cards with a cozy backdrop", content
        )
        self._review_backdrop.setToolTip(
            "This changes the space around a card. It does not edit the card template."
        )
        layout.addWidget(self._texture)
        layout.addWidget(self._native_window)
        layout.addWidget(self._review_backdrop)
        layout.addStretch(1)

        scroll.setWidget(content)
        shell_layout.addWidget(scroll, 1)

        footer = QFrame(shell)
        footer.setObjectName("footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(18, 13, 18, 16)
        reset = QPushButton("Restore defaults", footer)
        reset.setObjectName("resetButton")
        cancel = QPushButton("Cancel", footer)
        cancel.setObjectName("cancelButton")
        save = QPushButton("Save changes", footer)
        save.setObjectName("saveButton")
        save.setDefault(True)
        reset.clicked.connect(self._restore_defaults)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self._save_and_close)
        footer_layout.addWidget(reset)
        footer_layout.addStretch(1)
        footer_layout.addWidget(cancel)
        footer_layout.addWidget(save)
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
        row_layout = row.layout()
        if row_layout is None:
            raise RuntimeError("Setting row has no layout.")
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
        for combo in (self._color_mode, self._density, self._motion):
            combo.currentIndexChanged.connect(self._on_control_change)
        for slider in (self._font_scale, self._corner_radius):
            slider.valueChanged.connect(self._on_control_change)
        for checkbox in (self._texture, self._native_window, self._review_backdrop):
            checkbox.toggled.connect(self._on_control_change)

    def _load_controls(self, config: dict[str, Any]) -> None:
        self._enabled.setChecked(config["enabled"])
        self._palette_buttons[config["palette"]].setChecked(True)
        self._custom_accent_enabled.setChecked(config["custom_accent_enabled"])
        self._set_combo(self._color_mode, config["color_mode"])
        self._set_combo(self._density, config["density"])
        self._set_combo(self._motion, config["motion"])
        self._font_scale.setValue(round(config["font_scale"] * 100))
        self._corner_radius.setValue(config["corner_radius"])
        self._texture.setChecked(config["texture"])
        self._native_window.setChecked(config["native_window"])
        self._review_backdrop.setChecked(config["review_backdrop"])

    def _set_combo(self, combo: QComboBox, value: str) -> None:
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
        )
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
        radius = self._draft["corner_radius"]
        self._accent_button.setStyleSheet(
            f"background:{tokens['accent']}; color:#FFFAF0; border:0; "
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
        self._preview_panel.setEnabled(self._draft["enabled"])


def _dialog_stylesheet(tokens: dict[str, str], radius: int, density: str) -> str:
    row_padding = 7 if density == "compact" else 11
    return f"""
QDialog#lofiTownSettings {{
    background: {tokens["bg"]};
    color: {tokens["text"]};
    font-family: "Bricolage Grotesque", "Avenir Next", "Segoe UI", sans-serif;
}}
QFrame#previewPanel, QFrame#controlsShell {{
    background: {tokens["surface"]};
    border: 1px solid {tokens["border"]};
    border-radius: {radius + 7}px;
}}
QFrame#previewPanel {{
    background: {tokens["raised"]};
}}
QLabel#previewEyebrow, QLabel#eyebrow, QLabel#sectionLabel {{
    color: {tokens["accent"]};
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.5px;
}}
QLabel#previewMoon {{
    color: {tokens["accent"]};
    font-size: 28px;
    font-weight: 800;
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
    color: #FFFAF0;
    border: 0;
    border-bottom: 4px solid {tokens["accent_drop"]};
    border-radius: {max(10, radius - 2)}px;
    font-size: 14px;
    font-weight: 800;
    padding: 13px;
}}
QLabel#previewNote, QLabel#subtitle, QLabel#settingDescription {{
    color: {tokens["text_soft"]};
}}
QLabel#previewNote {{ font-size: 12px; }}
QLabel#title {{
    color: {tokens["text"]};
    font-size: 25px;
    font-weight: 850;
}}
QLabel#subtitle {{ font-size: 13px; }}
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
    color: #FFFAF0;
    border: 0;
    border-bottom: 4px solid {tokens["accent_drop"]};
}}
"""
