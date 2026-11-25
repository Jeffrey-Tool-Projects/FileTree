"""The rule editor refuses unusable rules, and what own rules find is named and never selected in bulk."""

import pytest
from PySide6.QtWidgets import QDialog

from test_gui import _wait, window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.core.cleanup_policy import CleanupPolicy, load_policy
from je_file_tree.core.custom_rules import CustomRule
from je_file_tree.gui import cleanup_policy_dialog, i18n
from je_file_tree.gui.cleanup_policy_dialog import CleanupPolicyDialog
from je_file_tree.gui.cleanup_text import explanation, title
from je_file_tree.gui.custom_rules_dialog import CustomRulesDialog
from je_file_tree.gui.recent_actions import _cleanup_title


@pytest.fixture
def editor(qapp):
    dialog = CustomRulesDialog([CustomRule("First", files=("*.bak",))])
    yield dialog
    dialog.deleteLater()


def test_add_update_and_remove(editor):
    assert editor.name.text() == "First" and editor.files.text() == "*.bak"
    editor.name.setText("Second")
    editor.folders.setText("MyApp/Cache ; Old logs")
    editor.files.setText("")
    editor.days.setValue(90)
    editor.add.click()
    assert editor.rules()[1] == CustomRule("Second", ("MyApp/Cache", "Old logs"), (), None, 90)
    assert editor.list.currentRow() == 1
    editor.name.setText("Renamed")
    editor.update_rule.click()
    assert [rule.name for rule in editor.rules()] == ["First", "Renamed"]
    editor.remove.click()
    editor.remove.click()
    assert editor.rules() == () and not editor.remove.isEnabled() and not editor.update_rule.isEnabled()


@pytest.mark.parametrize("name, files", [("First", "*.old"), ("Broad", "*"), ("", "*.bak"), ("None", "")])
def test_an_unusable_rule_changes_nothing_and_says_so(editor, name, files):
    editor.name.setText(name)
    editor.files.setText(files)
    editor.add.click()
    assert [rule.name for rule in editor.rules()] == ["First"]
    assert editor.status.text() == i18n.tr("custom_rules_invalid")


def test_changed_rules_need_a_new_policy_preview(window, monkeypatch):
    dialog = CleanupPolicyDialog(CleanupPolicy(), None, "auto", window)
    dialog.preview()
    save = dialog.buttons.button(dialog.buttons.StandardButton.Save)
    assert save.isEnabled()
    rule = CustomRule("Mine", files=("*.bak",))
    monkeypatch.setattr(cleanup_policy_dialog.CustomRulesDialog, "exec", lambda _self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr(cleanup_policy_dialog.CustomRulesDialog, "rules", lambda _self: (rule,))
    dialog.custom_button.click()
    assert not save.isEnabled() and "1" in dialog.custom_button.text()
    dialog.preview()
    assert save.isEnabled() and dialog.policy().custom == (rule,)
    assert load_policy(dialog.policy().dumps()).custom == (rule,)
    dialog.reject()
    dialog.deleteLater()


def test_names_and_reasons_in_every_language(qapp):
    key = CustomRule("Logs & more", files=("*.bak",))
    try:
        for language in i18n.LANGUAGES:
            i18n.set_language(language)
            assert "Logs & more" in title(key.key) and "Logs & more" in _cleanup_title("cleanup:" + key.key)
            assert i18n.tr("cleanup_custom_tip") in explanation(key.key)
            assert title("temp") == i18n.tr("cleanup_temp") and _cleanup_title("cleanup:future") == "cleanup:future"
    finally:
        i18n.set_language("en")


def test_the_panel_lists_own_finds_without_selecting_them_in_bulk(window, qapp, tmp_path):
    import os
    source = tmp_path / "source"
    source.mkdir()
    old = source / "plan.bak"
    old.write_bytes(b"x" * 50)
    os.utime(old, (1_600_000_000, 1_600_000_000))
    from je_file_tree.core.scanner import scan
    from je_file_tree.gui.scan_worker import analyse
    window._cleanup_policy = CleanupPolicy(custom=(CustomRule("Mine", files=("*.bak",)),))
    panel = window.results.cleanup
    panel.set_policy(window._cleanup_policy)
    window.results.show_outcome(analyse(scan(source)))
    _wait(qapp, lambda: panel.proposal_summary is not None)
    titles = [panel.model.data(panel.model.index(row, 0)) for row in range(panel.model.rowCount())]
    assert len(titles) == 1 and "Mine" in titles[0]
    assert not panel.select_all.isEnabled()
