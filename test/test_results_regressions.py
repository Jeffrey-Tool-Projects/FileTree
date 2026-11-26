"""Defects a review of the results side of the window found on 2026-11-26; each test failed before its fix."""

import json
import threading
import time
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QMenu, QMessageBox

from conftest import make_tree
from test_gui import _child, _scanned, _select, _wait, window as window  # noqa: PLC0414 - explicit fixture re-export
from je_file_tree.core.analysis import summarise
from je_file_tree.core.export import export_json
from je_file_tree.core.multi_scan import scan_roots
from je_file_tree.core.node import Node
from je_file_tree.core.scanner import scan
from je_file_tree.gui import changes_panel, file_actions, main_window, scan_worker
from je_file_tree.gui.bar_chart import BarChartWidget
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.results_view import CHANGES_TAB, LARGEST_TAB
from je_file_tree.gui.scan_worker import ScanWorker, analyse
from je_file_tree.gui.sunburst_widget import SunburstWidget


def _remove(window, *nodes):
    """Take entries out of the results as a finished removal does."""
    removed = summarise(Node("", True, children=list(nodes)), limit=0, now=window.results.outcome.now)
    window.results.forget(list(nodes), removed=removed)


@pytest.mark.parametrize("error", [SyntaxError("not a TIFF file"), RuntimeError("broken")])
def test_an_unexpected_search_failure_ends_the_search(window, qapp, sample_tree, monkeypatch, error):
    _scanned(window, qapp, sample_tree)
    panel = window.results.duplicates

    def fail(*_args, **_options):
        raise error

    monkeypatch.setattr(scan_worker, "find_duplicates", fail)
    panel.start()
    _wait(qapp, lambda: not panel.running)
    assert str(error) in panel.status.text() and panel.start_button.isEnabled()


def test_stopping_nothing_does_not_call_the_search_stopped(window, qapp, tmp_path):
    for name in ("a", "b"):
        (tmp_path / name).write_bytes(b"x" * 2_000_000)
    _scanned(window, qapp, tmp_path)
    panel = window.results.duplicates
    panel.start()
    _wait(qapp, lambda: not panel.running and panel.groups)
    before = panel.status.text()
    panel.stop()
    assert panel.status.text() == before and panel.groups


# --- refreshing changed folders ---------------------------------------------------------------------------


def _hold_scans(monkeypatch, outcome="cancelled"):
    entered = threading.Event()

    def run(worker):
        entered.set()
        if outcome == "cancelled":
            worker._cancel.wait(10)
            worker.cancelled.emit(None)
        else:
            worker.failed.emit("unreadable")

    monkeypatch.setattr(ScanWorker, "run", run)
    return entered


@pytest.mark.parametrize("outcome", ["cancelled", "failed"])
def test_a_changed_folder_that_was_not_read_stays_on_offer(window, qapp, sample_tree, monkeypatch, outcome):
    _scanned(window, qapp, sample_tree)
    root = window.results.tree_model.root
    photos, code = _child(root, "photos"), _child(root, "code")
    warned = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warned.append(args[2]))
    window._mark_changed([photos, code])
    entered = _hold_scans(monkeypatch, outcome)
    window.refresh_changed()
    _wait(qapp, entered.is_set)
    window.stop_scan()
    _wait(qapp, lambda: window._worker is None)
    qapp.processEvents()
    assert set(window._trash_rescans) == {photos, code} and window._rescanning is None and not window._refreshing
    assert [photos.path in text or code.path in text for text in warned] == ([True] if outcome == "failed" else [])


def test_follow_changes_reads_a_stopped_folder_again_later(window, qapp, sample_tree, monkeypatch):
    _scanned(window, qapp, sample_tree)
    root = window.results.tree_model.root
    follow = window._follow
    follow.root = root
    follow.retry([(_child(root, "photos"), False), (_child(root, "code"), True)])
    assert follow._pending.folders == (_child(root, "photos").path,)
    assert follow._pending.trees == (_child(root, "code").path,)
    assert follow._since > time.monotonic() + 20  # not at once: somebody may have stopped it
    entered = _hold_scans(monkeypatch)
    retried = []
    monkeypatch.setattr(follow, "retry", retried.append)
    chosen = [(_child(root, "photos"), False)]
    window.refresh_folders(chosen)
    _wait(qapp, entered.is_set)
    window.stop_scan()
    _wait(qapp, lambda: window._worker is None)
    assert retried == [chosen]


# --- after a removal ----------------------------------------------------------------------------------------


def test_the_selection_follows_a_removal(window, qapp, sample_tree):
    _scanned(window, qapp, sample_tree)
    notes = _child(window.results.tree_model.root, "notes.txt")
    _select(window, notes)
    window.results.select_node(notes)
    seen = []
    window.results.selection_changed.connect(seen.append)
    _remove(window, notes)
    assert seen and seen[-1] is window.results.selected_node() and seen[-1] is not notes


def test_the_places_of_a_focused_type_follow_a_removal(window, qapp, tmp_path):
    make_tree(tmp_path, {"a": {"one.bin": b"x" * 10}, "b": {"two.bin": b"x" * 20}, "c.txt": b"x"})
    _scanned(window, qapp, tmp_path)
    results = window.results
    results.show_largest_of_type(".bin")
    _wait(qapp, lambda: results.type_locations_model.rowCount() == 2)
    results.tabs.setCurrentIndex(CHANGES_TAB - 1)
    tab = results.tabs.currentIndex()
    root = results.tree_model.root
    _remove(window, _child(_child(root, "b"), "two.bin"))
    _wait(qapp, lambda: results.type_locations_model.rowCount() == 1)
    assert results._focus == ("type", ".bin") and not results._type_locations_pane.isHidden()
    assert results.tabs.currentIndex() == tab
    assert [node.name for node in results.largest_model.rows()] == ["one.bin"]


