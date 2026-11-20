"""Per-tab native-following ownership, bounded dirty state and fresh-scan-only event authority."""

import hashlib
import os
import sys
import time

import pytest
from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtTest import QSignalSpy
from PySide6.QtCore import QSettings

from test_gui import _wait
from test_gui import window as window  # noqa: PLC0414
from je_file_tree.core.change_watch import MAX_CHANGED, ChangeBatch
from je_file_tree.core.scanner import ScanOptions, scan
from je_file_tree.core.multi_scan import scan_roots
from je_file_tree.gui import change_watch as following
from je_file_tree.gui import main_window
from je_file_tree.gui.scan_worker import analyse
from je_file_tree.gui.app import create_workspace


def _source(window, tmp_path):
    source = tmp_path / "來源"
    (source / "資料" / "nested").mkdir(parents=True)
    (source / "另一個").mkdir()
    (source / "資料" / "file").write_bytes(b"kept")
    (source / "另一個" / "untouched").write_bytes(b"untouched")
    window.results.show_outcome(analyse(scan(source)))
    return source, window.results.outcome.result.root


def _enable(window, qapp, monkeypatch):
    def watch(_scope, _changed, cancel, *, ready, since=None, moved=None):
        ready("directory_changes")
        cancel.wait()

    monkeypatch.setattr(following, "watch_scope", watch)
    monkeypatch.setattr(following, "supported", lambda: True)
    window._actions["follow_changes"].setChecked(True)
    _wait(qapp, lambda: window._follow.worker is not None and bool(window._follow.worker.backend))
    return window._follow


def _dirty(controller, *paths, full=False):
    controller.worker.record(ChangeBatch(tuple(str(path) for path in paths), full))
    controller.tick()
    controller._since = time.monotonic() - 2


def test_default_off_and_opt_out_retires_worker_asynchronously(window, qapp, tmp_path, monkeypatch):
    _source(window, tmp_path)
    assert not window._actions["follow_changes"].isChecked() and window._follow.worker is None
    controller = _enable(window, qapp, monkeypatch)
    worker = controller.worker
    assert worker.isRunning() and window.settings.value("follow_changes", type=bool)
    window._actions["follow_changes"].setChecked(False)
    assert controller.worker is None and worker.cancel.is_set()
    _wait(qapp, lambda: not controller._retiring)
    assert not controller.timer.isActive() and not controller.label.isVisible()


def test_changed_folders_are_read_again_together_each_keeping_its_subfolders(window, qapp, tmp_path, monkeypatch):
    source, _root = _source(window, tmp_path)
    controller = _enable(window, qapp, monkeypatch)
    calls = []
    monkeypatch.setattr(window, "refresh_folders", calls.append)
    _dirty(controller, source / "資料", source / "資料" / "nested")
    assert not calls
    controller.tick()
    assert [[(node.path, whole) for node, whole in chosen] for chosen in calls] == [
        [(str(source / "資料"), False), (str(source / "資料" / "nested"), False)]]
    assert not controller._pending.folders
    controller.worker.record(ChangeBatch(tuple(str(source / f"d{number}" / "x") for number in range(MAX_CHANGED + 1))))
    taken = controller.worker.take()
    assert not taken.full and taken.trees == (str(source),)  # too many: their folder, read whole, not the root


def test_changed_folders_wait_for_a_request_unless_following_is_on(window, qapp, tmp_path, monkeypatch):
    _source(window, tmp_path)
    root = window.results.outcome.result.root
    branch, other = root.children[0], root.children[1]
    calls = []
    monkeypatch.setattr(window, "rescan_folder", calls.append)
    notice = window.results.refresh_notice
    window._mark_changed([branch])
    window._mark_changed([branch, other])
    for _ in range(5):
        qapp.processEvents()
    assert calls == [] and notice.pending == 2 and not notice.isHidden()
    window._rescan_after_trash()  # what closing another dialog or an expired Undo offer used to trigger
    assert calls == [] and window._trash_rescans == [branch, other]
    _enable(window, qapp, monkeypatch)  # the explicit opt-in to automatic refreshing takes them over
    _wait(qapp, lambda: len(calls) == 2)
    assert calls == [branch, other] and notice.isHidden() and not window._trash_rescans


