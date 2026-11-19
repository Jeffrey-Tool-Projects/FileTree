"""Read again only the folders Follow changes found changed, and put them in place in the results.

Each folder's own entries are listed again and its subfolders are kept (``core/refresh.py``), so a
change directly in the scanned folder reads that one folder, not the whole scan. A folder reported
whole (too many changes below it) is read entirely. The worker stands in for a scan worker: while it
runs, everything that waits for a scan waits for it.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject

from je_file_tree.core.formatting import format_count
from je_file_tree.core.node import Node
from je_file_tree.core.refresh import kept_subfolders
from je_file_tree.core.scanner import ScanCancelledError, ScanOptions, ScanResult, scan
from je_file_tree.core.snapshot import unpack_snapshot
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.scan_worker import ScanWorker
from je_file_tree.gui.worker_lifecycle import after_threads, queue_worker

if TYPE_CHECKING:
    from je_file_tree.gui.main_window import MainWindow

STATUS_TIMEOUT_MS = 8000

Plan = tuple[str, frozenset[tuple[str, int, int]]]  # a folder and the subfolders its listing keeps


class ListingWorker(ScanWorker):
    """Lists each planned folder; ``succeeded`` carries one ``ScanResult`` per plan, None for a folder gone."""

    def __init__(self, plans: tuple[Plan, ...], options: ScanOptions, parent: QObject | None = None) -> None:
        super().__init__(plans[0][0], options, parent)
        self.plans = plans
        self.linked = False  # a file listed has another name: the feed's scope must be captured again

    def _run_scan(self) -> None:
        results: list[ScanResult | None] = []
        for path, keep in self.plans:
            if self._cancel.is_set():
                self.cancelled.emit(None)
                return
            try:
                result = scan(path, options=replace(self._options, keep=keep), cancel=self._cancel, pause=self._pause)
                self.linked = self.linked or _has_links(result.root)
                results.append(result)
            except NotADirectoryError:
                results.append(None)  # removed meanwhile: the folder holding it shows that
            except ScanCancelledError:
                self.cancelled.emit(None)
                return
        self._scanning = False
        self.succeeded.emit(tuple(results))


def _has_links(folder: Node) -> bool:
    return any(not child.is_dir and child.snapshot is not None and unpack_snapshot(child.snapshot).links > 1
               for child in folder.iter_nodes() if child is not folder)


def _subfolders(node: Node) -> set[tuple[str, tuple[int, int] | None]]:
    return {(child.name, None if child.snapshot is None else unpack_snapshot(child.snapshot).identity)
            for child in node.children if child.is_dir}


def refresh_folders(window: MainWindow, chosen: list[tuple[Node, bool]]) -> None:
    """Read ``chosen`` again on a worker: each folder's own entries, or all of it when its flag is set."""
    outcome = window.results.outcome
    if window._worker is not None or window.operation_busy or outcome is None or not chosen:
        return
    root = outcome.result.root
    if ((outcome.result.hard_links is not None) != window._actions["count_hard_links"].isChecked()
            or any(whole and node is root for node, whole in chosen)):
        window.rescan_folder(root)  # only a whole scan counts every hard link again
        return
    paused = window._background_pause(wait=False) if window._background_pause is not None else ()
    window._undo.expire()
    window._analyser = None
    plans = tuple((node.path, frozenset() if whole else kept_subfolders(node)) for node, whole in chosen)
    # Listed, never taken from the file table, which can be a few seconds behind; hard links are counted
    # again over the whole tree afterwards, as after a folder rescan.
    options = replace(window._scan_options(), mft=False, count_hard_links=False)
    worker = ListingWorker(plans, options, window)
    before = [_subfolders(node) for node, _whole in chosen]
    worker.succeeded.connect(lambda results: window._is_current(worker) and _refreshed(
        window, chosen, results, before=before, linked=worker.linked))
    worker.failed.connect(lambda reason: window._is_current(worker) and _ended(window, tr("follow_refresh_failed",
                                                                                        reason=reason)))
    worker.cancelled.connect(lambda _outcome: window._is_current(worker) and _ended(window, tr("scan_cancelled")))
    worker.finished.connect(lambda: after_threads((worker,), lambda: window._release_scan(worker), window))
    window._worker = worker
    window.scan_activity_changed.emit()
    window._scan_workers.add(worker)
    window._update_actions()
    queue_worker(worker, lambda: not window._closing and window._worker is worker and not worker._cancel.is_set(),
                 window, lambda: _discarded(window, worker), readers=paused)


def _refreshed(window: MainWindow, chosen: list[tuple[Node, bool]], results: tuple[ScanResult | None, ...], *,
               before: list[set[tuple[str, tuple[int, int] | None]]], linked: bool) -> None:
    window._scan_ended()
    listings = [(node, result) for (node, _whole), result in zip(chosen, results, strict=True) if result is not None]
    follow = window._follow
    for (node, _whole), result in zip(chosen, results, strict=True):
        if result is None:
            follow.request(node.parent.path if node.parent is not None else None)
    failed = window.results.refill_folders(listings)
    for node in failed:
        follow.request(node.path, whole=True)  # a kept subfolder was replaced meanwhile: read it all
    # The feed's scope holds every folder and every file with another name: capture it again only when
    # a listing found, lost or replaced a subfolder, or listed such a file. Otherwise the feed carries on.
    structural = linked or bool(failed) or len(listings) != len(chosen) or any(
        whole or _subfolders(node) != folders for (node, whole), folders in zip(chosen, before, strict=True))
    window._update_actions()
    root = window.results.tree_model.root
    if root is not None and window.results.outcome is not None:
        window._start_analysis(root, with_capacity=True, count=window.results.outcome.result.hard_links is not None)
        follow.refreshed(root, structural=structural)
    window.statusBar().showMessage(tr("follow_refreshed", count=format_count(len(listings))), STATUS_TIMEOUT_MS)


def _ended(window: MainWindow, message: str) -> None:
    window._scan_ended()
    window._update_actions()
    window.statusBar().showMessage(message, STATUS_TIMEOUT_MS)


def _discarded(window: MainWindow, worker: ListingWorker) -> None:
    if worker is window._worker:
        if window._closing:
            window._worker = None
            window.scan_activity_changed.emit()
        else:
            _ended(window, tr("scan_cancelled"))
    window._release_scan(worker)
