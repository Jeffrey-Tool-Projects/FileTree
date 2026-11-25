"""Concurrent tabs isolate scan state and join ownership while sharing mutation exclusion."""

import hashlib
import threading

from PySide6.QtCore import QCoreApplication, QEvent, QSettings, QTimer
from PySide6.QtWidgets import QMessageBox
import pytest

from test_gui import _wait
from test_worker_lifecycle import _held_follow
from je_file_tree.core.operations import MoveReceipt
from je_file_tree.gui.busy_notice import busy_text
from je_file_tree.gui import change_watch, file_actions, i18n, main_window, scan_worker
from je_file_tree.gui.app import create_workspace
from je_file_tree.gui.qt_translation import apply_qt_translation
from je_file_tree.core.scanner import scan


@pytest.fixture
def workspace(qapp, tmp_path):
    settings = QSettings(str(tmp_path / "owned-settings.ini"), QSettings.Format.IniFormat)
    settings.setValue("language", "en")
    settings.setValue("scan_workers", 1)
    window = create_workspace(settings)
    yield window
    window.close()
    _wait(qapp, lambda: window._close_ready)
    window.deleteLater()
    # Its tabs and menus too, now: without an event loop 13,000 widgets stayed for every later theme change to repolish.
    QCoreApplication.sendPostedEvents(window, QEvent.Type.DeferredDelete)
    i18n.set_language("en")
    apply_qt_translation("en")


def test_tabs_execute_concurrently_and_preserve_distinct_sources(workspace, qapp, tmp_path, monkeypatch):
    roots = [tmp_path / "來源甲", tmp_path / "來源乙"]
    for number, root in enumerate(roots, 1):
        root.mkdir()
        (root / "資料.bin").write_bytes(b"payload" * number)
    before = {root: hashlib.sha256((root / "資料.bin").read_bytes()).hexdigest() for root in roots}
    barrier = threading.Barrier(2, timeout=5)
    original = scan_worker.scan

    def together(*args, **kwargs):
        barrier.wait()
        return original(*args, **kwargs)

    monkeypatch.setattr(scan_worker, "scan", together)
    first = workspace.current
    second = workspace.add_tab()
    first.start_scan(str(roots[0]))
    second.start_scan(str(roots[1]))
    workers = (first._worker, second._worker)
    assert workers[0] is not workers[1]
    _wait(qapp, lambda: all(window._worker is None for window in (first, second)))
    assert [window.results.outcome.result.root.size for window in (first, second)] == [7, 14]
    assert [window.results.outcome.result.root.path for window in (first, second)] == list(map(str, roots))
    assert first.results is not second.results and first.results.tree_model is not second.results.tree_model
    assert {root: hashlib.sha256((root / "資料.bin").read_bytes()).hexdigest() for root in roots} == before
    second.results.tree_filter.line.setText("unmatched")
    assert first.results.tree_filter.line.text() == ""
    assert second.results.tree_filter.line.text() == "unmatched"


def test_operation_owner_blocks_peer_commands_before_confirmation(workspace, tmp_path, monkeypatch):
    first, second = workspace.current, workspace.add_tab()
    held = object()
    source = tmp_path / "kept.bin"
    source.write_bytes(b"must remain")
    second.results.show_outcome(scan_worker.analyse(scan(tmp_path)))
    chosen = [node for node in second.results.outcome.result.root.iter_files() if node.path == str(source)]
    assert len(chosen) == 1
    first._path_dialogs.add(held)
    try:
        first._update_actions()
        assert first.operation_busy and second.operation_busy
        assert second._actions["open"].isEnabled()  # usable, but it says why it waits (U-20261118-02)
        second._actions["open"].trigger()
        assert second.statusBar().currentMessage() == busy_text(second._actions["open"].text(), scanning=False)
        monkeypatch.setattr(scan_worker.ScanWorker, "start", lambda _self: pytest.fail("peer scan dispatched"))
        monkeypatch.setattr(QMessageBox, "question", lambda *_args: pytest.fail("peer Trash approval dispatched"))
        second.move_to_trash(chosen)
        second.start_scan(str(tmp_path))
        assert second._worker is None and second._trash_worker is None and source.read_bytes() == b"must remain"
    finally:
        first._path_dialogs.remove(held)
    first._update_actions()
    assert not second.operation_busy and second._actions["open"].isEnabled()


def test_source_operation_waits_for_peer_native_reader_without_blocking_gui(
        workspace, qapp, tmp_path, monkeypatch, failed_move_diagnostics):
    source = tmp_path / "source"
    source.mkdir()
    kept = source / "kept"
    kept.write_bytes(b"kept")
    first, second = workspace.current, workspace.add_tab()
    for tab in (first, second):
        tab.results.show_outcome(scan_worker.analyse(scan(source)))
    calls = []
    monkeypatch.setattr(QMessageBox, "question", lambda *_: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_: QMessageBox.StandardButton.Ok)
    monkeypatch.setattr(file_actions, "trash_receipt", lambda path: calls.append(path) or MoveReceipt(False))
    release, reader = _held_follow(second, qapp, monkeypatch)
    try:
        first.move_to_trash(first.results.tree_model.root.children)
        assert reader.cancel.is_set() and reader.isRunning()
        assert first.operation_busy and second.operation_busy and not calls
        QTimer.singleShot(20, release.set)
        _wait(qapp, lambda: first._trash_worker is None)
        assert release.is_set() and calls == [str(kept)]
        assert not first.operation_busy and not second.operation_busy
        assert kept.read_bytes() == b"kept"
        report, captured = failed_move_diagnostics
        assert len(captured) == int(bool(report.error))
    finally:
        release.set()


