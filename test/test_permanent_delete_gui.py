"""*Delete permanently* in the window: always asked first, only the approved entries, made-up data only.

Every fixture lives under ``tmp_path``; the conftest guard refuses any removal outside pytest's
temporary directory, and any question a test does not answer itself counts as declined.
"""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox

from conftest import make_tree
from test_gui import _child, _scanned, _wait
from test_gui import window as window  # noqa: PLC0414 - shared fixture
from je_file_tree.core.node import Node
from je_file_tree.core.protected import PROGRAMS, Protection
from je_file_tree.core.system_files import SystemFile
from je_file_tree.gui import i18n, main_window
from je_file_tree.gui import permanent_delete as gui_delete
from je_file_tree.gui.permanent_delete import LISTED, PermanentDeleteWorker, PermanentReportDialog
from je_file_tree.gui.strings import STRINGS

YES, NO = QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No


def _contents(folder: Path) -> dict[str, bytes | None]:
    return {path.relative_to(folder).as_posix(): None if path.is_dir() else path.read_bytes()
            for path in sorted(folder.rglob("*"))}


@pytest.fixture
def answers(monkeypatch) -> list[str]:
    """Answer the main question Yes and record its text."""
    asked: list[str] = []
    monkeypatch.setattr(main_window, "confirm_permanent_delete",
                        lambda _parent, _title, text: asked.append(text) or YES)
    return asked


