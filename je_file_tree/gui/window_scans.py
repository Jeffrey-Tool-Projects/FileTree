"""Choosing folders, starting, stopping and repeating scans, and the settings they use."""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import replace

from PySide6.QtCore import QSignalBlocker, QTimer
from PySide6.QtWidgets import QDialog, QFileDialog, QInputDialog, QMessageBox

from je_file_tree.core.analysis import Summary
from je_file_tree.core.formatting import format_size
from je_file_tree.core.hard_links import HardLinkPlan
from je_file_tree.core.node import Node, outermost
from je_file_tree.core.scanner import DEFAULT_WORKERS, ScanOptions
from je_file_tree.gui import folder_refresh
from je_file_tree.gui.elevation_dialog import ElevationDialog
from je_file_tree.gui.folder_budget_store import display_error
from je_file_tree.gui.history import configured_history
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.multi_scan import MultiScanDialog
from je_file_tree.gui.reasons import problem_text
from je_file_tree.gui.scan_preferences import MAX_SCAN_WORKERS as _MAX_SCAN_WORKERS, SCAN_FLAGS, ScanDefaults
from je_file_tree.gui.scan_presets import ScanPreset
from je_file_tree.gui.scan_worker import AnalyseWorker, CountWorker, ScanOutcome, ScanWorker, wait_for
from je_file_tree.gui.startup_state import WorkspaceState
from je_file_tree.gui.window_settings import (
    EXCLUSIONS_KEY,
    RESULTS_PAGE,
    SCAN_WORKERS_KEY,
    STATUS_TIMEOUT_MS,
    WELCOME_PAGE,
    read_workers,
)
from je_file_tree.gui.worker_lifecycle import after_threads, queue_worker


