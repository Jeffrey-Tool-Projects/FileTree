"""The settings window drives the menu actions; the settings file is validated value by value, all or nothing."""

import json

import pytest
from PySide6.QtWidgets import QFileDialog, QMessageBox

from test_gui import window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.gui import i18n, main_window, settings_dialog, settings_file, updates
from je_file_tree.gui.change_watch import ENABLED_KEY as FOLLOW_KEY
from je_file_tree.gui.settings_dialog import SettingsDialog, apply_settings
from je_file_tree.gui.text_scale import text_percent
from je_file_tree.gui.themes import theme_controller


@pytest.fixture
def dialog(window):
    opened = SettingsDialog(window)
    yield opened
    opened.deleteLater()
    window.text_size_menu.choose(100)
    theme_controller().apply("system")
    window.change_language("en")


def test_boxes_mirror_and_drive_the_menu_actions(window, dialog):
    for key, box in dialog.boxes.items():
        action = window._actions[key]
        assert box.isChecked() == action.isChecked() and box.text() == action.text(), key
    dialog.boxes["gentle"].click()
    assert window._actions["gentle"].isChecked() and window.settings.value("gentle_scan", type=bool)
    dialog.boxes["gentle"].click()
    assert not window._actions["gentle"].isChecked() and not window.settings.value("gentle_scan", type=bool)


def test_appearance_choices_apply_at_once(window, dialog):
    def pick(combo, value):
        index = combo.findData(value)
        combo.setCurrentIndex(index)
        combo.activated.emit(index)
    pick(dialog.theme, "dark")
    pick(dialog.text_size, 125)
    pick(dialog.unit, "MB")
    pick(dialog.language, "zh-TW")
    assert theme_controller().choice == "dark" and text_percent() == 125
    assert window.size_unit == "MB" and i18n.current_language() == "zh-TW"


def test_search_shows_only_matching_rows_and_says_when_none_match(dialog):
    dialog.search.setText("gentle")
    assert not dialog.boxes["gentle"].isHidden() and not dialog.boxes["gentle"].parentWidget().isHidden()
    assert dialog.boxes["hidden"].parentWidget().isHidden()
    assert not dialog.empty.isVisibleTo(dialog)
    dialog.search.setText("english")  # an option of the language list
    assert not dialog.language.parentWidget().isHidden()
    dialog.search.setText("no such setting")
    assert dialog.empty.isVisibleTo(dialog) and all(group.isHidden() for group in dialog.groups)
    dialog.search.clear()
    assert all(not row.isHidden() for row, _box, _words in dialog.rows)


def test_buttons_open_the_existing_windows(window, dialog, monkeypatch):
    opened = []
    monkeypatch.setattr(window, "edit_exclusions", lambda: opened.append("exclusions"))
    window._actions["exclusions"].triggered.disconnect()
    window._actions["exclusions"].triggered.connect(lambda: opened.append("exclusions"))
    dialog.buttons["exclusions"].click()
    assert opened == ["exclusions"]


def test_every_portable_key_is_one_the_window_uses():
    used = {main_window.ASK_ADMIN_KEY, main_window.AUTO_CPU_KEY, main_window.MFT_SCAN_KEY, main_window.EXCLUSIONS_KEY,
            main_window.SCAN_WORKERS_KEY, updates.ENABLED_KEY, FOLLOW_KEY}
    assert used <= set(settings_file.SETTINGS)
    assert set(settings_dialog._FLAGS) == {key for key, setting in settings_file.SETTINGS.items()
                                           if isinstance(setting.default, bool)} - {"history_enabled"}
    assert all(setting.valid(setting.default) for setting in settings_file.SETTINGS.values())