def test_whole_scan_replaces_the_folders_on_offer(window, qapp, tmp_path):
    source, root = _source(window, tmp_path)
    notice = window.results.refresh_notice
    window._mark_changed([root.children[0]])
    assert notice.pending == 1
    window.start_scan(str(source))
    assert notice.isHidden() and not window._trash_rescans
    _wait(qapp, lambda: window._worker is None and window.results.outcome is not None)
    assert notice.isHidden()


def test_a_review_keeps_the_feed_and_reads_only_the_changed_folder_after(window, qapp, tmp_path, monkeypatch):
    source, root = _source(window, tmp_path)
    controller = _enable(window, qapp, monkeypatch)
    _dirty(controller, source / "資料")
    old = controller.worker
    rescans, refreshed = [], []
    monkeypatch.setattr(window, "rescan_folder", rescans.append)
    monkeypatch.setattr(window, "refresh_folders", refreshed.append)
    dialog = QDialog(window)
    window._path_dialogs.add(dialog)
    window._update_actions()
    window.pending_source_workers()  # what an approved operation asks for before it runs
    controller.tick()
    assert not rescans and not refreshed and controller.worker is old and not old.cancel.is_set()
    assert controller._operating and not controller._operation_gap
    window._path_dialogs.remove(dialog)
    controller.tick()
    assert not rescans and [[(node.path, whole) for node, whole in chosen] for chosen in refreshed] == [
        [(str(source / "資料"), False)]]
    dialog.deleteLater()


def test_a_feed_lost_during_an_operation_that_does_not_withdraw_it_reads_the_root(window, qapp, tmp_path,
                                                                                  monkeypatch):
    _source(window, tmp_path)
    root = window.results.outcome.result.root
    controller = _enable(window, qapp, monkeypatch)
    rescans = []
    monkeypatch.setattr(window, "rescan_folder", rescans.append)
    dialog = QDialog(window)
    window._path_dialogs.add(dialog)
    window.pending_source_workers()
    controller.worker.record(ChangeBatch(full=True, reason="notification_lost"))
    controller.tick()
    assert controller._operation_gap and not controller._pending.full
    window._path_dialogs.remove(dialog)
    controller._since -= 2
    controller.tick()
    assert rescans == [root]
    dialog.deleteLater()


@pytest.mark.parametrize("other_reason", [False, True])
def test_a_delete_shown_in_place_does_not_request_the_whole_root(window, qapp, tmp_path, monkeypatch, other_reason):
    source, root = _source(window, tmp_path)
    controller = _enable(window, qapp, monkeypatch)
    calls = []
    monkeypatch.setattr(window, "rescan_folder", calls.append)
    monkeypatch.setattr(main_window, "confirm_permanent_delete", lambda *_args: QMessageBox.StandardButton.Yes)
    if other_reason:  # a whole-root request the operation did not cause is kept
        _dirty(controller, full=True)
    before = controller.worker
    victim = next(child for child in root.children if child.name == "另一個")

    window.delete_permanently([victim])
    assert not before.cancel.is_set() and controller._operating  # the feed keeps reporting
    before.record(ChangeBatch(full=True, reason="notification_lost"))  # its notifications overflowed meanwhile
    controller.tick()
    assert controller._operation_gap
    _wait(qapp, lambda: window._delete_worker is None)

    assert not (source / "另一個").exists() and victim not in root.children and (source / "資料" / "file").exists()
    assert not controller._operation_gap  # the results show the delete: it withdrew that request
    controller.tick()  # captures again what the delete changed
    _wait(qapp, lambda: controller.worker is not before and bool(controller.worker and controller.worker.backend))
    controller._since = time.monotonic() - 2
    controller.tick()
    assert calls == ([root] if other_reason else []) and window.results.refresh_notice.isHidden()


def test_a_followed_folder_refresh_is_not_followed_by_a_whole_root_scan(window, qapp, tmp_path, monkeypatch):
    source, root = _source(window, tmp_path)
    controller = _enable(window, qapp, monkeypatch)
    scans = []
    monkeypatch.setattr(window, "start_scan", lambda path, **_kwargs: scans.append(path))
    _dirty(controller, source / "資料")
    (source / "資料" / "新增.bin").write_bytes(b"owned" * 10)
    controller.tick()
    _wait(qapp, lambda: window._worker is None and not window._analysers and root.size == 4 + 9 + 50)
    assert window.results.outcome.result.root is root and not controller._operation_gap
    _wait(qapp, lambda: controller.worker is not None and bool(controller.worker.backend))
    controller._since = time.monotonic() - 2
    controller.tick()
    assert scans == [] and window._worker is None  # nothing else changed: nothing more is read


