"""Shortcuts the user chose for menu commands: validated, free of conflicts, shared by every tab."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from PySide6.QtCore import QKeyCombination, QObject, QSettings, Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication

SHORTCUTS_KEY = "shortcuts"
# Removing entries stays on the keys everyone knows, and the quit and stop keys cannot be lost by accident.
FIXED = frozenset({"trash", "permanent_delete", "stop", "quit"})
# Commands outside the menu table; their keys are taken.
TAKEN = ("Ctrl++", "Ctrl+=", "Ctrl+-", "Ctrl+0", "Ctrl+T", "Ctrl+W", "Ctrl+K", "Alt+Left", "Alt+Right",
         "Ctrl+C", "Ctrl+X", "Ctrl+V", "Ctrl+A", "Ctrl+Z", "Ctrl+Y", "Delete", "Shift+Delete", "Shift+Del", "Esc")
_MAX_TEXT = 20_000
_STRONG = (Qt.KeyboardModifier.ControlModifier, Qt.KeyboardModifier.AltModifier, Qt.KeyboardModifier.MetaModifier)


def usable(text: str) -> bool:
    """Whether ``text`` is one key with Ctrl, Alt or Meta (or a function key) that nothing else needs."""
    sequence = QKeySequence(text)
    if sequence.count() != 1:
        return False
    combination: QKeyCombination = sequence[0]
    key, modifiers = combination.key(), combination.keyboardModifiers()
    if key == Qt.Key.Key_unknown:
        return False
    function = Qt.Key.Key_F1 <= key <= Qt.Key.Key_F24
    strong = any(modifiers & modifier for modifier in _STRONG)
    return (function or strong) and not any(sequence == QKeySequence(taken) for taken in TAKEN)


def load(text: object) -> dict[str, str]:
    """Saved choices by command; anything unusable is left out, so a broken setting never blocks the window."""
    if not isinstance(text, str) or not text or len(text) > _MAX_TEXT:
        return {}
    try:
        value = json.loads(text)
    except (ValueError, RecursionError):
        return {}
    if not isinstance(value, dict):
        return {}
    chosen: dict[str, str] = {}
    used: set[str] = set()
    for key, sequence in value.items():
        if (key in FIXED or not isinstance(sequence, str) or (sequence and not usable(sequence))
                or (sequence and sequence in used)):
            continue
        used.add(sequence)
        chosen[key] = sequence
    return chosen


class ShortcutController(QObject):
    """The choices in use; ``changed`` follows so every tab applies them."""

    changed = Signal()

    def __init__(self, app: QApplication) -> None:
        super().__init__(app)
        self.chosen: dict[str, str] = {}

    def apply(self, chosen: Mapping[str, str]) -> None:
        """Use these choices (an empty text means no shortcut; a missing command keeps its default)."""
        if dict(chosen) != self.chosen:
            self.chosen = dict(chosen)
            self.changed.emit()


def shortcut_controller() -> ShortcutController:
    """Return the single controller attached to this QApplication."""
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        raise RuntimeError("a QApplication is required")
    controller = getattr(app, "_filetree_shortcut_controller", None)
    if controller is None:
        controller = ShortcutController(app)
        app._filetree_shortcut_controller = controller
    return controller


class WindowShortcuts(QObject):
    """One window's commands: their default shortcuts, with the user's choices applied over them."""

    def __init__(self, actions: Mapping[str, QAction], settings: QSettings, parent: QObject) -> None:
        super().__init__(parent)
        self.actions, self.settings = actions, settings
        self.defaults = {key: list(action.shortcuts()) for key, action in actions.items()}
        self.controller = shortcut_controller()
        self.controller.changed.connect(self.refresh)
        self.controller.apply(load(settings.value(SHORTCUTS_KEY, "")))
        self.refresh()

    def refresh(self) -> None:
        """Give every command the shortcut in use; a default another command was given is dropped."""
        chosen = self.controller.chosen
        taken = [QKeySequence(text) for text in chosen.values() if text]
        for key, action in self.actions.items():
            if key in chosen:
                action.setShortcuts([QKeySequence(chosen[key])] if chosen[key] else [])
            else:
                action.setShortcuts([default for default in self.defaults[key]
                                     if key in FIXED or not any(default == other for other in taken)])

    def current(self, key: str) -> str:
        """The shortcut in use for a command, as portable text."""
        return self.actions[key].shortcut().toString(QKeySequence.SequenceFormat.PortableText)

    def default(self, key: str) -> str:
        """The shortcut a command has by itself."""
        return self.defaults[key][0].toString(QKeySequence.SequenceFormat.PortableText) if self.defaults[key] else ""

    def choose(self, shown: Mapping[str, str]) -> None:
        """Remember the shortcuts that differ from the defaults, and use them in every window.

        Commands not in ``shown`` (hidden ones, such as restarting as administrator in an elevated window) keep
        their choices, unless their key was given away.
        """
        given = set(filter(None, shown.values()))
        chosen = {key: text for key, text in self.controller.chosen.items()
                  if key in self.actions and key not in shown and text not in given}
        chosen |= {key: text for key, text in shown.items() if key not in FIXED and text != self.default(key)}
        self.settings.setValue(SHORTCUTS_KEY, json.dumps(chosen))
        self.controller.apply(chosen)

    def conflicts(self, shown: Mapping[str, str]) -> Sequence[str]:
        """The commands whose shortcut cannot be used, or is another command's too."""
        counts: dict[str, int] = {}
        for text in shown.values():
            if text:
                counts[text] = counts.get(text, 0) + 1
        fixed = {self.current(key) for key in FIXED if key in self.actions}
        return [key for key, text in shown.items() if text and (
            counts[text] > 1 or text in fixed or (text != self.default(key) and not usable(text)))]
