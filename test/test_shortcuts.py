"""Chosen shortcuts are validated, conflict-free and shared; the command finder runs real menu entries only."""

import json

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialog

from test_gui import window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.gui import i18n, window_dialogs
from je_file_tree.gui.app import create_window
from je_file_tree.gui.command_palette import CommandPalette, ShortcutsDialog, commands, plain
from je_file_tree.gui.shortcuts import FIXED, SHORTCUTS_KEY, TAKEN, load, shortcut_controller, usable


@pytest.fixture(autouse=True)
def _defaults_afterwards(qapp):
    yield
    shortcut_controller().apply({})


@pytest.mark.parametrize("text", ["Ctrl+G", "Alt+Q", "Ctrl+Shift+E", "F7", "Meta+J", "Shift+F3"])
def test_usable(text):
    assert usable(text)


@pytest.mark.parametrize("text", ["", "A", "Shift+A", "Space", "Return", "Ctrl+K, Ctrl+J", "nonsense+", *TAKEN])
def test_unusable(text):
    assert not usable(text)


@pytest.mark.parametrize("text, chosen", [
    ("", {}), (None, {}), (5, {}), ("{", {}), ("[]", {}), ("x" * 20_001, {}), ('{"open": "A"}', {}),
    ('{"open": 5}', {}), ('{"open": ""}', {"open": ""}), ('{"open": "Ctrl+G", "find": "Ctrl+G"}', {"open": "Ctrl+G"}),
    ('{"permanent_delete": "Ctrl+G", "trash": "F2", "quit": "F3"}', {}),
])
def test_saved_choices_are_read_defensively(text, chosen):
    assert load(text) == chosen


def test_choices_apply_in_every_window_and_are_remembered(window):
    other = create_window(window.settings)
    shown = {key: window._shortcuts.current(key) for key in window._actions if key not in FIXED}
    shown["programs"] = "Ctrl+G"
    shown["help"] = ""
    assert window._shortcuts.conflicts(shown) == []
    window._shortcuts.choose(shown)
    for each in (window, other):
        assert each._actions["programs"].shortcut() == QKeySequence("Ctrl+G")
        assert each._actions["help"].shortcut().isEmpty()
        assert each._actions["open"].shortcut() == QKeySequence(QKeySequence.StandardKey.Open)
    assert json.loads(window.settings.value(SHORTCUTS_KEY)) == {"programs": "Ctrl+G", "help": ""}
    other.close()
    other.deleteLater()
    shortcut_controller().apply({})
    third = create_window(window.settings)
    assert third._actions["programs"].shortcut() == QKeySequence("Ctrl+G")
    third.close()
    third.deleteLater()


def test_hidden_commands_keep_their_keys_until_they_are_given_away(window):
    shortcut_controller().apply({"elevate": "Ctrl+G", "programs": "Ctrl+J"})
    window._actions["elevate"].setVisible(False)
    dialog = ShortcutsDialog(window._shortcuts)
    assert "elevate" not in dialog.edits
    dialog.accept()
    assert shortcut_controller().chosen == {"elevate": "Ctrl+G", "programs": "Ctrl+J"}
    dialog.deleteLater()
    window._shortcuts.choose({"programs": "Ctrl+G"})
    assert shortcut_controller().chosen == {"programs": "Ctrl+G"}


def test_a_chosen_key_takes_over_another_commands_default(window):
    default = window._shortcuts.default("open")
    shortcut_controller().apply({"programs": default})
    assert window._actions["programs"].shortcut() == QKeySequence(default)
    assert window._actions["open"].shortcut().isEmpty()


def test_removing_stopping_and_quitting_cannot_be_rebound(window):
    before = {key: window._actions[key].shortcuts() for key in FIXED}
    shortcut_controller().apply({"programs": window._actions["permanent_delete"].shortcut().toString()})
    assert {key: window._actions[key].shortcuts() for key in FIXED} == before
    dialog = ShortcutsDialog(window._shortcuts)
    assert not FIXED & set(dialog.edits)
    dialog.deleteLater()


def test_conflicts_are_refused_and_named(window):
    dialog = ShortcutsDialog(window._shortcuts)
    dialog.edits["projects"].setKeySequence(QKeySequence("Ctrl+F"))
    dialog.accept()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert plain(window._actions["find"].text()) in dialog.status.text()
    dialog._reset()
    for text in ("Ctrl+Q", "Delete", "Ctrl+T"):
        dialog.edits["projects"].setKeySequence(QKeySequence(text))
        dialog.accept()
        assert dialog.result() != QDialog.DialogCode.Accepted, text
    dialog.edits["projects"].setKeySequence(QKeySequence("Ctrl+J"))
    dialog.accept()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert window._actions["projects"].shortcut() == QKeySequence("Ctrl+J")
    dialog.deleteLater()


def test_the_finder_lists_the_menus_and_nothing_hidden(window):
    listed = dict(commands(window.menuBar()))
    texts = {action.text() for action in listed.values()}
    assert window._actions["open"].text() in texts and window._actions["export_json"].text() in texts
    assert any(path.count(" › ") == 2 for path in listed)  # a command in a submenu names the way to it
    assert all(action.isVisible() and action.menu() is None for action in listed.values())
    assert plain("&File && more") == "File & more"


def test_typing_narrows_and_enter_runs_the_command_after_closing(window, monkeypatch):
    ran = []
    window._actions["projects"].triggered.connect(lambda: ran.append("projects"))
    palette = CommandPalette(window.menuBar())
    everything = palette.list.count()
    palette.box.setText("gentle scanning OPTIONS")
    assert palette.list.count() == 1 and everything > 40
    palette.box.setText("no such command")
    QTest.keyClick(palette.box, Qt.Key.Key_Return)
    assert palette.chosen is None and palette.result() != QDialog.DialogCode.Accepted
    palette.box.setText(plain(window._actions["export_json"].text()))  # there is no scan to export
    assert not palette.list.item(0).flags() & Qt.ItemFlag.ItemIsEnabled
    QTest.keyClick(palette.box, Qt.Key.Key_Return)
    assert palette.chosen is None
    palette.box.setText("text size")
    first = palette.list.currentRow()
    QTest.keyClick(palette.box, Qt.Key.Key_Down)
    assert palette.list.currentRow() == first + 1 and palette.box.text() == "text size"
    palette.deleteLater()

    def choose(dialog):
        dialog.box.setText(plain(window._actions["gentle"].text()))
        QTest.keyClick(dialog.box, Qt.Key.Key_Return)
        return dialog.result()
    monkeypatch.setattr(window_dialogs.CommandPalette, "exec", choose)
    before = window._actions["gentle"].isChecked()
    window.show_palette()
    assert window._actions["gentle"].isChecked() != before
    window.show_palette()
    assert window._actions["gentle"].isChecked() == before


def test_a_cancelled_finder_runs_nothing(window, monkeypatch):
    monkeypatch.setattr(window_dialogs.CommandPalette, "exec", lambda _dialog: QDialog.DialogCode.Rejected)
    monkeypatch.setattr(window._actions["gentle"], "trigger", lambda: pytest.fail("nothing runs"), raising=False)
    window.show_palette()


def test_every_language_names_the_finder(window):
    for language in i18n.LANGUAGES:
        window.change_language(language)
        assert i18n.tr("action_palette") in {action.text() for _path, action in commands(window.menuBar())}
    window.change_language("en")