def test_a_new_folder_reads_the_folder_holding_it_and_no_timer_reads_the_whole_root(window, qapp, tmp_path,
                                                                                    monkeypatch):
    source, root = _source(window, tmp_path)
    controller = _enable(window, qapp, monkeypatch)
    refreshed, rescanned = [], []
    monkeypatch.setattr(window, "refresh_folders", refreshed.append)
    monkeypatch.setattr(window, "rescan_folder", rescanned.append)
    _dirty(controller, source / "not-captured" / "deeper")
    controller.tick()
    assert refreshed == [[(root, False)]] and not rescanned  # the root's own entries, not the whole scan
    controller._since -= 600
    for _ in range(3):
        controller.tick()
    assert refreshed == [[(root, False)]] and not rescanned
    _dirty(controller, full=True)  # a lost feed: only now is all of it read again
    controller.tick()
    assert rescanned == [root]


def test_feed_error_is_visible_plain_text_without_automatic_retry(window, qapp, tmp_path, monkeypatch):
    _source(window, tmp_path)

    def failed(*_args, **_kwargs):
        raise OSError("owned <unsafe> native limit")

    monkeypatch.setattr(following, "watch_scope", failed)
    monkeypatch.setattr(following, "supported", lambda: True)
    window._actions["follow_changes"].setChecked(True)
    _wait(qapp, lambda: window._follow.worker is not None and bool(window._follow.worker.error))
    calls = []
    monkeypatch.setattr(window, "rescan_folder", calls.append)
    window._follow._merge(ChangeBatch(full=True))
    window._follow.tick()
    assert "owned <unsafe> native limit" in window._follow.label.text()
    assert not calls
    cancelled = window._follow.worker.cancel
    window.close()
    _wait(qapp, lambda: window._close_ready)
    assert cancelled.is_set()
    assert window._follow.worker is None


def test_unrelated_changed_folders_are_read_in_one_refresh(window, qapp, tmp_path, monkeypatch):
    source, _root = _source(window, tmp_path)
    controller = _enable(window, qapp, monkeypatch)
    calls = []
    monkeypatch.setattr(window, "refresh_folders", calls.append)
    _dirty(controller, source / "資料", source / "另一個")
    controller.tick()
    assert len(calls) == 1
    assert {node.path for node, _whole in calls[0]} == {str(source / "資料"), str(source / "另一個")}
    assert not controller._pending.folders


@pytest.mark.parametrize("combined", [False, True])
def test_partial_or_combined_scan_refuses_following_without_native_setup(window, tmp_path, monkeypatch, combined):
    source, _root = _source(window, tmp_path)
    result = scan_roots((str(source / "資料"), str(source / "另一個"))) if combined else scan(source)
    window.results.show_outcome(analyse(result, partial=not combined))
    dialog = QDialog(window)
    window._path_dialogs.add(dialog)

    def forbidden(*_args, **_kwargs):
        pytest.fail("partial scan started a native feed")

    monkeypatch.setattr(following, "watch_scope", forbidden)
    monkeypatch.setattr(following, "captured_scope", forbidden)
    monkeypatch.setattr(following, "supported", lambda: True)
    window._actions["follow_changes"].setChecked(True)
    assert window._follow.worker is None and window._follow._status == "follow_incomplete"
    window._path_dialogs.remove(dialog)
    window._follow._merge(ChangeBatch(full=True))
    window._follow._since -= 2
    monkeypatch.setattr(window, "rescan_folder", lambda _node: pytest.fail("refused scope was rescanned"))
    window._follow.tick()
    dialog.deleteLater()


def test_counted_hard_links_refresh_the_folder_and_recount_the_whole_tree(window, qapp, tmp_path, monkeypatch):
    source, _root = _source(window, tmp_path)
    window._actions["count_hard_links"].setChecked(True)
    os.link(source / "資料" / "file", source / "另一個" / "alias")
    window.results.show_outcome(analyse(scan(source, options=ScanOptions(count_hard_links=True))))
    root = window.results.outcome.result.root
    assert root.size == 17 and root.accounted_size == 13
    controller = _enable(window, qapp, monkeypatch)
    scans = []
    monkeypatch.setattr(window, "start_scan", lambda path, **_kwargs: scans.append(path))
    (source / "資料" / "more").write_bytes(b"x" * 6)
    _dirty(controller, source / "資料")
    controller.tick()
    _wait(qapp, lambda: window._worker is None and not window._analysers and root.size == 23)
    result = window.results.outcome.result
    assert scans == [] and result.root is root and result.hard_links is not None
    assert root.accounted_size == 19 and result.hard_links.aliases == 1  # the alias outside still counts once
    assert (source / "資料" / "file").read_bytes() == b"kept"