# --- menus, names and paths -----------------------------------------------------------------------------------


def test_an_open_menu_keeps_its_path_when_the_branch_is_replaced(window, qapp, sample_tree, monkeypatch):
    _scanned(window, qapp, sample_tree)
    photo = _child(_child(window.results.tree_model.root, "photos"), "a.jpg")
    path, copied, scanned = photo.path, [], []
    monkeypatch.setattr(file_actions, "copy_path", copied.append)
    monkeypatch.setattr(file_actions, "open_path", copied.append)

    class Menu(QMenu):
        def exec(self, _point):
            photo.parent.detach()  # a refresh replaced the branch meanwhile
            for action in self.actions():
                if action.text() in (tr("menu_copy_path"), tr("menu_open_item")):
                    action.trigger()

    monkeypatch.setattr(main_window, "QMenu", Menu)
    monkeypatch.setattr(window, "start_scan", lambda *args: scanned.append(args))
    window.show_menu_for(photo, [photo], QPoint())
    assert copied == [path, path]
    window.rescan_folder(photo.parent)  # no longer part of the results
    assert window._worker is None and not scanned


def test_a_combined_root_has_a_name(window, qapp, sources):
    window.results.show_outcome(analyse(scan_roots(sources)))
    root = window.results.tree_model.root
    window._selection_changed(root)
    assert tr("multi_roots") in window.statusBar().currentMessage()


@pytest.fixture
def sources(tmp_path):
    folders = [tmp_path / "one", tmp_path / "two"]
    for folder in folders:
        folder.mkdir()
        (folder / "file").write_bytes(b"x")
    return folders


@pytest.mark.parametrize("chart", [BarChartWidget, SunburstWidget])
def test_chart_tips_show_names_literally(qapp, chart):
    root = Node("C:\\scan", True, children=[], size=10)
    child = Node("<i>a&lt;b", False, parent=root, size=5)
    root.children.append(child)
    stub = SimpleNamespace(_view_root=root, unit="auto")
    text = chart._describe(stub, child)
    assert "&lt;i&gt;a&amp;lt;b" in text and "<i>" not in text


# --- texts and actions that follow ------------------------------------------------------------------------------


def test_the_chosen_unit_is_used_everywhere(window, qapp, sample_tree):
    _scanned(window, qapp, sample_tree)
    window.set_unit("KB")
    results = window.results
    assert "1.0 KB" in results._summary_text()
    assert all(" KB)" in label for _colour, label in results._legend_items())
    assert results.scan_bar.unit == "KB"
    window.set_unit("auto")


def test_reports_are_offered_again_when_the_analysis_ends(window, qapp, sample_tree):
    _scanned(window, qapp, sample_tree)
    root = window.results.tree_model.root
    window._start_analysis(root, with_capacity=False)
    assert not window._actions["export_report_html"].isEnabled()
    _wait(qapp, lambda: not window._analysers)
    assert window._actions["export_report_html"].isEnabled()


def _saved(tmp_path, name, **sizes):
    folder = tmp_path / name
    make_tree(tmp_path, {name: {key: b"x" * size for key, size in sizes.items()}})
    target = tmp_path / f"{name}.json"
    export_json(scan(folder).root, target)
    document = json.loads(target.read_text(encoding="utf-8"))
    target.write_text(json.dumps(document), encoding="utf-8")
    return str(target)


def test_a_comparison_being_read_survives_a_change_of_the_tree(window, qapp, sample_tree, tmp_path, monkeypatch):
    other = tmp_path / "other"
    other.mkdir()
    first, second = _saved(other, "first", a=1), _saved(other, "second", b=2)
    _scanned(window, qapp, sample_tree)
    panel = window.results.changes
    panel.open(first)
    _wait(qapp, lambda: not panel.busy)
    assert panel.saved.root.endswith("first")
    started = []
    real = changes_panel.CompareWorker.start

    def hold(worker):
        started.append(worker)

    monkeypatch.setattr(changes_panel.CompareWorker, "start", hold)
    panel.open(second)
    panel.refresh()  # a removal or refresh while it is read
    monkeypatch.setattr(changes_panel.CompareWorker, "start", real)
    started[-1].start()
    _wait(qapp, lambda: not panel.busy)
    assert panel.saved.root.endswith("second")
    started[0].deleteLater()


def test_a_failed_comparison_does_not_bring_the_tab_forward_later(window, qapp, sample_tree, tmp_path, monkeypatch):
    other = tmp_path / "other"
    other.mkdir()
    first = _saved(other, "first", a=1)
    (other / "no.json").write_text("{}", encoding="utf-8")
    _scanned(window, qapp, sample_tree)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_args: None)
    results = window.results
    results.compare_with(first)
    _wait(qapp, lambda: not results.changes.busy)
    results.compare_with(str(other / "no.json"))
    _wait(qapp, lambda: not results.changes.busy)
    results.tabs.setCurrentIndex(LARGEST_TAB)
    results.changes.refresh()
    _wait(qapp, lambda: not results.changes.busy)
    assert results.tabs.currentIndex() == LARGEST_TAB