def test_close_one_running_tab_joins_only_its_owned_scan(workspace, tmp_path, qapp, monkeypatch):
    entered = threading.Event()
    original = scan_worker.scan

    def held(path, **kwargs):
        entered.set()
        assert kwargs["cancel"].wait(5), "closed scan did not receive cancellation"
        return original(path, **kwargs)

    monkeypatch.setattr(scan_worker, "scan", held)
    first, second = workspace.current, workspace.add_tab()
    second.start_scan(str(tmp_path))
    _wait(qapp, entered.is_set)
    workspace.close_tab(workspace.tabs.indexOf(second))
    _wait(qapp, lambda: second._close_ready)
    assert second._closing
    assert second._worker is None
    _wait(qapp, lambda: workspace.tabs.count() == 1)
    assert workspace.current is first and not first._closing and workspace.tabs.count() == 1
    qapp.processEvents()
    assert first.results.outcome is None


@pytest.mark.parametrize("paused", [False, True])
def test_close_during_a_held_scan_keeps_the_event_loop_alive(workspace, tmp_path, qapp, monkeypatch, paused):
    source = tmp_path / "source"
    source.mkdir()
    kept = source / "kept.bin"
    kept.write_bytes(b"source remains untouched")
    entered, release = threading.Event(), threading.Event()
    original = scan_worker.scan

    def held(path, **kwargs):
        entered.set()
        assert release.wait(5), "closing blocked the GUI release timer"
        return original(path, **kwargs)

    monkeypatch.setattr(scan_worker, "scan", held)
    tab = workspace.current
    workspace.show()
    tab.start_scan(str(source))
    _wait(qapp, entered.is_set)
    tab.pause_scan(paused)
    ticks = []
    timer = QTimer(workspace)
    timer.setInterval(5)
    timer.timeout.connect(lambda: ticks.append(True))
    timer.start()
    try:
        workspace.quit_application()
        assert not release.is_set()
        assert not workspace._close_ready
        assert workspace.isVisible()
        assert tab._closing
        assert tab._worker._cancel.is_set()
        assert not tab._worker._pause.is_set()
        QTimer.singleShot(50, release.set)
        _wait(qapp, lambda: workspace._close_ready)
        assert ticks
        assert release.is_set()
        assert tab._close_ready
        assert not workspace.isVisible()
        assert kept.read_bytes() == b'source remains untouched'
    finally:
        release.set()
        timer.stop()
        _wait(qapp, lambda: workspace._close_ready)


def test_language_changes_every_tab_and_workspace(workspace):
    first, second = workspace.current, workspace.add_tab()
    second.change_language("zh-TW")
    assert workspace.new_button.text() == "新增掃描分頁"
    assert all(window._actions["open"].text() == i18n.tr("action_open") for window in (first, second))
    assert all(workspace.tabs.tabText(index) == "選擇資料夾" for index in range(2))


def test_quit_action_closes_all_tabs_and_tab_limit_is_enforced(workspace, monkeypatch):
    from je_file_tree.gui import workspace as module

    monkeypatch.setattr(module, "MAX_TABS", 2)
    first, second = workspace.current, workspace.add_tab()
    assert workspace.add_tab() is None and not workspace.new_button.isEnabled()
    second._actions["quit"].trigger()
    assert workspace._closing and first._closing and second._closing


def test_factory_never_starts_network_or_services(workspace):
    assert not workspace._services and not workspace.current._updates._active
    assert not workspace.current._updates.timer.isActive()


@pytest.mark.parametrize("following", [False, True])
def test_a_delete_in_one_tab_offers_only_its_folder_in_another(workspace, qapp, tmp_path, monkeypatch, following):
    source = tmp_path / "來源"
    (source / "資料").mkdir(parents=True)
    (source / "其他").mkdir()
    (source / "資料" / "removed.bin").write_bytes(b"gone" * 10)
    (source / "其他" / "kept.bin").write_bytes(b"kept")
    first, second = workspace.current, workspace.add_tab()
    first.results.show_outcome(scan_worker.analyse(scan(source / "資料")))
    second.results.show_outcome(scan_worker.analyse(scan(source)))
    peer_root = second.results.outcome.result.root
    if following:
        monkeypatch.setattr(change_watch, "watch_scope", lambda _scope, _changed, cancel, *, ready, **_feed: (
            ready("directory_changes"), cancel.wait()))
        monkeypatch.setattr(change_watch, "supported", lambda: True)
        second._actions["follow_changes"].setChecked(True)
        _wait(qapp, lambda: second._follow.worker is not None and bool(second._follow.worker.backend))
    scans, rescans = [], []
    monkeypatch.setattr(second, "start_scan", lambda path, **_kwargs: scans.append(path))
    monkeypatch.setattr(second, "rescan_folder", lambda node, **_kwargs: rescans.append(node))
    monkeypatch.setattr(main_window, "confirm_permanent_delete", lambda *_args: QMessageBox.StandardButton.Yes)

    first.delete_permanently(first.results.tree_model.root.children)  # this test's own made-up file
    _wait(qapp, lambda: first._delete_worker is None)
    assert not (source / "資料" / "removed.bin").exists() and (source / "其他" / "kept.bin").exists()
    folder = next(child for child in peer_root.children if child.name == "資料")
    assert second._trash_rescans == ([] if following else [folder])
    assert not second._follow._operation_gap
    if following:  # refreshed by itself, one folder only
        _wait(qapp, lambda: rescans == [folder])
        second._follow._since = 0.0
        second._follow.tick()
    else:  # offered, nothing read until asked
        assert second.results.refresh_notice.pending == 1 and rescans == []
    assert scans == [] and rescans == ([folder] if following else [])