def test_an_export_holds_the_settings_in_use_and_round_trips(window, tmp_path):
    window.set_exclusions(["node_modules", "*.tmp"])
    window.set_workers(3)
    values = settings_file.current(window.settings, "ja")
    path = tmp_path / "settings.json"
    settings_file.write(str(path), values)
    assert settings_file.read(str(path)) == values
    assert values["language"] == "ja" and values["scan_workers"] == 3
    assert values["exclusions"] == ["node_modules", "*.tmp"]
    assert "recent" not in path.read_text(encoding="utf-8") and "geometry" not in path.read_text(encoding="utf-8")
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("values", [
    {"theme": "neon"}, {"text_size": 101}, {"text_size": "100"}, {"text_size": True}, {"gentle_scan": 1},
    {"scan_workers": 0}, {"scan_workers": 10**9}, {"scan_workers": 2.0}, {"exclusions": "x"}, {"exclusions": [""]},
    {"exclusions": ["a\0b"]}, {"exclusions": ["x"] * 1001}, {"recent": ["C:/"]}, {"language": "xx"}, {"unit": None},
])
def test_one_unusable_value_refuses_the_whole_file(values):
    with pytest.raises(ValueError, match="unusable setting"):
        settings_file.loads(json.dumps({"format": settings_file.FORMAT, "values": {"gentle_scan": True, **values}
                                        if "gentle_scan" not in values else values}))


@pytest.mark.parametrize("text", [
    "", "[]", "{}", '{"format": "other", "values": {}}', '{"format": "file-tree-settings/1", "values": []}',
    '{"format": "file-tree-settings/1", "values": {}, "extra": 1}',
    '{"format": "file-tree-settings/1", "values": {"theme": "dark", "theme": "light"}}',
])
def test_other_documents_are_refused(text):
    with pytest.raises(ValueError):
        settings_file.loads(text)


def test_an_oversized_file_is_refused(tmp_path):
    path = tmp_path / "big.json"
    path.write_text(" " * (settings_file.MAX_BYTES + 1), encoding="utf-8")
    with pytest.raises(ValueError, match="too large"):
        settings_file.read(str(path))


def test_registry_text_is_read_as_the_files_types(window):
    window.settings.setValue("gentle_scan", "true")
    window.settings.setValue("scan_workers", "7")
    window.settings.setValue("text_size", "broken")
    window.settings.setValue("exclusions", "only-one")
    values = settings_file.current(window.settings, "en")
    assert values["gentle_scan"] is True and values["scan_workers"] == 7
    assert values["text_size"] == 100 and values["exclusions"] == ["only-one"]


def test_import_asks_first_and_changes_only_what_differs(window, dialog, tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    current = dialog._current()
    settings_file.write(str(path), {**current, "gentle_scan": not current["gentle_scan"], "unit": "GB"})
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *_args, **_kwargs: (str(path), ""))
    asked = []

    def answer(box):
        asked.append((box.text(), box.defaultButton() is box.button(QMessageBox.StandardButton.No)))
        return QMessageBox.StandardButton.No
    monkeypatch.setattr(QMessageBox, "exec", answer)
    dialog._import()
    assert asked == [("Change 2 settings to the values in this file?", True)]
    assert window._actions["gentle"].isChecked() == current["gentle_scan"] and window.size_unit == current["unit"]
    monkeypatch.setattr(QMessageBox, "exec", lambda _box: QMessageBox.StandardButton.Yes)
    dialog._import()
    assert window._actions["gentle"].isChecked() != current["gentle_scan"] and window.size_unit == "GB"
    told = []
    monkeypatch.setattr(QMessageBox, "information", lambda *args: told.append(args[2]))
    dialog._import()
    assert told == [i18n.tr("settings_same")]
    path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: told.append(args[2]))
    dialog._import()
    assert told[-1] == i18n.tr("settings_invalid")


def test_applied_settings_reach_the_window_and_are_remembered(window, dialog):
    apply_settings(window, {"include_hidden": False, "exclusions": ["cache"], "scan_workers": 2, "theme": "light",
                            "text_size": 110, "language": "ko"})
    assert not window._actions["hidden"].isChecked() and window.exclusions() == ["cache"]
    assert window._scan_options().workers == 2 and theme_controller().choice == "light" and text_percent() == 110
    assert i18n.current_language() == "ko" and window.settings.value("language") == "ko"