@pytest.fixture
def no_start(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("a declined question started a deletion")
    monkeypatch.setattr(PermanentDeleteWorker, "start", forbidden)


@pytest.fixture
def reports(monkeypatch) -> list[tuple[str, list[tuple[str, str]]]]:
    """Capture the end-of-run report instead of waiting for a user to close it."""
    shown: list[tuple[str, list[tuple[str, str]]]] = []
    def capture(dialog):
        shown.append((dialog.summary.text(), list(dialog.model.rows())))
        return 0
    monkeypatch.setattr(PermanentReportDialog, "exec", capture)
    return shown


def _finish(window, qapp) -> None:
    _wait(qapp, lambda: window._delete_worker is None)


# --- asking -----------------------------------------------------------------------------------


@pytest.mark.parametrize("dismissal", ["no", "escape", "close", "return"])
def test_a_declined_or_closed_question_deletes_nothing(window, qapp, sample_tree, monkeypatch, no_start, dismissal):
    _scanned(window, qapp, sample_tree)
    root = window.results.tree_model.root
    before = _contents(sample_tree)
    monkeypatch.setattr(main_window, "confirm_permanent_delete", gui_delete.confirm_permanent_delete)
    seen = []
    def answer():
        dialog = QApplication.activeModalWidget()
        seen.append((dialog.icon(), dialog.textFormat(), dialog.standardButtons(),
                     dialog.standardButton(dialog.defaultButton())))
        if dismissal == "escape":
            QTest.keyClick(dialog, Qt.Key.Key_Escape)
        elif dismissal == "return":
            QTest.keyClick(dialog, Qt.Key.Key_Return)
        elif dismissal == "close":
            dialog.close()
        else:
            dialog.button(NO).click()
    QTimer.singleShot(1, answer)

    window.delete_permanently([_child(root, "big.bin"), _child(root, "photos")])

    assert seen == [(QMessageBox.Icon.Warning, Qt.TextFormat.PlainText, YES | NO, NO)]
    assert window._delete_worker is None and _contents(sample_tree) == before
    assert root.size == 1000


def test_the_question_names_entries_count_size_and_that_it_cannot_be_undone(window, qapp, sample_tree, answers,
                                                                            no_start):
    _scanned(window, qapp, sample_tree)
    root = window.results.tree_model.root
    monkeypatch_nodes = [_child(root, "big.bin"), _child(root, "photos")]
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(main_window, "confirm_permanent_delete", lambda _p, _t, text: answers.append(text) or NO)
        window.delete_permanently(monkeypatch_nodes)
    text = answers[0]
    assert text == gui_delete.permanent_question(monkeypatch_nodes, window._unit)
    for expected in ("these 2 items", "750 B in total", str(sample_tree / "big.bin"), str(sample_tree / "photos"),
                     "(500 B)", "(250 B)", "do not go to the Recycle Bin", "cannot be undone",
                     "Anything added or changed since the scan is left in place"):
        assert expected in text


def test_a_long_selection_names_the_largest_and_counts_the_rest():
    parent = Node(os.path.abspath("made-up-root"), True)
    nodes = [Node(f"f{index}.bin", False, size=index + 1, parent=parent) for index in range(LISTED + 3)]
    text = gui_delete.permanent_question(nodes, "B")
    assert "…and 3 more" in text and "f10.bin" in text and "f0.bin" not in text
    assert "11 items" in text and "Anything added" not in text  # no folder among them
    single = gui_delete.permanent_question(nodes[:1], "B")
    assert "“f0.bin” (1 B)" in single and nodes[0].path in single and "cannot be undone" in single


def test_protected_folders_get_their_own_question_first(window, qapp, sample_tree, monkeypatch, no_start):
    _scanned(window, qapp, sample_tree)
    root = window.results.tree_model.root
    window._protected = [Protection(str(sample_tree / "photos"), PROGRAMS)]
    protected_questions: list[str] = []
    monkeypatch.setattr(QMessageBox, "warning", lambda _parent, _title, text, *_args:
                        protected_questions.append(text) or NO)
    monkeypatch.setattr(main_window, "confirm_permanent_delete",
                        lambda *_args: pytest.fail("the main question came before the protected one"))

    window.delete_permanently([_child(root, "photos")])

    assert len(protected_questions) == 1
    assert "Deleting them permanently can make the system" in protected_questions[0]
    assert str(sample_tree / "photos") in protected_questions[0]
    assert (sample_tree / "photos" / "a.jpg").exists()


def test_windows_managed_entries_are_refused_before_any_question(window, qapp, sample_tree, monkeypatch, answers):
    _scanned(window, qapp, sample_tree)
    root = window.results.tree_model.root
    big = _child(root, "big.bin")
    monkeypatch.setattr(main_window, "system_file", lambda path: SystemFile("pagefile", "memory")
                        if path == big.path else None)
    refused: list[list[str]] = []
    monkeypatch.setattr(main_window, "refuse_managed", lambda _parent, nodes: refused.append([n.name for n in nodes]))
    monkeypatch.setattr(PermanentDeleteWorker, "start", lambda *_args: pytest.fail("nothing was approved"))

    window.delete_permanently([big])

    assert refused == [["big.bin"]] and answers == []
    assert (sample_tree / "big.bin").exists()


# --- deleting ---------------------------------------------------------------------------------


def test_approved_entries_and_only_they_are_deleted_and_the_results_follow(window, qapp, sample_tree, monkeypatch,
                                                                          answers):
    _scanned(window, qapp, sample_tree)
    root = window.results.tree_model.root
    rescanned: list[Node] = []
    monkeypatch.setattr(window, "rescan_folder", rescanned.append)
    before = _contents(sample_tree)

    window.delete_permanently([_child(root, "big.bin"), _child(root, "photos")])
    _finish(window, qapp)

    assert len(answers) == 1
    expected = {name: value for name, value in before.items()
                if name not in {"big.bin", "photos"} and not name.startswith("photos/")}
    assert _contents(sample_tree) == expected
    assert root.size == 250 and [child.name for child in root.children] == ["code", "notes.txt"]
    assert "Permanently deleted 4 entries (750 B)" in window.statusBar().currentMessage()
    _wait(qapp, lambda: bool(rescanned))
    assert rescanned == [root]
    records = window._journal.recent().records
    assert {(Path(record.source).name, record.reason, record.outcome.status) for record in records} == {
        ("big.bin", "permanent_delete", "deleted"), ("photos", "permanent_delete", "deleted")}
    assert window.results.isEnabled() and not window._undo.available


def test_refusals_and_arrivals_stay_and_are_all_reported(window, qapp, tmp_path, monkeypatch, answers, reports):
    folder = tmp_path / "scan"
    make_tree(tmp_path, {"scan": {"keep.txt": b"k", "edited.txt": b"e", "box": {"old.txt": b"o"}}})
    _scanned(window, qapp, folder)
    root = window.results.tree_model.root
    monkeypatch.setattr(window, "rescan_folder", lambda _node: None)
    (folder / "edited.txt").write_bytes(b"edited after the scan")
    (folder / "box" / "new.txt").write_bytes(b"arrived after the scan")

    window.delete_permanently([_child(root, "edited.txt"), _child(root, "box")])
    _finish(window, qapp)

    assert _contents(folder) == {"box": None, "box/new.txt": b"arrived after the scan",
                                 "edited.txt": b"edited after the scan", "keep.txt": b"k"}
    summary, rows = reports[0]
    assert "Left in place: 3" in summary
    assert rows == [(str(folder / "edited.txt"), i18n.tr("permanent_skip_changed")),
                    (str(folder / "box" / "new.txt"), i18n.tr("permanent_skip_arrived")),
                    (str(folder / "box"), i18n.tr("permanent_skip_not_empty"))]
    statuses = {Path(record.source).name: record.outcome.status for record in window._journal.recent().records}
    assert statuses == {"edited.txt": "skipped", "box": "partial"}


def test_a_system_failure_is_reported(window, qapp, sample_tree, monkeypatch, answers, reports):
    from je_file_tree.core import permanent_delete as core

    _scanned(window, qapp, sample_tree)
    root = window.results.tree_model.root
    monkeypatch.setattr(window, "rescan_folder", lambda _node: None)
    def refuse(path, *_args, **_kwargs):
        raise PermissionError(13, "made-up lock", path)
    monkeypatch.setattr(core, "remove_entry", refuse)

    window.delete_permanently([_child(root, "notes.txt")])
    _finish(window, qapp)

    assert (sample_tree / "notes.txt").exists()
    summary, rows = reports[0]
    assert "failed: 1" in summary and rows[0][0] == str(sample_tree / "notes.txt")
    assert rows[0][1].startswith("The system did not delete it:") and "made-up lock" in rows[0][1]


def test_cancelling_midway_keeps_the_rest(window, qapp, tmp_path, monkeypatch, answers, reports):
    from je_file_tree.core import permanent_delete as core

    folder = tmp_path / "scan"
    make_tree(tmp_path, {"scan": {"first.txt": b"1" * 30, "second.txt": b"2" * 20, "third.txt": b"3" * 10}})
    _scanned(window, qapp, folder)
    root = window.results.tree_model.root
    monkeypatch.setattr(window, "rescan_folder", lambda _node: None)
    guarded = core.remove_entry
    def remove_then_stop(path, expected, parent, *, directory):
        guarded(path, expected, parent, directory=directory)
        window._delete_worker.cancel()  # what Esc does, from the worker's side of the first removal
    monkeypatch.setattr(core, "remove_entry", remove_then_stop)

    window.delete_permanently([_child(root, name) for name in ("first.txt", "second.txt", "third.txt")])
    _finish(window, qapp)

    assert sorted(_contents(folder)) == ["second.txt", "third.txt"]
    summary, rows = reports[0]
    assert [reason for _path, reason in rows] == [i18n.tr("permanent_skip_cancelled")] * 2


def test_escape_stops_a_running_deletion(window):
    stopped = []
    window._delete_worker = SimpleNamespace(cancel=lambda: stopped.append(True))
    try:
        window.stop_scan()
    finally:
        window._delete_worker = None
    assert stopped == [True]


def test_closing_during_a_deletion_waits_for_it(window, qapp, sample_tree, monkeypatch, answers):
    _scanned(window, qapp, sample_tree)
    root = window.results.tree_model.root
    monkeypatch.setattr(window, "rescan_folder", lambda _node: None)
    window.delete_permanently([_child(root, "notes.txt")])
    assert window._delete_worker is not None and window.operation_busy
    window.close()
    _wait(qapp, lambda: window._close_ready)
    assert window._delete_worker is None or window._delete_worker.isFinished()


# --- where it is offered ----------------------------------------------------------------------


def test_the_action_sits_beside_the_trash_action_and_follows_its_state(window, qapp, sample_tree):
    action, trash = window._actions["permanent_delete"], window._actions["trash"]
    assert action.shortcut() == QKeySequence("Shift+Del")
    assert action.text() == "Delete permanently" and "cannot be undone" in action.toolTip()
    file_menu = window._menus["menu_file"].actions()
    assert file_menu.index(action) == file_menu.index(trash) + 1
    assert action.isEnabled() == trash.isEnabled() is False
    _scanned(window, qapp, sample_tree)
    assert action.isEnabled() == trash.isEnabled() is True
    window._path_dialogs.add(object())
    window._update_actions()
    assert action.isEnabled() == trash.isEnabled() is False
    window._path_dialogs.clear()
    window._update_actions()


def _recording_menus(monkeypatch) -> list[list[str]]:
    """Record each context menu's item texts instead of showing it."""
    texts: list[list[str]] = []

    class RecordingMenu(QMenu):
        def exec(self, *_args):
            texts.append([action.text() for action in self.actions()])

    monkeypatch.setattr(main_window, "QMenu", RecordingMenu)
    return texts


def test_the_context_menu_offers_it_after_the_trash_item(window, qapp, sample_tree, monkeypatch):
    _scanned(window, qapp, sample_tree)
    root = window.results.tree_model.root
    texts = _recording_menus(monkeypatch)
    picked =[_child(root, "big.bin"), _child(root, "notes.txt")]

    window.show_menu_for(picked[0], picked, QPoint())
    window.show_menu_for(picked[0], picked[:1], QPoint())

    many, single = texts
    assert many[many.index("Move 2 items to Recycle Bin") + 1] == "Delete 2 items permanently"
    assert single[single.index("Move to Recycle Bin") + 1] == "Delete permanently"


def test_it_is_never_offered_from_clean_up_or_duplicate_suggestions(window, qapp, sample_tree, monkeypatch):
    _scanned(window, qapp, sample_tree)
    root = window.results.tree_model.root
    texts = _recording_menus(monkeypatch)
    monkeypatch.setattr(window, "delete_permanently", lambda _nodes: pytest.fail("offered from a suggestion list"))
    for view in (window.results.cleanup.view, window.results.duplicates.view):
        window.results.menu_source = view
        try:
            window.show_menu_for(root.children[0], [root.children[0]], QPoint())
        finally:
            window.results.menu_source = None
        assert "Move to Recycle Bin" in texts[-1] and "Delete permanently" not in texts[-1]
        monkeypatch.setattr(view, "hasFocus", lambda: True)
        window._delete_selected()
        assert window.statusBar().currentMessage() == i18n.tr("permanent_not_suggestions")
        monkeypatch.setattr(view, "hasFocus", lambda: False)


# --- words --------------------------------------------------------------------------------------


_IRREVERSIBLE = {"en": ("cannot be undone", "Recycle Bin"), "zh-TW": ("無法復原", "資源回收筒"),
                 "zh-CN": ("无法恢复", "回收站"), "ja": ("元に戻せません", "ごみ箱"),
                 "ko": ("되돌릴 수 없습니다", "휴지통")}


@pytest.mark.parametrize("language", sorted(_IRREVERSIBLE))
def test_the_question_says_it_cannot_be_undone_in_every_language(language):
    i18n.set_language(language)
    try:
        for key in ("permanent_confirm", "permanent_confirm_many"):
            text = i18n.tr(key, name="made-up.txt", size="1 B", path="made-up-path", count="2", names="• x")
            assert all(words in text for words in _IRREVERSIBLE[language]), (language, key)
            assert "made-up" in text or "• x" in text
    finally:
        i18n.set_language(i18n.DEFAULT_LANGUAGE)


@pytest.mark.parametrize("language", sorted(STRINGS))
def test_the_strings_form_one_block_after_the_trash_question(language):
    keys = list(STRINGS[language])
    permanent = [index for index, key in enumerate(keys) if key.startswith("permanent_")]
    start = keys.index("trash_done_many") + 1
    assert permanent == list(range(start, start + len(permanent)))
    assert [keys[index] for index in permanent] == [key for key in STRINGS["en"] if key.startswith("permanent_")]
