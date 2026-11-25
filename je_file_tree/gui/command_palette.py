"""Ctrl+K: type to find any menu command and run it; and the window that edits their shortcuts."""

from __future__ import annotations

from collections.abc import Iterator

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QAction, QKeyEvent, QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMenuBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from je_file_tree.gui.i18n import tr
from je_file_tree.gui.shortcuts import FIXED, WindowShortcuts
from je_file_tree.gui.text_scale import text_scaled
from je_file_tree.gui.window_fit import fit_window

_SEPARATOR = " › "


def plain(text: str) -> str:
    """A menu text without its access key."""
    return text.replace("&&", "\0").replace("&", "").replace("\0", "&")


def commands(bar: QMenuBar) -> Iterator[tuple[str, QAction]]:
    """Every visible command of the menus with the way to it, in menu order."""
    stack: list[tuple[str, list[QAction]]] = [("", list(reversed(bar.actions())))]
    while stack:
        above, actions = stack[-1]
        if not actions:
            stack.pop()
            continue
        action = actions.pop()
        menu = action.menu()
        if action.isSeparator() or not action.isVisible():
            continue
        path = above + plain(action.text())
        if isinstance(menu, QMenu):
            stack.append((path + _SEPARATOR, list(reversed(menu.actions()))))
        elif action.text():
            yield path, action


class CommandPalette(QDialog):
    """A list of commands narrowed by typing; Enter or a double-click runs the chosen one after closing."""

    def __init__(self, bar: QMenuBar, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("palette_title"))
        fit_window(self, 620, 420)
        self.chosen: QAction | None = None
        self._commands = list(commands(bar))
        self.box = QLineEdit()
        self.box.setPlaceholderText(tr("palette_hint"))
        self.box.setAccessibleName(tr("palette_title"))
        self.box.setClearButtonEnabled(True)
        self.box.textChanged.connect(self._filter)
        self.box.returnPressed.connect(self._run)
        self.box.installEventFilter(self)
        self.list = QListWidget()
        self.list.setAccessibleName(tr("palette_title"))
        self.list.itemActivated.connect(lambda _item: self._run())
        layout = QVBoxLayout(self)
        layout.addWidget(self.box)
        layout.addWidget(self.list, 1)
        self._filter("")

    def _filter(self, text: str) -> None:
        words = text.casefold().split()
        self.list.clear()
        for path, action in self._commands:
            if not all(word in f"{path} {action.toolTip()}".casefold() for word in words):
                continue
            mark = "✓ " if action.isCheckable() and action.isChecked() else ""
            keys = action.shortcut().toString(QKeySequence.SequenceFormat.NativeText)
            item = QListWidgetItem(f"{mark}{path}" + (f"   ({keys})" if keys else ""))
            item.setToolTip(action.toolTip())
            item.setData(Qt.ItemDataRole.UserRole, action)
            if not action.isEnabled():
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.list.addItem(item)
        first = next((row for row in range(self.list.count())
                      if self.list.item(row).flags() & Qt.ItemFlag.ItemIsEnabled), -1)
        self.list.setCurrentRow(first)

    def _run(self) -> None:
        item = self.list.currentItem()
        if item is not None and item.flags() & Qt.ItemFlag.ItemIsEnabled:
            self.chosen = item.data(Qt.ItemDataRole.UserRole)
            self.accept()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802 - Qt's name
        """Qt: arrow and page keys move through the list while typing."""
        keys = (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown)
        if isinstance(event, QKeyEvent) and event.type() == QEvent.Type.KeyPress and event.key() in keys:
            self.list.keyPressEvent(event)
            return True
        return super().eventFilter(watched, event)


class ShortcutsDialog(QDialog):
    """Every command of the menus with its shortcut; OK is refused while two share one."""

    def __init__(self, shortcuts: WindowShortcuts, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("action_shortcuts"))
        fit_window(self, 640, 560)
        self.shortcuts = shortcuts
        self.keys = [key for key, action in shortcuts.actions.items()
                     if key not in FIXED and action.isVisible() and action.text()]
        hint = QLabel(tr("shortcuts_hint"))
        hint.setWordWrap(True)
        self.table = QTableWidget(len(self.keys), 2)
        self.table.setHorizontalHeaderLabels([tr("shortcuts_command"), tr("shortcuts_keys")])
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, text_scaled(200))
        self.edits: dict[str, QKeySequenceEdit] = {}
        for row, key in enumerate(self.keys):
            self._add_row(row, key)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.reset = QPushButton(tr("shortcuts_reset"))
        self.reset.setAutoDefault(False)
        self.reset.clicked.connect(self._reset)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.addButton(self.reset, QDialogButtonBox.ButtonRole.ResetRole)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(hint)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.status)
        layout.addWidget(self.buttons)

    def _add_row(self, row: int, key: str) -> None:
        name = plain(self.shortcuts.actions[key].text())
        item = QTableWidgetItem(name)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item.setToolTip(self.shortcuts.actions[key].toolTip())
        self.table.setItem(row, 0, item)
        edit = QKeySequenceEdit(QKeySequence(self.shortcuts.current(key)))
        edit.setMaximumSequenceLength(1)
        edit.setClearButtonEnabled(True)
        edit.setAccessibleName(name)
        edit.keySequenceChanged.connect(lambda _sequence: self.status.clear())
        self.table.setCellWidget(row, 1, edit)
        self.edits[key] = edit

    def shown(self) -> dict[str, str]:
        """The shortcuts in the table, as portable text."""
        return {key: edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
                for key, edit in self.edits.items()}

    def _reset(self) -> None:
        for key, edit in self.edits.items():
            edit.setKeySequence(QKeySequence(self.shortcuts.default(key)))

    def accept(self) -> None:
        """Use the shortcuts, or say which command's cannot be used and go to it."""
        shown = self.shown()
        refused = self.shortcuts.conflicts(shown)
        if refused:
            names = ", ".join(plain(self.shortcuts.actions[key].text()) for key in refused)
            self.status.setText(tr("shortcuts_conflict", names=names))
            self.edits[refused[0]].setFocus()
            return
        self.shortcuts.choose(shown)
        super().accept()
