"""Default-off per-tab native following; bounded metadata events only request fresh listings.

A change reads again only the folder whose own entries changed (``core/refresh.py``): its subfolders
are kept, so a file saved directly in the scanned folder never reads the whole scan again. The native
feed keeps running while that folder is read; the scope is captured again afterwards and a new feed
takes over only once it is armed, an NTFS journal feed reading on from where the refresh began, so
nothing that happens meanwhile goes unseen. Only a lost or overflowing feed reads the whole root again.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QThread, Qt, QTimer
from PySide6.QtWidgets import QApplication, QLabel

from je_file_tree.core.change_watch import (
    ChangeBatch, Position, WatchScope, captured_scope, changed, merged, watch_scope,
)
from je_file_tree.core.node import Node, folder_holding
from je_file_tree.core.scanner import EXCLUDED
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.scan_worker import wait_for
from je_file_tree.gui.worker_lifecycle import after_threads, queue_worker

if TYPE_CHECKING:
    from je_file_tree.gui.main_window import MainWindow

ENABLED_KEY = "follow_changes"
COALESCE_SECONDS = 0.5  # changes this close together are read in one go; analysing after each also spaces them
TICK_MS = 250


def supported() -> bool:
    """Native change feeds: NTFS journal or directory notifications, inotify, FSEvents."""
    return sys.platform in ("win32", "darwin") or sys.platform.startswith("linux")


class CaptureWorker(QThread):
    """Read the tree once for a feed's scope. It reads the tree, so scans and operations wait for it."""

    def __init__(self, root: Node, parent: QObject) -> None:
        super().__init__(parent)
        self.root = root
        self.cancel = threading.Event()
        self.scope: WatchScope | None = None
        self.error = ""

    def run(self) -> None:
        """Capture off the GUI thread; errors stay visible on the controller."""
        try:
            self.scope = captured_scope(self.root, self.cancel)
        except (OSError, ValueError, UnicodeError) as error:
            self.error = str(error)


class ChangeWorker(QThread):
    """One native feed over a captured scope, retaining at most one bounded dirty batch.

    It never reads the tree, so a folder is read again while it runs. That is why it has no Qt parent:
    ``queue_worker`` waits for every thread a window holds. Its controller keeps it until it joins.
    """

    def __init__(self, scope: WatchScope, since: Position | None = None) -> None:
        super().__init__()
        self.scope, self.since = scope, since
        self.cancel = threading.Event()
        self.backend, self.error = "", ""
        self.position: Position | None = None
        self._lock = threading.Lock()
        self._batch = ChangeBatch()

    def record(self, batch: ChangeBatch) -> None:
        """Coalesce at the producer; event storms cannot create an unbounded Qt signal queue."""
        with self._lock:
            self._batch = merged(self._batch, batch)

    def take(self) -> ChangeBatch:
        """Transfer pending metadata once under the producer lock."""
        with self._lock:
            result, self._batch = self._batch, ChangeBatch()
        return result

    def run(self) -> None:
        """Retain native setup/errors until the owning controller cancels and joins this worker."""
        try:
            watch_scope(self.scope, self.record, self.cancel, ready=self._initialized, since=self.since,
                        moved=self._moved)
        except (OSError, ValueError, UnicodeError) as error:
            self.error = str(error)

    def _initialized(self, backend: str) -> None:
        self.backend = backend

    def _moved(self, position: Position) -> None:
        self.position = position


def targets(root: Node, batch: ChangeBatch) -> list[tuple[Node, bool]]:
    """The scanned folders to read again for ``batch``, each with whether to read it whole.

    A reported path maps to the deepest folder scanned there; one below it is new, and that folder's
    listing reads it whole. Folders inside one read whole, and excluded folders, are left out.
    """
    found: dict[Node, bool] = {}
    for path, whole in (*((path, False) for path in batch.folders), *((path, True) for path in batch.trees)):
        node = folder_holding(root, path)
        if node is None or node.error == EXCLUDED or node.path is None:
            continue
        exact = os.path.normcase(node.path) == os.path.normcase(os.path.normpath(path))
        found[node] = found.get(node, False) or (whole and exact)
    whole_ones = {node for node, whole in found.items() if whole}

    def covered(node: Node) -> bool:
        above = node.parent
        while above is not None:
            if above in whole_ones:
                return True
            above = above.parent
        return False

    chosen = [(node, whole) for node, whole in found.items() if not covered(node)]
    return sorted(chosen, key=lambda item: item[0].depth)