def test_tab_close_joins_only_its_monitor_and_pending_state_is_independent(qapp, tmp_path, monkeypatch):
    settings = QSettings(str(tmp_path / "workspace.ini"), QSettings.Format.IniFormat)
    workspace = create_workspace(settings)
    try:
        first = workspace.current
        second = workspace.add_tab()
        first_source, _root = _source(first, tmp_path / "first")
        _source(second, tmp_path / "second")
        first_controller = _enable(first, qapp, monkeypatch)
        second_controller = _enable(second, qapp, monkeypatch)
        _dirty(first_controller, first_source / "資料")
        first_worker, second_worker = first_controller.worker, second_controller.worker
        first_cancelled = first_worker.cancel
        first_finished = QSignalSpy(first_worker.finished)
        assert first_controller._pending.folders and not second_controller._pending.folders
        workspace.close_tab(0)
        _wait(qapp, lambda: workspace.tabs.count() == 1)
        assert first_controller.worker is None
        assert first_cancelled.is_set()
        assert first_finished.count() == 1
        assert second_controller.worker is second_worker and second_worker.isRunning()
        assert not second_worker.cancel.is_set() and not second_controller._pending.folders
    finally:
        workspace.close()
        _wait(qapp, lambda: workspace._close_ready)


@pytest.mark.skipif(not (sys.platform in ("win32", "darwin") or sys.platform.startswith("linux")),
                    reason="native feed platform")
def test_native_event_replaces_one_branch_preserves_other_source_and_joins(window, qapp, tmp_path, monkeypatch):
    if sys.platform == "win32":
        from je_file_tree.core import windows_watch

        # Volume-wide USN changes can legitimately require a full rescan; this case proves branch notifications.
        def unavailable(*_args, **_kwargs):
            raise PermissionError("Native GUI branch test uses recursive directory notifications")

        monkeypatch.setattr(windows_watch, "_watch_usn", unavailable)
    source, root = _source(window, tmp_path)
    untouched = next(child for child in root.children if child.name == "另一個")
    file = source / "另一個" / "untouched"
    proof = file.stat().st_ino, hashlib.sha256(file.read_bytes()).hexdigest()
    old_branch = next(child for child in root.children if child.name == "資料")
    nested = next(child for child in old_branch.children if child.name == "nested")
    assert any(item.node is old_branch for item in window.results.charts.tree.rows())
    window._actions["follow_changes"].setChecked(True)
    _wait(qapp, lambda: window._follow.worker is not None and bool(window._follow.worker.backend))
    worker = window._follow.worker
    if sys.platform == "win32":
        assert worker.backend == "directory_changes"
    finished = QSignalSpy(worker.finished)
    cancelled = worker.cancel
    (source / "資料" / "新增.bin").write_bytes(b"owned event" * 2048)
    _wait(qapp, lambda: root.size == 4 + 9 + 22528 and window._worker is None and not window._analysers)
    assert window.results.outcome.result.root is root and untouched in root.children
    assert (file.stat().st_ino, hashlib.sha256(file.read_bytes()).hexdigest()) == proof
    # Only that folder was read again, in place: it and the subfolder it kept are the same nodes.
    current_branch = next(child for child in root.children if child.name == "資料")
    assert current_branch is old_branch and any(child.name == "新增.bin" for child in current_branch.children)
    assert nested in current_branch.children and nested.parent is current_branch
    assert any(item.node is current_branch for item in window.results.charts.tree.rows())
    # The feed kept reporting while the folder was read; no folder changed, so it simply carries on.
    assert window._follow.worker is worker and not cancelled.is_set() and finished.count() == 0
    active = window._follow.worker
    assert active is not None
    active_cancelled = active.cancel
    active_finished = QSignalSpy(active.finished)
    window.close()
    _wait(qapp, lambda: window._close_ready)
    assert active_finished.count() == 1
    assert active_cancelled.is_set()


