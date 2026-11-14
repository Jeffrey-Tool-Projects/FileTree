"""The Free up space dialog: nothing pre-checked, a live meter, and checked entries only through move_to_trash."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QTreeWidgetItem, QTreeWidgetItemIterator

from test_cleanup import age_tree
from test_gui import _wait, window as window  # noqa: PLC0414 - shared fixture
from test_protected import WINDOWS_ENV
from je_file_tree.core.advice import Adviser
from je_file_tree.core.cleanup import DETAILS, CleanupGroup
from je_file_tree.core.duplicates import DuplicateGroup
from je_file_tree.core.node import Node
from je_file_tree.core.protected import protected_places
from je_file_tree.core.reclaim import ReclaimSources, free_share_target
from je_file_tree.gui import file_actions, i18n
from je_file_tree.gui import main_window as main_window_module
from je_file_tree.gui.main_window import MainWindow
from je_file_tree.gui.reclaim_dialog import CUSTOM, GB, PRESETS_GB, SHARE, ReclaimDialog
from je_file_tree.gui.tree_model import NODE_ROLE

_KEYS = ("reclaim_title", "reclaim_hint", "reclaim_target", "reclaim_note", "reclaim_show", "reclaim_review",
         "reclaim_custom", "reclaim_share", "reclaim_action")


def _node(name: str, parent: Node | None = None, *, size: int = 0, is_dir: bool = False) -> Node:
    node = Node(name, is_dir, size=size, allocated=size, parent=parent, children=[] if is_dir else ())
    if parent is not None:
        parent.children.append(node)
        above: Node | None = parent
        while above is not None:
            above.size += size
            above.allocated += size
            above = above.parent
    return node


def _adviser(groups: list[CleanupGroup] | None) -> Adviser:
    return Adviser(protected_places("win32", WINDOWS_ENV), groups, platform="win32", environ=WINDOWS_ENV)


def _fake(*, ready: bool = True) -> tuple[ReclaimSources, dict[str, Node]]:
    root = _node("C:\\", is_dir=True)
    me = _node("me", _node("Users", root, is_dir=True), is_dir=True)
    cache = _node("cache2", _node("p", _node("Profiles", _node("Firefox", _node("Mozilla", me, is_dir=True),
                                                                      is_dir=True), is_dir=True), is_dir=True),
                  is_dir=True)
    _node("entries", cache, size=3 * GB)
    work = _node("work", me, is_dir=True)
    dump = _node("crash.dmp", work, size=2 * GB)
    kept = _node("disk.vhd", work, size=GB)
    extra = _node("disk.vhd", me, size=GB)
    movie = _node("movie.mp4", me, size=6 * GB)
    program = _node("tool.exe", _node("Program Files", root, is_dir=True), size=9 * GB)
    groups = [CleanupGroup("browser_cache", [cache], 3 * GB, DETAILS["browser_cache"]),
              CleanupGroup("crash_dumps", [dump], 2 * GB, DETAILS["crash_dumps"])]
    sources = ReclaimSources(root, _adviser(groups if ready else None), tuple(groups) if ready else (),
                             (DuplicateGroup(GB, [kept, extra], kept=kept),), (program, movie, dump, kept, extra),
                             total=100 * GB, free=5 * GB)
    return sources, {"root": root, "cache": cache, "dump": dump, "kept": kept, "extra": extra, "movie": movie,
                     "program": program}


def _items(dialog: ReclaimDialog) -> dict[Node, QTreeWidgetItem]:
    found = {}
    iterator = QTreeWidgetItemIterator(dialog.tree)
    while (item := iterator.value()) is not None:
        node = item.data(0, NODE_ROLE)
        if isinstance(node, Node):
            found[node] = item
        iterator += 1
    return found


def _check(dialog: ReclaimDialog, node: Node, qapp: QApplication) -> None:
    _items(dialog)[node].setCheckState(0, Qt.CheckState.Checked)
    qapp.processEvents()


def test_the_plan_opens_with_nothing_checked_and_never_proposes_what_must_stay(qapp) -> None:
    sources, nodes = _fake()
    dialog = ReclaimDialog(sources, "auto")
    try:
        items = _items(dialog)
        assert set(items) == {nodes["cache"], nodes["dump"], nodes["extra"], nodes["movie"]}
        assert dialog.checked_nodes() == [] and not dialog.review_button.isEnabled()
        assert dialog.meter.value() == 0 and dialog.selected_size() == 0
        assert nodes["program"] not in items and nodes["kept"] not in items
        top = [dialog.tree.topLevelItem(row) for row in range(dialog.tree.topLevelItemCount())]
        assert all(item.checkState(0) == Qt.CheckState.Unchecked for item in top)
        assert i18n.tr("reclaim_options") in top[-1].text(0), "your own files come last, as a separate list"
        assert dialog.target() == PRESETS_GB[0] * GB
    finally:
        dialog.deleteLater()


def test_checking_updates_the_meter_and_review_hands_over_exactly_the_checked_entries(qapp) -> None:
    sources, nodes = _fake()
    dialog = ReclaimDialog(sources, "auto")
    try:
        dialog.preset.setCurrentIndex(dialog.preset.findData(5))
        _check(dialog, nodes["dump"], qapp)
        assert dialog.selected_size() == 2 * GB and dialog.meter.value() == 400
        assert "2.0 GB" in dialog.selection.text() and "5.0 GB" in dialog.selection.text()
        cache_step = _items(dialog)[nodes["cache"]].parent()
        cache_step.setCheckState(0, Qt.CheckState.Checked)
        qapp.processEvents()
        assert dialog.meter.value() == dialog.meter.maximum()
        shown, handed = [], []
        dialog.selected.connect(shown.append)
        dialog.review_requested.connect(handed.append)
        dialog.tree.setCurrentItem(_items(dialog)[nodes["movie"]])
        dialog.show_button.click()
        assert shown == [nodes["movie"]] and not handed, "showing an entry is not choosing it"
        dialog.review_button.click()
        assert handed == [[nodes["cache"], nodes["dump"]]]
        assert dialog.result() == QDialog.DialogCode.Accepted
    finally:
        dialog.deleteLater()


def test_targets_presets_custom_and_free_share(qapp) -> None:
    sources, _nodes = _fake()
    dialog = ReclaimDialog(sources, "auto")
    try:
        data = [dialog.preset.itemData(row) for row in range(dialog.preset.count())]
        assert data == [*PRESETS_GB, CUSTOM, SHARE]
        assert dialog.custom.isHidden() and dialog.share.isHidden()
        dialog.preset.setCurrentIndex(data.index(CUSTOM))
        dialog.custom.setValue(2.5)
        assert not dialog.custom.isHidden() and dialog.target() == round(2.5 * GB)
        assert dialog.plan.target == round(2.5 * GB)
        dialog.preset.setCurrentIndex(data.index(SHARE))
        dialog.share.setValue(20)
        assert dialog.target() == free_share_target(20, 100 * GB, 5 * GB) == 15 * GB
        assert not dialog.drive.isHidden() and dialog.drive.text()
        assert not dialog.plan.reached and dialog.status.text()
    finally:
        dialog.deleteLater()
    unknown = ReclaimSources(sources.root, sources.adviser, sources.groups)
    dialog = ReclaimDialog(unknown, "auto")
    try:
        assert dialog.preset.findData(SHARE) == -1, "no capacity: no free-share target"
    finally:
        dialog.deleteLater()


def test_the_plan_fills_in_once_the_suggestions_arrive_and_keeps_the_checks(qapp) -> None:
    waiting, nodes = _fake(ready=False)
    dialog = ReclaimDialog(waiting, "auto")
    try:
        assert i18n.tr("reclaim_waiting") in dialog.status.text()
        assert nodes["cache"] not in _items(dialog)
        _check(dialog, nodes["extra"], qapp)
        dialog.update_sources(ReclaimSources(waiting.root, waiting.adviser, (), waiting.duplicates))
        assert nodes["cache"] not in _items(dialog), "the same answers: nothing to rebuild"
        groups = [CleanupGroup("browser_cache", [nodes["cache"]], 3 * GB, DETAILS["browser_cache"])]
        dialog.update_sources(ReclaimSources(waiting.root, _adviser(groups), tuple(groups),
                                             waiting.duplicates, waiting.largest, waiting.total, waiting.free))
        assert i18n.tr("reclaim_waiting") not in dialog.status.text()
        assert nodes["cache"] in _items(dialog) and dialog.checked_nodes() == [nodes["extra"]]
    finally:
        dialog.deleteLater()


@pytest.mark.parametrize("language", i18n.LANGUAGES)
def test_every_text_is_worded_in_every_language(qapp, language: str) -> None:
    i18n.set_language(language)
    try:
        sources, _nodes = _fake()
        dialog = ReclaimDialog(sources, "auto")
        try:
            assert dialog.windowTitle() == i18n.tr("reclaim_title")
            assert dialog.review_button.text() == i18n.tr("reclaim_review") and dialog.note.text()
            for key in _KEYS:
                assert i18n.tr(key) and i18n.tr(key) != key
            steps = [dialog.tree.topLevelItem(row).text(0) for row in range(dialog.tree.topLevelItemCount())]
            assert len(steps) == 4 and all(steps)
            assert dialog.status.text() and dialog.selection.text()
        finally:
            dialog.deleteLater()
    finally:
        i18n.set_language(i18n.DEFAULT_LANGUAGE)


def _plan_tree(tmp_path: Path) -> Path:
    folder = tmp_path / "plan"
    folder.mkdir()
    (folder / "video.bin").write_bytes(b"v" * 300_000)
    (folder / "memory.dmp").write_bytes(b"d" * 200_000)
    (folder / "notes.txt").write_bytes(b"n" * 100_000)
    age_tree(folder)
    return folder


def _scanned_plan(window: MainWindow, qapp: QApplication, folder: Path) -> Node:
    window.start_scan(str(folder))
    _wait(qapp, lambda: window.results.outcome is not None)
    _wait(qapp, lambda: window.results.cleanup.proposal_summary is not None and window.results.adviser.ready)
    root = window.results.tree_model.root
    assert root is not None
    return root


def _open_and_review(window: MainWindow, monkeypatch: pytest.MonkeyPatch, names: list[str], seen: list) -> None:
    def review(dialog: ReclaimDialog) -> QDialog.DialogCode:
        items = _items(dialog)
        seen.append(sorted(node.name for node in items))
        assert dialog.checked_nodes() == [], "nothing is checked for the user"
        for node, item in items.items():
            if node.name in names:
                item.setCheckState(0, Qt.CheckState.Checked)
        dialog.review()
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(ReclaimDialog, "exec", review)
    window.show_reclaim()


def test_a_declined_question_moves_nothing_and_a_yes_moves_only_the_checked_entry(
        window: MainWindow, qapp: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    folder = _plan_tree(tmp_path)
    root = _scanned_plan(window, qapp, folder)
    assert window._reclaim_action.isEnabled() and window.results.cleanup.reclaim.isEnabled()
    moved, questions, seen = [], [], []
    monkeypatch.setattr(file_actions, "trash_receipt", lambda path: moved.append(path) or True)
    monkeypatch.setattr(window, "rescan_folder", lambda _node: None)
    monkeypatch.setattr(QMessageBox, "question",
                        lambda *_args: questions.append(True) or QMessageBox.StandardButton.No)
    _open_and_review(window, monkeypatch, ["video.bin"], seen)
    _wait(qapp, lambda: window._trash_worker is None)
    assert seen == [["memory.dmp", "notes.txt", "video.bin"]]
    assert questions == [True] and moved == [], "the usual question was asked and its No moved nothing"
    assert (folder / "video.bin").exists() and root.size == 600_000
    monkeypatch.setattr(QMessageBox, "question", lambda *_args: QMessageBox.StandardButton.Yes)
    _open_and_review(window, monkeypatch, ["video.bin"], seen)
    _wait(qapp, lambda: window._trash_worker is None)
    assert moved == [str(folder / "video.bin")], "exactly the checked entry, nothing else"
    assert root.size == 300_000


def test_a_clean_up_entry_still_gets_the_clean_up_review(
        window: MainWindow, qapp: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    folder = _plan_tree(tmp_path)
    _scanned_plan(window, qapp, folder)
    reviewed, questions, moved, seen = [], [], [], []

    def cancel(dialog):
        reviewed.append(dialog.model.data(dialog.model.index(0, 1)))
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(main_window_module.CleanupReview, "exec", cancel)
    monkeypatch.setattr(QMessageBox, "question", lambda *_args: questions.append(True))
    monkeypatch.setattr(file_actions, "trash_receipt", lambda path: moved.append(path) or True)
    _open_and_review(window, monkeypatch, ["memory.dmp"], seen)
    assert reviewed == [str(folder / "memory.dmp")] and questions == [] and moved == []
    assert (folder / "memory.dmp").exists()


def test_the_plan_needs_a_scan(window: MainWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    opened = []
    monkeypatch.setattr(ReclaimDialog, "exec", opened.append)
    assert not window._reclaim_action.isEnabled()
    window.show_reclaim()
    assert opened == []