class FollowChanges(QObject):
    """Own one tab's feed, defer busy work and hand over between feeds without a gap."""

    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window = window
        self.worker: ChangeWorker | None = None
        self._previous: ChangeWorker | None = None  # the feed before ``worker``, until that one is armed
        self._capture: CaptureWorker | None = None
        self.root: Node | None = None
        self.enabled, self._closing = False, False
        self._pending = ChangeBatch()
        self._operation_gap = False  # a feed was lost during a source operation: read the whole root again
        self._operating = False  # a source operation runs (``quiesce``): a lost feed counts as its gap
        self._stale = False  # the scope was not captured again since an operation: capture it when idle
        self._handoff: Position | None = None  # where the next journal feed reads on from
        self._since = 0.0
        self._status, self._detail = "follow_waiting", ""
        self._retiring: set[QThread] = set()
        self.label = QLabel(window)
        self.label.setTextFormat(Qt.TextFormat.PlainText)
        self.label.setMaximumWidth(300)
        self.label.hide()
        window.statusBar().addPermanentWidget(self.label)
        self.timer = QTimer(self)
        self.timer.setInterval(TICK_MS)
        self.timer.timeout.connect(self.tick)

    def configure(self, enabled: bool) -> None:
        """Persist the default-off preference; cancel old readers and retire them asynchronously."""
        self.window.settings.setValue(ENABLED_KEY, enabled)
        self.enabled = enabled
        self.stop(clear=True)
        self.label.setVisible(enabled)
        if enabled and not self._closing:
            self.timer.start()
            outcome = self.window.results.outcome
            if (outcome is not None and self.window.operation_busy
                    and outcome.result.root.path is not None and not outcome.partial):
                self.root = outcome.result.root
                self._merge(ChangeBatch(full=True, reason="source_operation"))
                self._set_status("follow_waiting")
            elif outcome is not None and self.window._worker is None:
                self.adopt(outcome.result.root)
            else:
                self._set_status("follow_waiting")
        else:
            self.timer.stop()

    def adopt(self, root: Node) -> None:
        """Follow ``root``: capture its scope again; a feed already following it reports on meanwhile."""
        if root is not self.root or self.worker is None or self.worker.error:
            self.stop()
        self.root = root
        if not self.enabled or self._closing:
            return
        if not supported():
            self._set_status("follow_unsupported")
            return
        outcome = self.window.results.outcome
        if root.path is None or outcome is None or outcome.partial:
            self.stop()
            self._set_status("follow_incomplete")
            return
        if self._capture is not None:
            self._retire(self._capture)
        if self.worker is None:
            self._set_status("follow_starting")
        capture = CaptureWorker(root, self)
        self._capture = capture
        capture.finished.connect(lambda: self._captured(capture))
        queue_worker(capture, lambda: self._capture is capture and not self._closing
                     and not self.window._closing and not capture.cancel.is_set(), self)

    def _captured(self, capture: CaptureWorker) -> None:
        if capture is not self._capture:
            return
        self._capture = None
        cancelled = capture.cancel.is_set()
        self._retire(capture)  # joined already: this only releases it
        if cancelled or self._closing or not self.enabled or capture.root is not self.root:
            return
        if capture.error:
            self.stop()
            self._set_status("follow_failed", capture.error)
            return
        if capture.scope is not None and capture.scope.folders:
            self._arm(capture.scope)

    def _arm(self, scope: WatchScope) -> None:
        """Start a feed over ``scope``: beside the running one, which it then replaces, else after the old ones join."""
        if self._previous is not None:
            self._retire(self._previous)
        # Without an agreed place to read on from, take the running feed's: what it has not polled yet is not lost.
        feed = ChangeWorker(scope, self._handoff or self._position())
        self._previous, self.worker = self.worker, feed
        self._handoff = None
        if self._previous is not None:
            feed.start()
            return
        stopped = tuple(worker for worker in self._retiring if isinstance(worker, ChangeWorker))
        queue_worker(feed, lambda: self.worker is feed and not self._closing and not feed.cancel.is_set(), self,
                     readers=stopped)

    def refreshed(self, root: Node, *, structural: bool) -> None:
        """Folders of ``root`` were read again: capture the scope again if their subfolders changed.

        Otherwise the running feed's scope still holds every folder, and it saw everything since the
        refresh began, so it simply carries on.
        """
        if structural or self._capture is not None or self.worker is None or self.root is not root:
            self.adopt(root)
        else:
            self._handoff = None

    def hold(self) -> None:
        """A folder is about to be read again: the next journal feed reads on from here."""
        if self._handoff is None:
            self._handoff = self._position()

    def _position(self) -> Position | None:
        known = [feed.position for feed in (self._previous, self.worker) if feed is not None and feed.position]
        return min(known) if known else None

    def _retire(self, worker: CaptureWorker | ChangeWorker, then: Callable[[], None] | None = None) -> None:
        """Cancel ``worker`` and keep it until it joins; a feed's last batch is kept for the same root."""
        worker.cancel.set()
        root = self.root
        self._retiring.add(worker)

        def joined() -> None:
            self._retiring.discard(worker)
            if isinstance(worker, ChangeWorker) and not self._closing and self.root is root and root is not None:
                self._merge(worker.take())
            worker.deleteLater()
            if then is not None:
                then()

        after_threads((worker,), joined, self)

    def stop(self, *, clear: bool = False, wait: bool = False) -> tuple[QThread, ...]:
        """Cancel the capture and every feed; join through the GUI's shared gate unless ``wait``."""
        for worker in (self._capture, self._previous, self.worker):
            if worker is not None:
                self._retire(worker)
        self._capture = self._previous = self.worker = None
        if clear:
            self.root = None
            self._pending, self._since = ChangeBatch(), 0.0
            self._operation_gap = self._operating = self._stale = False
            self._handoff = None
        retiring = tuple(self._retiring)
        if wait:
            for pending in retiring:
                wait_for(pending)
        return retiring

    def quiesce(self, *, wait: bool = True) -> tuple[QThread, ...]:
        """Stop reading the tree before a source operation changes it; the feed keeps reporting.

        Only the capture reads the tree, so only it is stopped (the operation waits for what this
        returns); it runs again once the operation is over, which may have added or removed folders.
        The feed reads none of the tree and holds no handle that keeps an entry from being moved or
        removed, so what the operation and any other program change meanwhile is reported and read
        again afterwards: no gap is left, and nothing asks for the whole root (U-20261120-03).
        """
        capture, self._capture = self._capture, None
        if capture is not None:
            self._retire(capture)
        self._operating = self._stale = True
        retiring = tuple(worker for worker in self._retiring if isinstance(worker, CaptureWorker))
        if wait:
            for pending in retiring:
                wait_for(pending)
        return retiring

    def resume(self) -> None:
        """Follow on after an operation whose changes the results already show or have on offer.

        A move to the Recycle Bin, a permanent delete or an Undo can report so many changes that a
        directory-notification feed overflows; the results show those entries already, so a whole-root
        request that arrived during it is withdrawn. Folders reported meanwhile are still read again.
        """
        self._operation_gap = self._operating = False
        root = self.root
        if (self.enabled and not self._closing and root is not None and self.worker is None
                and self._capture is None):
            self.adopt(root)

    def request(self, path: str | None, *, whole: bool = False) -> None:
        """Read ``path`` again later (the whole root for None), as if its feed had reported it."""
        if path is None:
            self._merge(ChangeBatch(full=True, reason="root_changed"))
        else:
            self._merge(ChangeBatch(trees=(path,)) if whole else ChangeBatch((path,)))

    def shutdown(self, *, wait: bool = True) -> None:
        """Prevent late replies and join all native work before the tab is destroyed."""
        self._closing = True
        self.timer.stop()
        self.stop(clear=True, wait=wait)

    def _merge(self, batch: ChangeBatch) -> None:
        if not batch.folders and not batch.trees and not batch.full:
            return
        if batch.full and self._operating:  # lost while a source operation ran: its gap, which it may withdraw
            self._operation_gap = True
            if not self._pending.full and not self._pending.folders and not self._pending.trees:
                self._since = time.monotonic()
            batch = ChangeBatch(batch.folders, trees=batch.trees)
            if not batch.folders and not batch.trees:
                return
        pending = self._pending
        if not pending.full and not pending.folders and not pending.trees:
            self._since = time.monotonic()
        self._pending = merged(pending, batch)

    def tick(self) -> None:
        """Poll bounded events four times a second and avoid scans during reviews, Undo offers or analysis."""
        if not self.enabled or self._closing or self.window._closing:
            return
        for feed in (self._previous, self.worker):
            if feed is not None:
                self._merge(feed.take())
        worker = self.worker
        if worker is not None:
            if worker.error and self._previous is not None and not self._previous.error:
                self._arm_alone(worker)
            elif worker.error:
                self._set_status("follow_failed", worker.error)
                return
            elif worker.backend:
                if self._previous is not None:
                    self._handed_over(self._previous, worker)
                self._set_status("follow_active", worker.backend)
        if (self._stale and self.root is not None and not self.window.operation_busy
                and self.window._worker is None):
            self._stale = False
            self.adopt(self.root)  # capture again what the operation may have changed
        if self.window._trash_rescans:
            self.window._rescan_after_trash()  # folders left on offer before following was turned on
        self._flush()

    def _handed_over(self, previous: ChangeWorker, worker: ChangeWorker) -> None:
        """``worker`` is armed: retire ``previous``.

        An inotify feed watches a folder only once it is armed, so the folders it watches that
        ``previous`` did not are read again, which shows what changed in them meanwhile. A journal feed
        reads on from the held position, and directory notifications watch the whole root anyway.
        """
        self._previous = None
        self._retire(previous)
        if worker.backend == "inotify":
            known = {folder.path for folder in previous.scope.folders}
            self._merge(changed({folder.path for folder in worker.scope.folders if folder.path not in known}))

    def _arm_alone(self, failed: ChangeWorker) -> None:
        """The new feed could not run beside the old one (an inotify watch limit): stop that one first."""
        previous, root = self._previous, self.root
        self._previous = self.worker = None
        self._retire(failed)
        if previous is None:
            return
        self.hold()

        def rearm() -> None:
            if self.enabled and not self._closing and self.root is root and self.worker is None:
                self._arm(failed.scope)

        self._retire(previous, rearm)

    def _flush(self) -> None:
        window = self.window
        if (window._worker is not None or window.operation_busy or window._analysers
                or window._undo.available or window._trash_rescans or QApplication.activeModalWidget() is not None
                or time.monotonic() - self._since < COALESCE_SECONDS):
            return
        outcome = window.results.outcome
        if (self.root is None or self.root.path is None or outcome is None
                or outcome.partial or outcome.result.root is not self.root):
            return
        batch = self._pending
        self._operating = False  # whatever operation ran is over: a feed lost during it reads the whole root
        if batch.full or self._operation_gap:
            self._pending, self._operation_gap = ChangeBatch(), False
            window.rescan_folder(self.root)
            return
        worker = self.worker
        if not batch.folders and not batch.trees or worker is None or not worker.backend or worker.error:
            return
        self._pending = ChangeBatch()
        chosen = targets(self.root, batch)
        if chosen:
            self.hold()
            window.refresh_folders(chosen)

    def _set_status(self, key: str, detail: str = "") -> None:
        if (key, detail) == (self._status, self._detail) and self.label.text():
            return
        self._status, self._detail = key, detail
        self.retranslate()

    def retranslate(self) -> None:
        """Show plain-text feed status/errors in the current interface language."""
        detail = tr("follow_backend_" + self._detail) if self._status == "follow_active" else self._detail
        self.label.setText(tr(self._status, detail=detail))
        self.label.setToolTip(self.label.text())