def test_a_change_directly_in_the_root_reads_only_its_own_entries(window, qapp, tmp_path, monkeypatch):
    source, root = _source(window, tmp_path)
    controller = _enable(window, qapp, monkeypatch)
    scans = []
    monkeypatch.setattr(window, "start_scan", lambda path, **_kwargs: scans.append(path))
    kept = {child.name: child for child in root.children}
    feed = controller.worker
    (source / "另一個" / "untouched").write_bytes(b"not read again")  # inside a kept subfolder
    (source / "新檔案").write_bytes(b"n" * 7)
    _dirty(controller, source)
    controller.tick()
    _wait(qapp, lambda: window._worker is None and not window._analysers and root.size == 4 + 9 + 7)
    assert scans == [] and window.results.outcome.result.root is root
    assert controller.worker is feed and not feed.cancel.is_set() and not controller._capture  # no folder changed
    assert all(next(child for child in root.children if child.name == name) is node for name, node in kept.items())
    assert next(child for child in kept["另一個"].children).size == 9  # what it holds was kept, not read


def test_the_feed_keeps_reporting_while_a_folder_is_read_and_hands_over_after(window, qapp, tmp_path, monkeypatch):
    source, root = _source(window, tmp_path)
    controller = _enable(window, qapp, monkeypatch)
    before = controller.worker
    (source / "資料" / "新增.bin").write_bytes(b"x" * 3)
    (source / "資料" / "新資料夾").mkdir()  # a new folder: the scope is captured again and a new feed takes over
    _dirty(controller, source / "資料")
    controller.tick()
    assert window._worker is not None and before.isRunning() and not before.cancel.is_set()
    before.record(ChangeBatch((str(source / "另一個"),)))  # reported while the folder was being read
    (source / "另一個" / "later").write_bytes(b"y" * 5)
    _wait(qapp, lambda: controller.worker is not before and bool(controller.worker.backend))
    _wait(qapp, lambda: window._worker is None and not window._analysers)
    controller.tick()
    assert before.cancel.is_set()
    controller._since -= 2
    controller.tick()
    _wait(qapp, lambda: window._worker is None and not window._analysers and root.size == 4 + 3 + 9 + 5)


def test_a_folder_removed_before_it_is_read_reads_the_folder_that_held_it(window, qapp, tmp_path, monkeypatch):
    source, root = _source(window, tmp_path)
    controller = _enable(window, qapp, monkeypatch)
    nested = next(child for child in root.children if child.name == "資料").children
    nested = next(child for child in nested if child.name == "nested")
    (source / "資料" / "nested").rmdir()
    window.refresh_folders([(nested, False)])
    _wait(qapp, lambda: window._worker is None and not window._analysers)
    assert controller._pending.folders == (str(source / "資料"),)


def test_a_removed_folder_whose_folder_was_read_too_asks_for_nothing_more(window, qapp, tmp_path, monkeypatch):
    source, root = _source(window, tmp_path)
    controller = _enable(window, qapp, monkeypatch)
    branch = next(child for child in root.children if child.name == "資料")
    nested = next(child for child in branch.children if child.name == "nested")
    (source / "資料" / "nested").rmdir()
    window.refresh_folders([(branch, False), (nested, False)])
    _wait(qapp, lambda: window._worker is None and not window._analysers)
    assert nested not in branch.children and not controller._pending.folders


def test_an_inotify_feed_reads_the_folders_it_watches_newly_once_armed(window, qapp, tmp_path, monkeypatch):
    source, _root = _source(window, tmp_path)

    def watch(_scope, _changed, cancel, *, ready, **_feed):
        ready("inotify")
        cancel.wait()

    monkeypatch.setattr(following, "watch_scope", watch)
    monkeypatch.setattr(following, "supported", lambda: True)
    window._actions["follow_changes"].setChecked(True)
    controller = window._follow
    _wait(qapp, lambda: controller.worker is not None and bool(controller.worker.backend))
    before = controller.worker
    (source / "資料" / "新資料夾").mkdir()
    _dirty(controller, source / "資料")
    controller.tick()
    _wait(qapp, lambda: controller.worker is not before and bool(controller.worker.backend)
          and window._worker is None)
    controller.tick()  # armed: the old feed is retired
    # It watched nothing there before it was armed: that folder is read again, in case it changed meanwhile.
    assert controller._previous is None and controller._pending.folders == (str(source / "資料" / "新資料夾"),)
