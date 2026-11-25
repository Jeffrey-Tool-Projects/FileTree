"""View → Text size: one saved size for every text in the application, applied without a restart."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QSettings, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import QApplication, QHeaderView, QMenu, QTableView

from je_file_tree.gui.i18n import current_language, tr
from je_file_tree.gui.locale_font import apply_language_font
from je_file_tree.gui.text_scale import (
    DEFAULT_TEXT_SIZE,
    TEXT_SIZES,
    fit_rows,
    set_text_percent,
    text_percent,
    text_scale,
)

TEXT_SIZE_KEY = "text_size"
_ADJUSTABLE = (QHeaderView.ResizeMode.Interactive, QHeaderView.ResizeMode.Fixed)


def saved_text_size(settings: QSettings) -> int:
    """The remembered text size; a missing, unreadable or no longer offered one means the default."""
    value = str(settings.value(TEXT_SIZE_KEY, DEFAULT_TEXT_SIZE))
    percent = int(value) if value.isascii() and value.isdigit() else DEFAULT_TEXT_SIZE
    return percent if percent in TEXT_SIZES else DEFAULT_TEXT_SIZE


def neighbour(percent: int, step: int) -> int:
    """The offered size ``step`` places from ``percent``, stopping at the smallest and the largest."""
    return TEXT_SIZES[max(0, min(len(TEXT_SIZES) - 1, TEXT_SIZES.index(percent) + step))]


class TextSizeController(QObject):
    """Apply one text size application-wide; ``changed`` follows once every open widget has its new font."""

    changed = Signal(int)

    def apply(self, percent: int) -> None:
        """Show every text at ``percent`` of the system's size; scan data and selections are untouched."""
        before = text_scale()
        set_text_percent(percent)
        if text_scale() == before:
            return
        apply_language_font(current_language())
        # Qt posts the new font to the windows; everything below measures text, so deliver it first.
        QCoreApplication.sendPostedEvents(None, QEvent.Type.ApplicationFontChange)
        _fit_open_lists(text_scale() / before)
        self.changed.emit(text_percent())


def _fit_open_lists(ratio: float) -> None:
    """Keep the columns and rows of lists that are already open in proportion to their text."""
    for widget in QApplication.allWidgets():
        if isinstance(widget, QTableView):
            fit_rows(widget)
        if isinstance(widget, QHeaderView) and widget.orientation() == Qt.Orientation.Horizontal:
            _scale_columns(widget, ratio)


def _scale_columns(header: QHeaderView, ratio: float) -> None:
    stretched = header.logicalIndex(header.count() - 1) if header.stretchLastSection() else -1
    for section in range(header.count()):
        if section == stretched or header.sectionResizeMode(section) not in _ADJUSTABLE:
            continue
        hidden = header.isSectionHidden(section)
        if hidden:  # Qt tells a hidden column's width only while it is shown
            header.showSection(section)
        header.resizeSection(section, round(header.sectionSize(section) * ratio))
        if hidden:
            header.hideSection(section)


def text_size_controller() -> TextSizeController:
    """Return the single controller attached to this QApplication."""
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        raise RuntimeError("a QApplication is required")
    controller = getattr(app, "_filetree_text_size_controller", None)
    if controller is None:
        controller = TextSizeController(app)
        app._filetree_text_size_controller = controller
    return controller


class TextSizeMenu(QMenu):
    """A translated View → Text size submenu: larger, smaller, reset and every offered size."""

    def __init__(self, parent: QMenu, settings: QSettings) -> None:
        super().__init__(parent)
        parent.addMenu(self)
        self.settings = settings
        self.controller = text_size_controller()
        # Ctrl+= is the same key as Ctrl++ without Shift on most keyboards.
        self.larger = self._command([QKeySequence("Ctrl++"), QKeySequence("Ctrl+=")], lambda: self.step(1))
        self.smaller = self._command([QKeySequence("Ctrl+-")], lambda: self.step(-1))
        self.reset = self._command([QKeySequence("Ctrl+0")], lambda: self.choose(DEFAULT_TEXT_SIZE))
        self.addSeparator()
        group = QActionGroup(self)
        self.actions_by_size: dict[int, QAction] = {}
        for percent in TEXT_SIZES:
            action = self.addAction("")
            action.setCheckable(True)
            group.addAction(action)
            action.triggered.connect(lambda _checked=False, chosen=percent: self.choose(chosen))
            self.actions_by_size[percent] = action
        self.controller.changed.connect(self._mark)
        self._mark(text_percent())
        self.retranslate()

    def _command(self, shortcuts: list[QKeySequence], run: Callable[[], None]) -> QAction:
        action = self.addAction("")
        action.setShortcuts(shortcuts)
        action.triggered.connect(lambda _checked=False: run())
        return action

    def retranslate(self) -> None:
        """Refresh the submenu labels in the current language without changing the choice."""
        self.setTitle(tr("menu_text_size"))
        self.larger.setText(tr("text_size_larger"))
        self.smaller.setText(tr("text_size_smaller"))
        self.reset.setText(tr("text_size_reset"))
        for percent, action in self.actions_by_size.items():
            key = "text_size_default" if percent == DEFAULT_TEXT_SIZE else "text_size_percent"
            action.setText(tr(key, percent=percent))

    def choose(self, percent: int) -> None:
        """Use ``percent`` everywhere and remember it."""
        self.settings.setValue(TEXT_SIZE_KEY, percent)
        self.controller.apply(percent)

    def step(self, places: int) -> None:
        """Move ``places`` sizes up (or down, when negative)."""
        self.choose(neighbour(text_percent(), places))

    def _mark(self, percent: int) -> None:
        self.actions_by_size[percent].setChecked(True)
        self.larger.setEnabled(percent != TEXT_SIZES[-1])
        self.smaller.setEnabled(percent != TEXT_SIZES[0])
