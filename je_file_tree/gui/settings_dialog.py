"""Options → Settings: every setting in one searchable window, driven by the same actions as the menus."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from je_file_tree.gui import settings_file
from je_file_tree.gui.chart_palette import COLOUR_BLIND, palette_controller
from je_file_tree.gui.i18n import LANGUAGES, current_language, tr
from je_file_tree.gui.text_scale import DEFAULT_TEXT_SIZE, TEXT_SIZES, text_percent
from je_file_tree.gui.themes import THEMES, theme_controller
from je_file_tree.gui.window_fit import fit_window

if TYPE_CHECKING:
    from je_file_tree.gui.main_window import MainWindow

# (title, checkable actions, actions that open a window of their own)
_GROUPS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("settings_scanning", ("hidden", "gentle", "auto_cpu", "mft_scan"), ("exclusions", "scan_workers", "scan_presets")),
    ("settings_recording", ("capture_file_times", "capture_owners", "exact_allocation", "count_hard_links"), ()),
    ("settings_following", ("follow_changes", "check_updates"), ("background_monitor", "folder_budgets")),
    ("settings_cleaning", (), ("cleanup_policy", "history_settings")),
    ("settings_system", ("ask_admin",), ("shell_integration",)),
)
_FLAGS = {"include_hidden": "hidden", "gentle_scan": "gentle", "auto_cpu": "auto_cpu", "mft_scan": "mft_scan",
          "capture_file_times": "capture_file_times", "capture_owners": "capture_owners",
          "exact_allocation": "exact_allocation", "count_hard_links": "count_hard_links",
          "follow_changes": "follow_changes", "check_updates": "check_updates", "ask_admin_at_start": "ask_admin"}


class SettingsDialog(QDialog):
    """Changes apply at once, exactly as choosing the same entry in a menu does."""

    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window_ = window
        self.setWindowTitle(tr("settings_title"))
        fit_window(self, 640, 640)
        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText(tr("settings_search"))
        self.search.setAccessibleName(tr("settings_search"))
        self.search.textChanged.connect(self._filter)
        self.empty = QLabel(tr("settings_none"))
        self.empty.setProperty("role", "caption")
        self.rows: list[tuple[QWidget, QGroupBox, str]] = []
        self.groups: list[QGroupBox] = []
        self.boxes: dict[str, QCheckBox] = {}
        self.buttons: dict[str, QPushButton] = {}
        content = QWidget()
        self._column = QVBoxLayout(content)
        self._add_appearance()
        for title, flags, dialogs in _GROUPS:
            self._add_group(title, flags, dialogs)
        self._column.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(content)
        layout = QVBoxLayout(self)
        layout.addWidget(self.search)
        layout.addWidget(self.empty)
        layout.addWidget(scroll, 1)
        layout.addLayout(self._add_buttons())
        self._filter("")

    # --- rows ---------------------------------------------------------------

    def _group(self, title: str) -> tuple[QGroupBox, QVBoxLayout]:
        box = QGroupBox(tr(title))
        self._column.addWidget(box)
        self.groups.append(box)
        return box, QVBoxLayout(box)

    def _add_row(self, box: QGroupBox, row: QWidget, words: str) -> None:
        box.layout().addWidget(row)
        self.rows.append((row, box, f"{box.title()} {words}".casefold()))

    def _add_appearance(self) -> None:
        window = self.window_
        box, _layout = self._group("settings_appearance")
        self.language = self._combo(list(LANGUAGES.items()), current_language(), window.change_language)
        self.theme = self._combo([(theme, tr(f"theme_{theme}")) for theme in THEMES], theme_controller().choice,
                                 window.theme_menu.choose)
        sizes = [(percent, tr("text_size_default" if percent == DEFAULT_TEXT_SIZE else "text_size_percent",
                              percent=percent)) for percent in TEXT_SIZES]
        self.text_size = self._combo(sizes, text_percent(), window.text_size_menu.choose)
        units = [(unit, tr("unit_auto") if unit == settings_file.UNITS[0] else unit) for unit in settings_file.UNITS]
        self.unit = self._combo(units, window.size_unit, window.set_unit)
        for key, combo in (("menu_language", self.language), ("menu_theme", self.theme),
                           ("menu_text_size", self.text_size), ("menu_unit", self.unit)):
            self._add_combo(box, key, combo)
        self.colour_blind = QCheckBox(tr("theme_colour_blind"))
        self.colour_blind.setChecked(palette_controller().choice == COLOUR_BLIND)
        self.colour_blind.clicked.connect(window.theme_menu.colour_blind.trigger)
        self._add_row(box, self.colour_blind, tr("theme_colour_blind"))
        for action in (window.theme_menu.accent, window.theme_menu.platform_accent):
            button = QPushButton(action.text())
            button.setProperty("role", "list")
            button.clicked.connect(action.trigger)
            self._add_row(box, button, action.text())

    @staticmethod
    def _combo(options: Sequence[tuple[object, str]], chosen: object, apply) -> QComboBox:
        combo = QComboBox()
        for value, text in options:
            combo.addItem(text, value)
        combo.setCurrentIndex(max(0, combo.findData(chosen)))
        combo.activated.connect(lambda index: apply(combo.itemData(index)))
        return combo

    def _add_combo(self, box: QGroupBox, key: str, combo: QComboBox) -> None:
        caption = QLabel(tr(key))
        caption.setBuddy(combo)
        row = QWidget()
        line = QHBoxLayout(row)
        line.setContentsMargins(0, 0, 0, 0)
        line.addWidget(caption)
        line.addStretch(1)
        line.addWidget(combo)
        combo.setAccessibleName(_plain(tr(key)))
        options = " ".join(combo.itemText(index) for index in range(combo.count()))
        self._add_row(box, row, f"{_plain(tr(key))} {options}")

    def _add_group(self, title: str, flags: Sequence[str], dialogs: Sequence[str]) -> None:
        actions = self.window_._actions
        flags = [key for key in flags if actions[key].isVisible()]
        dialogs = [key for key in dialogs if actions[key].isVisible()]
        if not flags and not dialogs:
            return
        box, _layout = self._group(title)
        for key in flags:
            self._add_row(box, self._check_row(key, actions[key]), _words(actions[key]))
        for key in dialogs:
            button = QPushButton(actions[key].text())
            button.setProperty("role", "list")
            button.setToolTip(actions[key].toolTip())
            button.setEnabled(actions[key].isEnabled())
            button.clicked.connect(actions[key].trigger)
            self.buttons[key] = button
            self._add_row(box, button, _words(actions[key]))

    def _check_row(self, key: str, action: QAction) -> QWidget:
        box = QCheckBox(action.text())
        box.setChecked(action.isChecked())
        box.setEnabled(action.isEnabled())
        box.clicked.connect(action.trigger)
        box.setAccessibleDescription(action.toolTip())
        hint = QLabel(action.toolTip())
        hint.setWordWrap(True)
        hint.setProperty("role", "caption")
        hint.setIndent(box.iconSize().width() + 8)
        row = QWidget()
        column = QVBoxLayout(row)
        column.setContentsMargins(0, 0, 0, 4)
        column.setSpacing(1)
        column.addWidget(box)
        column.addWidget(hint)
        self.boxes[key] = box
        return row

    def _filter(self, text: str) -> None:
        words = text.casefold().split()
        shown = {box: 0 for box in self.groups}
        for row, box, searched in self.rows:
            fits = all(word in searched for word in words)
            row.setVisible(fits)
            shown[box] += fits
        for box, count in shown.items():
            box.setVisible(bool(count))
        self.empty.setVisible(not any(shown.values()))

    # --- the settings file ----------------------------------------------------

    def _add_buttons(self) -> QHBoxLayout:
        export, load = QPushButton(tr("settings_export")), QPushButton(tr("settings_import"))
        export.setToolTip(tr("settings_file_tip"))
        load.setToolTip(tr("settings_file_tip"))
        export.clicked.connect(self._export)
        load.clicked.connect(self._import)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        for button in (export, load):
            button.setAutoDefault(False)
        row = QHBoxLayout()
        row.addWidget(export)
        row.addWidget(load)
        row.addWidget(close, 1)
        return row

    def _current(self) -> dict[str, settings_file.Value]:
        return settings_file.current(self.window_.settings, current_language())

    def _export(self) -> None:
        target, _ = QFileDialog.getSaveFileName(self, tr("settings_export"), "file-tree-settings.json",
                                                tr("json_filter"))
        if not target:
            return
        try:
            settings_file.write(target, self._current())
        except OSError as error:
            QMessageBox.warning(self, tr("settings_export"), tr("export_failed", reason=str(error)))

    def _import(self) -> None:
        file, _ = QFileDialog.getOpenFileName(self, tr("settings_import"), "", tr("json_filter"))
        if not file:
            return
        try:
            changed = settings_file.changes(self._current(), settings_file.read(file))
        except (OSError, ValueError, RecursionError):
            QMessageBox.warning(self, tr("settings_import"), tr("settings_invalid"))
            return
        if not changed:
            QMessageBox.information(self, tr("settings_import"), tr("settings_same"))
            return
        question = QMessageBox(QMessageBox.Icon.Question, tr("settings_import"),
                               tr("settings_confirm", count=len(changed)),
                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self)
        question.setTextFormat(Qt.TextFormat.PlainText)
        question.setDefaultButton(QMessageBox.StandardButton.No)
        question.setDetailedText("\n".join(f"{key}: {value}" for key, value in changed.items()))
        if question.exec() == QMessageBox.StandardButton.Yes:
            apply_settings(self.window_, changed)
            self.accept()  # the texts, sizes and boxes on screen belong to the settings before


def apply_settings(window: MainWindow, values: dict[str, settings_file.Value]) -> None:
    """Use validated settings now and remember them, as choosing each in its menu would."""
    for key, value in values.items():
        window.settings.setValue(key, value)
        if key in _FLAGS:
            window._actions[_FLAGS[key]].setChecked(bool(value))
    if "scan_workers" in values:
        window.set_workers(int(values["scan_workers"]))
    if "exclusions" in values:
        window.set_exclusions(list(values["exclusions"]))
    if "unit" in values:
        window.set_unit(str(values["unit"]))
    if "theme" in values:
        window.theme_menu.choose(str(values["theme"]))
    if "accent" in values:
        window.theme_menu.choose_accent(str(values["accent"]))
    if "chart_palette" in values:
        window.theme_menu.choose_palette(str(values["chart_palette"]))
    if "text_size" in values:
        window.text_size_menu.choose(int(values["text_size"]))
    if "language" in values:
        window.change_language(str(values["language"]))


def _plain(text: str) -> str:
    return text.replace("&", "")


def _words(action: QAction) -> str:
    return f"{_plain(action.text())} {action.toolTip()}"