class ScanControls:
    """Part of ``MainWindow``: choosing folders, starting, stopping and repeating scans, and the settings they use."""

    def start_scan(self, path: str, *, exact_allocation: bool = False) -> None:
        """Scan ``path`` (stopping a scan already running)."""
        if self.operation_busy or self._path_dialogs or self._closing:
            return
        self._undo.expire()
        self._forget_changed()
        path = os.path.abspath(os.path.expanduser(path.strip().strip('"')))
        self._begin_scan(path, exact_allocation=exact_allocation)

    def start_scan_roots(self, paths: tuple[str, ...], *, exact_allocation: bool = False) -> None:
        """Scan an immutable explicit root list; the virtual root never acquires source authority."""
        if self.operation_busy or self._closing or not paths:
            return
        self._begin_scan(tuple(paths), exact_allocation=exact_allocation)

    def capture_scan_scope(self) -> str | tuple[str, ...] | None:
        """Return next-scan input independently of roots belonging to existing results."""
        return self._prepared_scope

    def capture_restart_scope(self) -> str | tuple[str, ...] | None:
        """Prefer explicit next input, including blank; retain result scopes for untouched integrations."""
        if self._has_prepared_scope:
            return self.capture_scan_scope()
        return self._last_roots or self._last_path or None

    def prepare_scan_scope(self, scope: str | tuple[str, ...] | None,
                           errors: tuple[str, ...] = ()) -> None:
        """Stage exact inputs without scanning or changing existing results."""
        if self._prepared_errors:
            self.statusBar().clearMessage()
        self._prepared_scope, self._prepared_errors = scope, errors
        self._has_prepared_scope = True
        self._render_scan_scope()
        self.scan_scope_changed.emit()
        if errors:
            self.statusBar().showMessage("\n".join(errors))

    def _render_scan_scope(self) -> None:
        scope = self.capture_scan_scope()
        self.path_edit.blockSignals(True)
        self.path_edit.setText(tr("multi_roots") if isinstance(scope, tuple) else scope or "")
        self.path_edit.blockSignals(False)
        roots = scope if isinstance(scope, tuple) else (scope,) if scope else ()
        self.path_edit.setToolTip("\n".join((*roots, *self._prepared_errors)))
        self._update_path_button()

    def _path_input_changed(self) -> None:
        if self._prepared_errors:
            self.statusBar().clearMessage()
        self._has_prepared_scope = True
        self._prepared_scope = self.path_edit.text().strip() or None
        self._prepared_errors = ()
        self._update_path_button()

    def start_prepared_scan(self) -> None:
        """Start the exact staged single or combined scope only on explicit request."""
        scope = self.capture_scan_scope()
        if self._prepared_errors or scope is None:
            return
        if isinstance(scope, tuple):
            self.start_scan_roots(scope)
        else:
            self.start_scan(scope)

    def scan_all_drives(self) -> None:
        """Capture the currently ready mounted roots once; discovery does not grant mutation authority."""
        self.start_scan_roots(tuple(volume.root for volume in self.welcome.drive_rows))

    def choose_roots(self) -> None:
        """Start a combined scan only after accepting an owned explicit-folder list."""
        if self.operation_busy or self._closing:
            return
        dialog = MultiScanDialog(self)
        self._path_dialogs.add(dialog)
        self._update_actions()
        roots = ()
        try:
            if dialog.exec() == QDialog.DialogCode.Accepted:
                roots = dialog.roots
        finally:
            dialog.shutdown()
            self._path_dialogs.discard(dialog)
            self._update_actions()
            dialog.deleteLater()
        if roots:
            self.start_scan_roots(roots)

    def _begin_scan(self, path: str | tuple[str, ...], *, exact_allocation: bool = False) -> None:
        self._folder_drops.cancel()
        background = self._background_pause(wait=False) if self._background_pause is not None else ()
        following = self._follow.stop(clear=True, wait=False)
        self._undo.expire()
        self._forget_changed()
        previous = self._worker
        if previous is not None:
            previous.cancel()
            if previous is self._pending_scan:
                previous.deleteLater()
        self._bin_labels.stop()
        self._analyser = None
        self._last_roots = path if isinstance(path, tuple) else ()
        self._last_path = path if isinstance(path, str) else ""
        self.prepare_scan_scope(path)
        ticket = None
        if self._budget_store is not None:
            try:
                ticket = self._budget_store.ticket()
            except (OSError, ValueError) as error:
                self.statusBar().showMessage(tr("budget_save_error", reason=display_error(str(error))))
        worker = ScanWorker(path, self._scan_options(exact_allocation=exact_allocation), self,
                            history=configured_history(self.settings), budget_ticket=ticket)
        # Signals of a worker that was replaced (a new scan started while it was
        # stopping) arrive late and must not touch the window any more.
        worker.started.connect(lambda root: self._is_current(worker) and self.results.show_live_root(root))
        worker.progressed.connect(
            lambda progress: self._is_current(worker) and self.results.show_progress(progress))
        worker.succeeded.connect(lambda outcome: self._is_current(worker) and self._scan_succeeded(outcome))
        worker.failed.connect(lambda reason: self._is_current(worker) and self._scan_failed(reason))
        worker.cancelled.connect(lambda outcome: self._is_current(worker) and self._scan_cancelled(outcome))
        worker.analysing.connect(lambda: self._is_current(worker) and self.results.scan_bar.analysing())
        worker.history_failed.connect(lambda reason: self._is_current(worker) and not self._closing
                                      and self.statusBar().showMessage(tr("history_save_failed", reason=reason)))
        worker.finished.connect(lambda: after_threads((worker,), lambda: self._release_scan(worker), self))
        self._worker = worker
        self._pending_scan = worker
        self.results.begin_scan()
        self.scan_activity_changed.emit()
        self.pages.setCurrentIndex(RESULTS_PAGE)
        self._leave_path_box()
        self._update_actions()
        self._live_timer.start()
        after_threads((*self._scan_workers, *background, *following), lambda: self._dispatch_scan(worker), self)

    def _leave_path_box(self) -> None:
        """Move keyboard focus from the path box (or the start page) to the results of a new scan.

        Focus stayed in the path box after Enter started a scan, so a later Enter meant for the chart
        or the tree scanned the whole root again and Backspace edited the path (U-20261119-01).
        """
        focused = self.focusWidget()  # the window's own focus, also while another program is active
        if (focused is None or focused is self.path_edit or focused is self._scan_path
                or self.welcome.isAncestorOf(focused)):
            self.results.focus_results()

    def _dispatch_scan(self, worker: ScanWorker) -> None:
        if self._closing or worker is not self._worker or worker is not self._pending_scan:
            return
        if self._background_pause is not None:
            self._background_pause()
        self._pending_scan = None
        self._scan_workers.add(worker)
        worker.start()

    def _release_scan(self, worker: ScanWorker) -> None:
        if self._closing and self._worker is worker:
            self._worker = None
            self.scan_activity_changed.emit()
        self._scan_workers.discard(worker)
        worker.deleteLater()

    def stop_scan(self, *, wait: bool = False) -> None:
        """Ask the running scan (if any) to stop; with ``wait``, until it has."""
        worker = self._worker
        if worker is None:
            if self._undo.busy:
                self._undo.worker.cancel()
            elif self._trash_worker is not None:
                self._trash_worker.cancel()
            elif self._delete_worker is not None:
                self._delete_worker.cancel()
            return
        worker.cancel()
        self.results.scan_bar.stopping()
        if worker is self._pending_scan:
            self._pending_scan = self._worker = None
            self.scan_activity_changed.emit()
            worker.deleteLater()
            self._live_timer.stop()
            self._back_from_scan()
            return
        if wait:
            wait_for(worker)
            self._worker = None
            self.scan_activity_changed.emit()
            self._live_timer.stop()

    def _is_current(self, worker: ScanWorker) -> bool:
        return not self._closing and worker is self._worker

    def pause_scan(self, paused: bool) -> None:
        """Pause or resume the current folder scan while live refreshes keep running."""
        if self._worker is not None and not self._worker.set_paused(paused):
            self.results.scan_bar.analysing()

    def rescan(self) -> None:
        """Scan the last folder again."""
        if self._last_roots:
            self.start_scan_roots(self._last_roots)
        elif self._last_path:
            self.start_scan(self._last_path)

    def _scan_succeeded(self, outcome: ScanOutcome) -> None:
        self._scan_ended()
        if self._budget_store is not None and outcome.budget_batch is not None:
            try:
                self._budget_store.publish(outcome.budget_batch)
            except (OSError, ValueError) as error:
                self.statusBar().showMessage(tr("budget_save_error", reason=display_error(str(error))))
        self.results.show_outcome(outcome)
        self.scan_activity_changed.emit()
        self.pages.setCurrentIndex(RESULTS_PAGE)
        root = outcome.result.root
        for source in root.children if root.path is None else (root,):
            if source.snapshot is not None:
                self._remember(source.path)
        self._update_actions()

        if outcome.result.warnings:
            self.statusBar().showMessage(tr("scan_priority_warning", reason="; ".join(
                problem_text(reason) for reason in outcome.result.warnings)))
        self._follow.adopt(root)

    def _scan_failed(self, reason: str) -> None:
        self._scan_ended()
        self._back_from_scan()
        path = tr("multi_roots") if self._last_roots else self._last_path
        QMessageBox.warning(self, tr("scan_failed_title"), tr("scan_failed", path=path, reason=reason))

    def _scan_cancelled(self, outcome: ScanOutcome | None) -> None:
        self._scan_ended()
        if outcome is None:
            self._back_from_scan()
            self.statusBar().showMessage(tr("scan_cancelled"), STATUS_TIMEOUT_MS)
            return
        self.results.show_outcome(outcome)
        self.scan_activity_changed.emit()
        self._update_actions()
        self.statusBar().showMessage(tr("scan_stopped_partial"), STATUS_TIMEOUT_MS)
        if outcome.result.warnings:
            self.statusBar().showMessage(tr("scan_priority_warning", reason="; ".join(
                problem_text(reason) for reason in outcome.result.warnings)))

    def _scan_ended(self) -> None:
        self._worker = None
        self.scan_activity_changed.emit()
        self._live_timer.stop()
        if self._trash_rescans:
            QTimer.singleShot(0, self._rescan_after_trash)
        else:
            self._refreshing = False

    def _back_from_scan(self) -> None:
        self.results.end_scan()
        self.pages.setCurrentIndex(RESULTS_PAGE if self.results.outcome is not None else WELCOME_PAGE)
        self._update_actions()

    def rescan_folder(self, node: Node, *, exact_allocation: bool = False) -> None:
        """Scan one folder again and swap it into the results (the whole scan when it is the root)."""
        if self._worker is not None or self.operation_busy or self.results.outcome is None:
            return
        # The scan waits for the window's readers, except Follow changes: its feed reads nothing of the tree
        # and keeps reporting while the folder is read, until the feed armed after it takes over.
        paused = self._background_pause(wait=False) if self._background_pause is not None else ()
        self._follow.hold()
        self._undo.expire()
        if self.results.outcome.result.root.path is None:
            roots = tuple(child.path for child in self.results.outcome.result.root.children)
            self.start_scan_roots(roots, exact_allocation=exact_allocation)
            return
        if (self.results.outcome.result.hard_links is not None) != self._actions["count_hard_links"].isChecked():
            # Counting hard links was turned on or off since this scan: only a whole scan counts every name.
            root = self.results.outcome.result.root
            self._forget_changed()
            self.start_scan(root.path, exact_allocation=exact_allocation)
            return
        if node.parent is None:
            self.start_scan(node.path, exact_allocation=exact_allocation)
            return
        self._analyser = None
        # One folder of a finished scan is listed, never taken from the file table on disk, which can be
        # a few seconds behind what an operation has just changed. Hard links are counted afterwards over
        # the whole tree (_branch_rescanned), since a name inside the folder can share data with one outside.
        options = replace(self._scan_options(exact_allocation=exact_allocation), mft=False, count_hard_links=False)
        worker = ScanWorker(node.path, options, self)
        before = node.size
        worker.progressed.connect(
            lambda progress: self._is_current(worker) and self.results.scan_bar.show_progress(progress))
        worker.succeeded.connect(
            lambda outcome: self._is_current(worker) and self._branch_rescanned(node, outcome, before))
        worker.failed.connect(lambda reason: self._is_current(worker) and self._branch_failed(reason))
        worker.cancelled.connect(lambda _outcome: self._is_current(worker) and self._branch_cancelled())
        worker.analysing.connect(lambda: self._is_current(worker) and self.results.scan_bar.analysing())
        worker.finished.connect(lambda: after_threads((worker,), lambda: self._release_scan(worker), self))
        self._worker = worker
        self.scan_activity_changed.emit()
        self._scan_workers.add(worker)
        self.results.scan_bar.start()
        self._update_actions()
        queue_worker(worker, lambda: not self._closing and self._worker is worker and not worker._cancel.is_set(),
                     self, lambda: self._discard_branch(worker), readers=paused)

    def refresh_folders(self, chosen: list[tuple[Node, bool]]) -> None:
        """Read again only what Follow changes found changed (``gui/folder_refresh.py``)."""
        folder_refresh.refresh_folders(self, chosen)

    def _discard_branch(self, worker: ScanWorker) -> None:
        if worker is self._worker:
            if self._closing:
                self._worker = None
                self.scan_activity_changed.emit()
            else:
                self._branch_cancelled()
        self._release_scan(worker)

    def _branch_rescanned(self, old: Node, outcome: ScanOutcome, before: int) -> None:
        self._scan_ended()
        self.results.scan_bar.hide()
        new = self.results.replace_branch(old, outcome.result)
        self._update_actions()
        self.statusBar().showMessage(tr("rescan_done", name=new.name, before=format_size(before, self._unit),
                                        after=format_size(new.size, self._unit)), STATUS_TIMEOUT_MS)
        root = self.results.tree_model.root
        self._start_analysis(root, with_capacity=True, count=self.results.outcome.result.hard_links is not None)
        self._follow.adopt(root)
        if outcome.result.warnings:
            self.statusBar().showMessage(tr("scan_priority_warning", reason="; ".join(
                problem_text(reason) for reason in outcome.result.warnings)))

    def _start_analysis(self, root: Node, *, with_capacity: bool, count: bool = False) -> None:
        """Summarise the changed tree on a worker; with ``count``, plan its counted hard-link totals first.

        A later tree change drops ``_analyser``, so an answer for an older tree is ignored.
        """
        worker: AnalyseWorker | CountWorker
        if count:
            worker = CountWorker(root, self)
            worker.ready.connect(lambda plan: not self._closing and self._analyser is worker
                                 and self.results.tree_model.root is root and self._counted(root, plan, with_capacity))
        else:
            worker = AnalyseWorker(root, self, partial=self.results.outcome.partial, with_capacity=with_capacity)
            worker.capacity_ready.connect(lambda ledger: not self._closing and self.results.tree_model.root is root
                                          and self._analyser is worker and self.results.set_capacity(ledger))
            worker.done.connect(lambda summary: not self._closing and self._analyser is worker
                                and self._summary_ready(summary))
        worker.finished.connect(lambda: self._analysers.discard(worker))
        worker.finished.connect(worker.deleteLater)
        self._analyser = worker
        self._analysers.add(worker)
        worker.start()

    def _counted(self, root: Node, plan: HardLinkPlan, with_capacity: bool) -> None:
        self.results.apply_counted(plan)
        self._start_analysis(root, with_capacity=with_capacity)  # the counted chart categories follow

    def _summary_ready(self, summary: Summary) -> None:
        self.results.apply_summary(summary)

    def _branch_cancelled(self) -> None:
        self._refreshing = False  # stopping one folder stops the rest of a requested refresh: they stay on offer
        self._scan_ended()
        self.results.scan_bar.hide()
        self._update_actions()
        self.statusBar().showMessage(tr("scan_cancelled"), STATUS_TIMEOUT_MS)
        self._follow.resume()  # the results did not change: follow them on

    def _branch_failed(self, reason: str) -> None:
        self._scan_failed(reason)
        self._follow.resume()

    def _mark_changed(self, nodes: Sequence[Node], *, exact: bool = False) -> None:
        """Remember that an operation changed files in ``nodes``: offered for a rescan, never scanned unasked."""
        root = self.results.tree_model.root
        if root is None or self._closing:
            return
        self._trash_rescans = outermost(node for node in (*self._trash_rescans, *nodes) if node.is_in(root))
        if exact:
            self._exact_rescans.update(nodes)
        self._update_refresh_notice()
        QTimer.singleShot(0, self._rescan_after_trash)

    def _forget_changed(self) -> None:
        """Drop the changed folders on offer: a whole scan replaces them, or the window is closing."""
        self._trash_rescans.clear()
        self._exact_rescans.clear()
        self._refreshing = False
        self._update_refresh_notice()

    def _update_refresh_notice(self) -> None:
        offered = self.results.outcome is not None and not self._follow.enabled and not self._closing
        ready = self._worker is None and not self.operation_busy
        self.results.refresh_notice.show_pending(len(self._trash_rescans) if offered else 0, enabled=ready)

    def refresh_changed(self) -> None:
        """Rescan the folders changed since they were scanned, because the user asked for it."""
        if self._closing or self.operation_busy or self._worker is not None or not self._trash_rescans:
            return
        self._undo.expire()
        self._refreshing = True
        self._rescan_after_trash()

    def _apply_scan_preset(self, preset: ScanPreset) -> None:
        options = preset.options
        keys = ("include_hidden", "gentle_scan", "capture_file_times", "capture_owners",
                "exact_allocation", "count_hard_links")
        for (action, field), key in zip(SCAN_FLAGS, keys, strict=True):
            with QSignalBlocker(self._actions[action]):
                self._actions[action].setChecked(getattr(options, field))
            self.settings.setValue(key, getattr(options, field))
        self.settings.setValue(SCAN_WORKERS_KEY, options.workers)
        self.settings.setValue(EXCLUSIONS_KEY, list(options.exclude))
        if self._scan_defaults is not None:
            self._scan_defaults.workers, self._scan_defaults.exclude = options.workers, options.exclude
        self.path_edit.setText(preset.path)
        self.statusBar().showMessage(tr("presets_loaded", name=preset.name), STATUS_TIMEOUT_MS)

    def choose_folder(self) -> None:
        """Ask for a folder and scan it."""
        start = self._last_path or os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(self, tr("choose_folder_title"), start)
        if folder:
            self.start_scan(folder)

    def restart_as_admin(self) -> None:
        """Start FileTree again as administrator (scanning the same folder) and close this copy.

        When the prompt is declined, this copy keeps running and says so.
        """
        if self._closing or self._settings_dialogs or self.operation_busy:
            return
        try:
            arguments = (self._restart_arguments() if self._restart_arguments is not None
                         else WorkspaceState((self.capture_restart_scope(),),
                                             options=(self._scan_options(),)).arguments())
        except ValueError as error:
            self.statusBar().showMessage(tr("elevate_failed", reason=str(error)), STATUS_TIMEOUT_MS)
            return
        dialog = ElevationDialog(arguments, self)
        self._settings_dialogs.add(dialog)
        self._update_actions()
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            self._settings_dialogs.discard(dialog)
            dialog.deleteLater()
            if not self._closing:
                self._update_actions()
        if self._closing:
            return
        if dialog.worker.started_copy:
            self.quit_application()
        else:
            message = (tr("elevate_failed", reason=dialog.worker.error) if dialog.worker.error is not None
                       else tr("elevate_declined"))
            self.statusBar().showMessage(message, STATUS_TIMEOUT_MS)

    def set_exclusions(self, patterns: list[str]) -> None:
        """Skip ``patterns`` from the next scan on, and remember them."""
        if self._scan_defaults is not None:
            self._scan_defaults.exclude = tuple(patterns)
        self.settings.setValue(EXCLUSIONS_KEY, patterns)

    def exclusions(self) -> list[str]:
        """The folder name patterns and folder paths that scans skip (the ``exclusions`` setting)."""
        if self._scan_defaults is not None:
            return list(self._scan_defaults.exclude)
        value = self.settings.value(EXCLUSIONS_KEY, [])
        if isinstance(value, str):  # an INI file keeps a one-item list as a plain string
            return [value] if value else []
        return [str(pattern) for pattern in value or []]

    def restore_scan_preferences(self, options: ScanOptions, defaults: ScanDefaults) -> None:
        """Apply captured choices without emitting preference writes or starting any operation."""
        self._scan_defaults = defaults
        for action, field in SCAN_FLAGS:
            with QSignalBlocker(self._actions[action]):
                self._actions[action].setChecked(getattr(options, field))

    def _scan_options(self, *, exact_allocation: bool = False) -> ScanOptions:
        return ScanOptions(include_hidden=self._actions["hidden"].isChecked(), exclude=tuple(self.exclusions()),
                           gentle=self._actions["gentle"].isChecked(),
                           workers=(self._scan_defaults.workers if self._scan_defaults is not None
                                    else read_workers(self.settings)),
                           file_times=self._actions["capture_file_times"].isChecked(),
                           windows_owners=self._actions["capture_owners"].isChecked(),
                           exact_windows_allocation=exact_allocation or self._actions["exact_allocation"].isChecked(),
                           count_hard_links=self._actions["count_hard_links"].isChecked(),
                           adaptive=self._actions["auto_cpu"].isChecked(),
                           mft=self._actions["mft_scan"].isChecked())

    def configure_workers(self) -> None:
        """Persist bounded concurrency for new scans and branch rescans, leaving running workers alone."""
        value, accepted = QInputDialog.getInt(self, tr("action_scan_workers"),
                                             tr("workers_prompt", default=DEFAULT_WORKERS),
                                             self._scan_options().workers, 1, _MAX_SCAN_WORKERS, 1)
        if accepted:
            self.set_workers(value)

    def set_workers(self, value: int) -> None:
        """Read with ``value`` threads from the next scan on, and remember it."""
        if self._scan_defaults is not None:
            self._scan_defaults.workers = value
        self.settings.setValue(SCAN_WORKERS_KEY, value)

    def choose_saved_scan(self) -> None:
        """Ask for a saved scan (a Folder tree JSON export) and compare the scan on screen with it."""
        if self.results.outcome is None or self._worker is not None:
            return
        start = str(self.settings.value("export_dir", os.path.expanduser("~")))
        file, _ = QFileDialog.getOpenFileName(self, tr("compare_title"), start, tr("json_filter"))
        if file:
            self.results.compare_with(file)
