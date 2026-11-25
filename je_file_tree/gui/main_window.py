"""The main window: toolbar and menus around two pages (welcome, results; a scan fills the results live)."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from PySide6.QtCore import QByteArray, QEvent, QPoint, QSettings, QSignalBlocker, QThread, QTimer, Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QDialog, QFileDialog, QLineEdit, QMainWindow, QMenu, QMessageBox, QStackedWidget

from je_file_tree.core.analysis import Summary
from je_file_tree.core.cleanup import CleanupGroup, DETAILS
from je_file_tree.core.cleanup_policy import CleanupPolicy, RuleSetting, load_policy
from je_file_tree.core.copy_approval import CopyApproval
from je_file_tree.core.duplicates import DuplicateGroup
from je_file_tree.core.formatting import AUTO_UNIT, format_count, format_share, format_size
from je_file_tree.core.hard_links import HardLinkPlan
from je_file_tree.core.node import Node, folder_holding, outermost
from je_file_tree.core.operation_journal import JournalApproval, OperationJournal
from je_file_tree.core.operations import MoveResult, MoveSummary
from je_file_tree.core.permanent_delete import DeleteResult
from je_file_tree.core.protected import protected_places, protection_of
from je_file_tree.core.system_files import system_file
from je_file_tree.gui import elevation, file_actions, shell_integration
from je_file_tree.gui.bin_labels import BinLabels
from je_file_tree.gui.busy_notice import show_busy
from je_file_tree.gui.change_watch import FollowChanges
from je_file_tree.gui.cleanup_review import CleanupReview
from je_file_tree.gui.compression import CompressionDialog
from je_file_tree.gui.copy_dialog import CopyDialog
from je_file_tree.gui.duplicate_link_dialog import DuplicateLinksDialog
from je_file_tree.gui.entry_move_prompt import confirm_entry_move
from je_file_tree.gui.entry_report import EntryReportDialog
from je_file_tree.gui.failed_dialog import FailedEntriesDialog
from je_file_tree.gui.folder_validation import FolderDrops
from je_file_tree.gui.i18n import current_language, set_language, tr
from je_file_tree.gui.lazy_details import set_lazy_details
from je_file_tree.gui.live_refresh import LiveRefresh
from je_file_tree.gui.locale_font import apply_language_font
from je_file_tree.gui.namespace_dialog import NamespaceDialog
from je_file_tree.gui.operation_group import OperationGroup
from je_file_tree.gui.permanent_delete import (
    PermanentDeleteWorker,
    PermanentReportDialog,
    confirm_permanent_delete,
    permanent_question,
    refuse_managed,
    report_rows,
    report_summary,
)
from je_file_tree.gui.qt_translation import apply_qt_translation
from je_file_tree.gui.recent_actions import journal_folder
from je_file_tree.gui.recurring_review import RecurringReview
from je_file_tree.gui.results_view import CHART_TAB, ResultsView
from je_file_tree.gui.scan_preferences import ScanDefaults
from je_file_tree.gui.scan_worker import AnalyseWorker, CountWorker, ExportWorker, ScanWorker, wait_for
from je_file_tree.gui.scrolling_page import ScrollingPage
from je_file_tree.gui.shortcuts import WindowShortcuts
from je_file_tree.gui.skipped_dialog import SkippedEntriesDialog
from je_file_tree.gui.trash_undo import TrashUndo
from je_file_tree.gui.trash_worker import TrashWorker
from je_file_tree.gui.welcome import WelcomePage
from je_file_tree.gui.window_fit import fit_window
from je_file_tree.gui.window_settings import (
    ASK_ADMIN_KEY,
    AUTO_CPU_KEY,
    CLEANUP_POLICY_KEY,
    MFT_SCAN_KEY,
    RESULTS_PAGE,
    SEARCHES_KEY,
    STATUS_TIMEOUT_MS,
    UNITS,
    read_flag,
    saved_searches,
)
from je_file_tree.gui.worker_lifecycle import WorkerDialog, after_threads, queue_worker
from je_file_tree.gui.zip_dialog import ZipDialog
from je_file_tree.gui.window_dialogs import DialogActions
from je_file_tree.gui.window_exports import ExportActions
from je_file_tree.gui.window_menus import WindowMenus
from je_file_tree.gui.window_scans import ScanControls

_MAX_RECENT = 10
_LISTED_NAMES = 8  # entries named in a Recycle Bin question; the rest are counted
_MAX_REFUSAL_NOTICE = 1024
# Actions that read or change the scanned entries wait for a running scan or source operation. They stay
# enabled meanwhile and, when used, say why they wait instead of doing nothing (gui.busy_notice).
_WAIT_FOR_SCAN = frozenset({
    "rescan", "export_folders", "export_largest", "export_list", "export_json", "export_chart_png",
    "export_chart_svg", "print_view", "export_view_pdf", "export_report_html", "export_report_xlsx", "trash",
    "permanent_delete", "find", "compare", "special_files", "problem_files", "dev_tools", "live_compare",
    "git_history", "history",
    "recurring", "scan_presets", "projects", "programs", "virtual_disks", "file_times", "volumes", "disks",
    "bins", "cleanup_policy",
})
# These start a scan or a restart themselves, so only a running source operation makes them wait.
_WAIT_FOR_OPERATION = frozenset({"open", "multi_scan", "elevate"})
_CHART_SETTINGS = ("chart_mode", "treemap_levels", "treemap_colours", "tree_orientation")


@dataclass(frozen=True, slots=True)
class FolderContext:
    """A current loaded folder or the translation key explaining why none is available."""

    node: Node | None
    reason: str = ""


class MainWindow(ScanControls, ExportActions, DialogActions, WindowMenus, QMainWindow):
    """The FileTree window."""

    shutdown_finished = Signal()
    scan_scope_changed = Signal()
    scan_activity_changed = Signal()
    size_unit_changed = Signal(str)

    def __init__(self, settings: QSettings | None = None, *, operations: OperationGroup | None = None) -> None:
        super().__init__()
        self._operations = operations
        self._close_all: Callable[[], object] | None = None
        self._background_settings: Callable[[], object] | None = None
        self._background_pause: Callable[..., tuple[QThread, ...]] | None = None
        self._recurring_show: Callable[[], object] | None = None
        self._language_changed: Callable[[], object] = self.retranslate
        self.settings = settings if settings is not None else QSettings()
        self._journal = OperationJournal(journal_folder())
        self._init_scan_state()
        self._init_operation_workers()
        self._path_dialogs, self._settings_dialogs = set[QDialog](), set[WorkerDialog]()
        self._closing, self._close_waiting, self._close_ready = False, False, False
        self._analyser: AnalyseWorker | CountWorker | None = None
        self._analysers: set[AnalyseWorker | CountWorker] = set()
        self._exports: set[ExportWorker] = set()
        self._protected = protected_places()  # system and program folders: ask twice before moving them
        self._last_path, self._last_roots = "", ()
        self._unit = str(self.settings.value("unit", AUTO_UNIT))
        if self._unit not in UNITS:
            self._unit = AUTO_UNIT
        self.welcome = WelcomePage()
        self.results = ResultsView(settings=self.settings)
        self._follow = FollowChanges(self)
        self._undo = TrashUndo(self)
        self._bin_labels = BinLabels(self)
        self._bin_labels.ready.connect(self._bin_metadata_ready)
        self._bin_labels.busy_changed.connect(lambda _busy: self._update_bin_buttons())
        self.pages = QStackedWidget()
        scrolled = ScrollingPage(self.results)
        scrolled.room_changed.connect(self.results.fit_height)
        for page in (self.welcome, scrolled):
            self.pages.addWidget(page)
        self._live_timer = LiveRefresh(self.results.refresh_live, self)  # spaced by its cost (U-20261118-01)
        self.setCentralWidget(self.pages)
        self.path_edit = QLineEdit()
        self._actions: dict[str, QAction] = {}
        self._menus: dict[str, QMenu] = {}
        self._unit_actions: dict[str, QAction] = {}
        self._language_actions: dict[str, QAction] = {}
        self._build_actions()
        self._build_menus()
        self._shortcuts = WindowShortcuts(self._actions, self.settings, self)
        self._build_toolbar()
        self._connect()
        self.setAcceptDrops(True)
        fit_window(self, 1240, 800)
        self._restore()
        self.retranslate()
        self._update_actions()
        self._restore_cleanup_policy()

    def _init_operation_workers(self) -> None:
        self._trash_worker: TrashWorker | None = None
        self._delete_worker: PermanentDeleteWorker | None = None

    def _init_scan_state(self) -> None:
        self._budget_store = None
        self._budget_show = None
        self._prepared_scope: str | tuple[str, ...] | None = None
        self._has_prepared_scope = False
        self._prepared_errors: tuple[str, ...] = ()
        self._restart_arguments: Callable[[], list[str]] | None = None
        self._scan_defaults: ScanDefaults | None = None
        self._worker: ScanWorker | None = None
        self._scan_workers: set[ScanWorker] = set()
        self._pending_scan: ScanWorker | None = None
        self._folder_drops = FolderDrops(self)
        # Folders whose files an operation changed after they were scanned. They are read again when the
        # user asks (the notice above the results), or by themselves only while Follow changes is on.
        self._trash_rescans: list[Node] = []
        self._exact_rescans: set[Node] = set()  # of those, the ones to read with per-file allocation
        self._refreshing = False  # the user asked for the changed folders: go through all of them

    def _restore_cleanup_policy(self) -> None:
        self._cleanup_policy = CleanupPolicy()
        if self.settings.contains(CLEANUP_POLICY_KEY):
            try:
                self._cleanup_policy = load_policy(self.settings.value(CLEANUP_POLICY_KEY))
            except (ValueError, RecursionError):
                self._cleanup_policy = CleanupPolicy(tuple(RuleSetting(key, False, int(details.minimum_age))
                                                           for key, details in DETAILS.items()))
                self.statusBar().showMessage(tr("policy_saved_invalid"))
        self.results.cleanup.set_policy(self._cleanup_policy)

    def quit_application(self) -> None:
        """Close the containing workspace, or this standalone integration window."""
        if self._close_all is None:
            self.close()
        else:
            self._close_all()

    def configure_background(self) -> None:
        """Open the owning workspace's explicit preferences; standalone integrations remain passive."""
        if self._background_settings is not None:
            self._background_settings()

    def show_recurring(self) -> None:
        """Open the workspace's dated observations, including before a foreground result exists."""
        if self._recurring_show is not None:
            self._recurring_show()

    @property
    def local_operation_busy(self) -> bool:
        """Whether this tab owns Trash, permanent deletion, restoration or a source-operation review."""
        return (self._trash_worker is not None or self._delete_worker is not None or self._undo.busy
                or bool(self._path_dialogs))

    @property
    def operation_busy(self) -> bool:
        """Serialize source mutations across this window and any result-tab peers."""
        return self.local_operation_busy or self._operations is not None and self._operations.busy

    def pending_source_workers(self) -> tuple[QThread, ...]:
        """Quiesce native readers without joining on the GUI thread; queued operations wait for them."""
        windows = ((self,) if self._operations is None or not self.operation_busy
                   else tuple(self._operations.windows))
        readers = tuple(worker for window in windows if not window._closing
                        for worker in window._quiesce_source_readers())
        return (*readers, *self.findChildren(QThread))

    def _quiesce_source_readers(self) -> tuple[QThread, ...]:
        background = self._background_pause(wait=False) if self._background_pause is not None else ()
        following = self._follow.quiesce(wait=False)
        return (*background, *following)

    # --- scanning ---------------------------------------------------------

    # --- entry actions ----------------------------------------------------

    def show_menu_for(self, node: Node, picked: Sequence[Node], point: QPoint, *, chart: bool = False) -> None:
        """Pop up the menu of things to do with ``node``; its *Move to Recycle Bin* takes all of ``picked``."""
        if node.path is None:
            self._show_in_chart(node)
            return
        menu = QMenu(self)
        entries: list[tuple[str, Callable[[], object]]] = [
            ("menu_open_item", lambda: file_actions.open_path(node.path)),
            ("menu_reveal", lambda: file_actions.reveal_in_file_manager(node.path)),
            ("menu_copy_path", lambda: file_actions.copy_path(node.path)),
        ]
        if shell_integration.supported():
            entries.append(("menu_properties", lambda: self.show_properties(node)))
        if self.results.archives.busy(node):
            entries.append(("archive_stop", lambda: self.results.archives.stop(node)))
        if node.is_dir and not node.is_link:
            entries.append(("menu_show_chart", lambda: self._show_in_chart(node)))
            entries.append(("menu_rescan_here", lambda: self._explain_busy(tr("menu_rescan_here"))
                            or self.rescan_folder(node)))
            entries.append(("menu_scan_here", lambda: self.start_scan(node.path)))
            if (elevation.supported() and self._worker is None and not self.operation_busy
                    and self.results.outcome is not None and self.results.outcome.result.root.path is not None):
                entries.append(("menu_compression", lambda: self.show_compression(node)))
        for key, handler in entries:
            menu.addAction(tr(key)).triggered.connect(handler)
        virtual = self.results.outcome is not None and self.results.outcome.result.root.path is None
        movable = [] if virtual else [entry for entry in _movable(picked) if system_file(entry.path) is None]
        if movable:
            menu.addSeparator()
            if self._worker is None and not self.operation_busy:
                self._add_move_entries(menu, picked, movable)
            text = tr("action_trash") if len(movable) == 1 else tr("action_trash_many",
                                                                    count=format_count(len(movable)))
            menu.addAction(text).triggered.connect(lambda: self.move_to_trash(movable))
            if not self.results.in_suggestions():  # never from FileTree's Clean up or duplicate suggestions
                text = tr("permanent_delete") if len(movable) == 1 else tr("permanent_menu_many",
                                                                            count=format_count(len(movable)))
                menu.addAction(text).triggered.connect(lambda: self.delete_permanently(movable))
        if chart:
            menu.addSeparator()
            for key in ("export_chart_png", "export_chart_svg"):
                menu.addAction(self._actions[key])
        menu.exec(point)

    def _add_move_entries(self, menu: QMenu, picked: Sequence[Node], movable: Sequence[Node]) -> None:
        menu.addAction(tr("menu_move_folder")).triggered.connect(lambda: self.show_namespace(picked))
        menu.addAction(tr("menu_rename")).triggered.connect(lambda: self.show_namespace(picked, rename=True))
        if any(entry.is_dir and not entry.is_link for entry in movable):
            menu.addAction(tr("menu_move_drive")).triggered.connect(lambda: self.show_copy(picked))
        if len(movable) == 1 and movable[0].is_dir and not movable[0].is_link:
            menu.addAction(tr("menu_zip")).triggered.connect(lambda: self.show_zip(movable[0]))

    def show_properties(self, node: Node) -> None:
        """Open the selected entry's Windows Properties, reporting shell failures."""
        if not shell_integration.show_properties(node.path, int(self.winId())):
            QMessageBox.warning(self, tr("menu_properties"), tr("properties_failed", path=node.path))

    def show_namespace(self, nodes: Sequence[Node], *, rename: bool = False) -> None:
        """Review real selected entries; join operations and refresh the current affected scan scope."""
        outcome = self.results.outcome
        if (outcome is None or self._path_dialogs or self._worker is not None or self.operation_busy
                or not nodes
                or any(node.parent is None or not node.is_in(outcome.result.root) for node in nodes)):
            return
        root = outcome.result.root
        if root.path is None:
            return
        dialog = NamespaceDialog(root, nodes, self._unit, self, rename=rename)
        self._undo.expire()
        self._path_dialogs.add(dialog)
        self._update_actions()
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            self._path_dialogs.discard(dialog)
            self._update_actions()
            dialog.deleteLater()
            QTimer.singleShot(0, self._rescan_after_trash)
        if not self._closing and dialog.changed and self.results.outcome is outcome:
            self._analyser = None
            self.results.clear_capacity()
            self._bin_labels.refresh()
            self._mark_changed([root])

    def show_zip(self, node: Node) -> None:
        """Archive one folder; moving the original goes through the ordinary Recycle Bin questions."""
        outcome = self.results.outcome
        if (outcome is None or self._path_dialogs or self._worker is not None or self.operation_busy
                or node.parent is None or not node.is_in(outcome.result.root) or outcome.result.root.path is None):
            return
        target, _ = QFileDialog.getSaveFileName(self, tr("zip_title"), f"{node.path}.zip", tr("zip_filter"),
                                                options=QFileDialog.Option.DontConfirmOverwrite)
        if not target:
            return
        dialog = ZipDialog(outcome.result.root, node, target, self._unit, self)
        self._path_dialogs.add(dialog)
        self._update_actions()
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            self._path_dialogs.discard(dialog)
            self._update_actions()
            dialog.deleteLater()
        if self._closing or self.results.outcome is not outcome:
            return
        if dialog.move_requested and (dialog.proof is None or not dialog.proof.unchanged()):
            QMessageBox.warning(self, tr("zip_title"), tr("zip_lost"))
        elif dialog.move_requested:
            self.move_to_trash([node])
        holder = folder_holding(outcome.result.root, target) if dialog.proof is not None else None
        if holder is not None:  # last: with Follow changes on, this reads the folder again
            self._mark_changed([holder])

    def show_copy(self, nodes: Sequence[Node]) -> None:
        """Review copied folders, join the copy worker, then use ordinary protected-folder Trash approval."""
        outcome = self.results.outcome
        if (outcome is None or self._path_dialogs or self._worker is not None or self.operation_busy
                or not nodes
                or any(node.parent is None or not node.is_in(outcome.result.root) for node in nodes)):
            return
        root = outcome.result.root
        if root.path is None:
            return
        dialog = CopyDialog(root, nodes, self._unit, self)
        self._undo.expire()
        self._path_dialogs.add(dialog)
        self._update_actions()
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            self._path_dialogs.discard(dialog)
            self._update_actions()
            dialog.deleteLater()
            QTimer.singleShot(0, self._rescan_after_trash)
        if self._closing or not dialog.changed or self.results.outcome is not outcome:
            return
        self._analyser = None
        self.results.clear_capacity()
        self._bin_labels.refresh()
        if dialog.finish_requested and dialog.approval is not None:
            self.move_to_trash([proof.item.node for proof in dialog.approval.proofs], copies=dialog.approval)
        self._mark_changed([root])

    def show_duplicate_links(self, groups: Sequence[DuplicateGroup]) -> None:
        """Serialize reviewed exact-file linking and rebuild the full root after any attempted operation."""
        outcome = self.results.outcome
        panel = self.results.duplicates
        if (outcome is None or self._worker is not None or self.operation_busy or not groups
                or any(group not in panel.link_groups for group in groups)):
            return
        root = outcome.result.root
        if root.path is None:
            return
        if any(group.kept is None or any(not node.is_in(root) for node in group.files) for group in groups):
            return
        panel.stop()
        self._undo.expire()
        dialog = DuplicateLinksDialog(root, groups, self._journal, self)
        self._path_dialogs.add(dialog)
        self._update_actions()
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            self._path_dialogs.discard(dialog)
            self._update_actions()
            dialog.deleteLater()
            QTimer.singleShot(0, self._rescan_after_trash)
        if not self._closing and dialog.changed and self.results.outcome is outcome:
            self._analyser = None
            self.results.clear_capacity()
            self._bin_labels.refresh()
            self._mark_changed([root])

    def show_compression(self, node: Node) -> None:
        """Review/confirm scoped native operations, then rescan with per-file allocation if attempted."""
        outcome = self.results.outcome
        if (not elevation.supported() or self._worker is not None or self.operation_busy
                or outcome is None or outcome.result.root.path is None or not node.is_dir or node.is_link
                or not node.is_in(outcome.result.root)):
            return
        dialog = CompressionDialog(node, self._unit, self, partial=outcome.partial)
        dialog.selected.connect(self.results.select_node)
        self._path_dialogs.add(dialog)
        self._update_actions()
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            self._path_dialogs.discard(dialog)
            self._update_actions()
            dialog.deleteLater()
        if dialog.changed:
            self._mark_changed([node], exact=True)

    def _without_managed(self, nodes: list[Node]) -> list[Node]:
        # 10k managed refusals: the old full warning label took 5.14 s to display.
        blocked, allowed = [], []
        for node in nodes:
            (blocked if system_file(node.path) is not None else allowed).append(node)
        if blocked:
            self._show_skipped([(node, "system_managed") for node in blocked])
        return allowed

    def _show_skipped(self, skipped: Sequence[tuple[Node, str]]) -> None:
        """Keep small notices familiar; show every large refusal in a lazy read-only table."""
        if len(skipped) <= _LISTED_NAMES:
            lines = "\n".join(f"{node.path}: {tr(f'trash_skip_{reason}')}" for node, reason in skipped)
            text = tr("trash_skipped", names=lines)
            if len(text) <= _MAX_REFUSAL_NOTICE and "<" not in text and ">" not in text:
                QMessageBox.warning(self, tr("trash_confirm_title"), text)
                return
        self._show_entry_report(SkippedEntriesDialog(skipped, self))

    def _show_entry_report(self, dialog: EntryReportDialog) -> None:
        """Own a complete read-only report until dismissal, serializing source actions."""
        self._path_dialogs.add(dialog)
        self._update_actions()
        try:
            dialog.exec()
        finally:
            self._path_dialogs.discard(dialog)
            self._update_actions()
            dialog.deleteLater()

    def move_to_trash(self, nodes: Sequence[Node], *, copies: CopyApproval | None = None,
                      proposal: RecurringReview | None = None) -> None:
        """Ask once, then move ``nodes`` to the Recycle Bin / Trash and take them out of the results.

        An entry inside another of ``nodes`` goes along with its folder; the scanned folder itself is
        never moved. Entries the system refuses to move stay, and are named in a warning.
        """
        chosen = _movable(nodes)
        root = self.results.tree_model.root
        if (not chosen or root is None or root.path is None
                or self._explain_busy(tr("action_trash"))  # a scan or operation runs: say so
                or self._worker is not None or self.operation_busy
                or copies is not None and not copies.matches(root, chosen)
                or proposal is not None and (not proposal.matches(root, chosen)
                                            or not self._proposal_current(proposal))):
            return
        chosen = self._without_managed(chosen)
        if self._closing:
            return
        reasons = self.results.cleanup.reasons_for(chosen) if proposal is None else proposal.reasons
        if reasons and chosen:
            chosen = self._review_cleanup(chosen, reasons, root)
        if not chosen or proposal is not None and not self._proposal_current(proposal):
            return
        approvals = {node: protection_of(node.path, self._protected) for node in chosen}
        if not self._confirm_protected(chosen):
            return
        answer = self._confirm_copy_trash(chosen, copies) if copies is not None else confirm_entry_move(
            self, tr("trash_confirm_title"), self._trash_question(chosen))
        if answer != QMessageBox.StandardButton.Yes or proposal is not None and not self._proposal_current(proposal):
            return
        if self._worker is not None or self.operation_busy or self.results.tree_model.root is not root:
            self._show_skipped([(node, "outside") for node in chosen])
            return
        if self.results.duplicates.running:
            self.results.duplicates.stop()
        decisions = self.results.duplicates.decisions_for(chosen)
        # 20k captured duplicate members: repeated selected-list searches took 1.55 s.
        selected = set(chosen)
        explanations = {node: f"cleanup:{group.key}" for node, group in reasons.items() if node in selected}
        explanations.update((node, "duplicates") for group in decisions for node in group.files if node in selected)
        audit = JournalApproval(self._journal, explanations)
        worker = TrashWorker(root, chosen, self._protected, approvals, self, decisions=decisions, audit=audit)
        if self.results.outcome is not None:
            worker.summary_now = self.results.outcome.now
        worker.proposal_context = proposal.report.context if proposal is not None else None
        worker.proposal_check = (lambda: proposal.store.status(proposal.report)) if proposal is not None else None
        if copies is not None:
            worker.copy_approval = CopyApproval(tuple(proof for proof in copies.proofs if proof.item.node in selected),
                                                copies.redirect)
        self._undo.expire()
        worker.allow_undo = True
        worker.done.connect(lambda result: after_threads((worker,), lambda: self._trash_finished(result), self))
        self._trash_worker = worker
        self.results.setEnabled(False)
        self._update_actions()
        self.statusBar().showMessage(tr("trash_running"))
        queue_worker(worker, lambda: not self._closing and self._trash_worker is worker
                     and not worker._cancel.is_set(), self, lambda: self._discard_trash(worker))

    def _discard_trash(self, worker: TrashWorker) -> None:
        if worker is self._trash_worker and not self._closing:
            worker.result = MoveResult()
            self._trash_finished(worker.result)

    def delete_permanently(self, nodes: Sequence[Node]) -> None:
        """Ask, every time, then permanently delete exactly the approved ``nodes``: the only way in.

        Windows-managed entries are refused before any question. System and program folders get the
        protected-folder question first; then one question, No by default, names the entries, their
        count and size and says it cannot be undone. A declined or closed question deletes nothing.
        The worker removes only the approved entries and what the scan recorded inside approved
        folders, rechecking each against its scan record; no setting or batch skips the question.
        """
        chosen = _movable(nodes)
        root = self.results.tree_model.root
        if (not chosen or root is None or root.path is None
                or self._explain_busy(tr("permanent_delete"))  # a scan or operation runs: say so
                or self._worker is not None or self.operation_busy or self._closing):
            return
        managed = {node for node in chosen if system_file(node.path) is not None}
        if managed:
            refuse_managed(self, [node for node in chosen if node in managed])
            chosen = [node for node in chosen if node not in managed]
        if not chosen or self._closing:
            return
        approvals = {node: protection_of(node.path, self._protected) for node in chosen}
        if not self._confirm_protected(chosen, "permanent_protected_question"):
            return
        answer = confirm_permanent_delete(self, tr("permanent_title"), permanent_question(chosen, self._unit))
        if answer != QMessageBox.StandardButton.Yes or self._closing:
            return
        if self._worker is not None or self.operation_busy or self.results.tree_model.root is not root:
            self._show_entry_report(PermanentReportDialog([(node.path, tr("permanent_skip_outside"))
                                                           for node in chosen], tr("permanent_title"), self))
            return
        if self.results.duplicates.running:
            self.results.duplicates.stop()
        worker = PermanentDeleteWorker(root, chosen, self._protected, approvals, self._journal, self)
        if self.results.outcome is not None:
            worker.summary_now = self.results.outcome.now
        self._undo.expire()
        worker.progressed.connect(lambda count: worker is self._delete_worker and not self._closing
                                  and self.statusBar().showMessage(tr("permanent_running", count=format_count(count))))
        worker.done.connect(lambda result: after_threads((worker,), lambda: self._delete_finished(worker, result),
                                                         self))
        self._delete_worker = worker
        self.results.setEnabled(False)
        self._update_actions()
        self.statusBar().showMessage(tr("permanent_running", count=format_count(0)))
        queue_worker(worker, lambda: not self._closing and self._delete_worker is worker and not worker.cancelled,
                     self, lambda: self._discard_delete(worker))

    def _stop_delete(self, *, wait: bool) -> None:
        """Closing: stop after the entry being removed; with ``wait``, until the worker has ended."""
        worker = self._delete_worker
        if worker is None:
            return
        worker.cancel(discard_results=True)
        if wait:
            wait_for(worker)
            self._delete_worker = None

    def _discard_delete(self, worker: PermanentDeleteWorker) -> None:
        """A batch stopped before it started deleted nothing; report every entry as left in place."""
        if worker is self._delete_worker and not self._closing:
            self._delete_finished(worker, DeleteResult(refused=[(node.path, "cancelled") for node in worker.nodes]))

    def _delete_finished(self, worker: PermanentDeleteWorker, result: DeleteResult) -> None:
        """Show what happened (every refusal and failure stays visible) and take the removals out of the results."""
        if worker is not self._delete_worker:
            return
        worker.deleteLater()
        self._delete_worker = None
        self.refresh_bin_labels()
        if self._closing:
            return
        self.results.setEnabled(True)
        self._update_actions()
        changed = [*result.parents, *result.kept]  # captured before the removals leave the tree
        shown = False  # whether the results already show everything this batch did
        if result.removed and self._drop_removed(result.removed, worker.removed_summary, worker.counted_plan):
            shown = not (result.failed or result.refused or result.kept)
        summary = report_summary(result, self._unit)
        rows = report_rows(result)
        if rows:
            self._show_entry_report(PermanentReportDialog(rows, summary, self))
        if worker.journal_errors:
            QMessageBox.warning(self, tr("action_recent_actions"),
                                tr("journal_write_failed", reason="\n".join(worker.journal_errors)))
        self.statusBar().showMessage(summary, STATUS_TIMEOUT_MS)
        self._update_actions()
        self._follow.resume()  # the results show the removals; anything else is offered just below
        self._tell_peers(changed)
        if not shown:
            self._mark_changed(result.parents)

    def _drop_removed(self, nodes: Sequence[Node], removed: Summary | None, counted: HardLinkPlan | None) -> bool:
        """Take moved or deleted entries out of the results in place; False when only a rescan can show it.

        A scan counting hard links needs the worker's plan too: a name left alone of its group counts in
        full again. Its counted chart categories then follow from a summary on a worker.
        """
        self._analyser = None
        outcome = self.results.outcome
        counting = outcome is not None and outcome.result.hard_links is not None
        if outcome is None or removed is None or removed.now != outcome.now or (counting and counted is None):
            return False
        self.results.forget(nodes, removed=removed, counted=counted if counting else None)
        if counting:
            self._start_analysis(outcome.result.root, with_capacity=False)
        return True

    def _tell_peers(self, folders: Iterable[Node]) -> None:
        """After a Trash move, permanent delete or Undo here, other tabs offer only the folders it changed.

        Their readers were stopped for the operation like this tab's; without this each tab following
        changes read its whole root again afterwards, and a tab not following showed old sizes silently.
        """
        if self._operations is None:
            return
        paths = {path for folder in folders if (path := folder.path) is not None}
        for window in self._operations.windows:
            if window is not self and not window._closing:
                window._changed_elsewhere(paths)

    def _changed_elsewhere(self, paths: Iterable[str]) -> None:
        """Another tab changed entries in the folders ``paths``: follow on, and offer the folders here."""
        self._follow.resume()
        outcome = self.results.outcome
        if outcome is None:
            return
        found = [folder for path in paths if (folder := folder_holding(outcome.result.root, path)) is not None]
        if found:
            self._mark_changed(found)

    def _proposal_current(self, proposal: RecurringReview) -> bool:
        status = proposal.check()
        if status is None:
            return True
        QMessageBox.warning(self, tr("action_recurring"), tr("recurring_refused",
                            status=tr("recurring_status_" + status)))
        return False

    def _confirm_copy_trash(self, nodes: list[Node], copies: CopyApproval) -> QMessageBox.StandardButton:
        selected = set(nodes)
        question = QMessageBox(QMessageBox.Icon.Question, tr("trash_confirm_title"), "",
                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self)
        question.setTextFormat(Qt.TextFormat.PlainText)
        question.setText(self._trash_question(nodes) + "\n\n" + tr("copy_trash_confirm")
                         + ("\n\n" + tr("copy_redirect") if copies.redirect else ""))
        items = [proof.item for proof in copies.proofs if proof.item.node in selected]
        if items:
            set_lazy_details(question, lambda: "\n\n".join(f"{item.source}\n→ {item.destination}" for item in items))
        question.setDefaultButton(QMessageBox.StandardButton.No)
        return question.exec()

    def _review_cleanup(self, nodes: list[Node], reasons: dict[Node, CleanupGroup], root: Node) -> list[Node]:
        dialog = CleanupReview(nodes, reasons, self._protected, self._unit, root, self)
        self._path_dialogs.add(dialog)
        self._update_actions()
        try:
            return dialog.selected_nodes() if dialog.exec() == QDialog.DialogCode.Accepted else []
        finally:
            dialog.shutdown()
            self._path_dialogs.discard(dialog)
            self._update_actions()
            dialog.deleteLater()

    def _trash_finished(self, result: MoveResult) -> None:
        worker = self._trash_worker
        if worker is not None:
            worker.deleteLater()
        self._trash_worker = None
        self.refresh_bin_labels()
        if self._closing:
            self._report_copy_errors(result)
            return
        self.results.setEnabled(True)
        self._update_actions()
        moved, failed = result.moved, result.failed
        summary = result.summary or MoveSummary(len(moved), len(result.skipped), len(failed),
                                               sum(node.size for node in moved),
                                               journal_errors=len(result.journal_errors),
                                               copy_errors=len(result.copy_errors))
        moved_size = format_size(summary.moved_bytes, self._unit)
        outcome = self.results.outcome
        self.results.completion.show_summary(summary, outcome.result.root if outcome is not None else None,
                                             outcome.capacity if outcome is not None else None)
        changed = [*(node.parent for node in moved if node.parent is not None), *result.parents]
        shown = False  # whether the results already show everything this batch did
        if moved and self._drop_removed(moved, worker.removed_summary if worker is not None else None,
                                        worker.counted_plan if worker is not None else None):
            shown = not (failed or result.skipped or result.copy_errors)
        if failed:
            self._show_failed(result)
        if result.skipped:
            self._show_skipped(result.skipped)
        if result.journal_errors:
            QMessageBox.warning(self, tr("action_recent_actions"),
                                tr("journal_write_failed", reason="\n".join(result.journal_errors)))
        self._report_copy_errors(result)
        done = tr("trash_batch_done", moved=format_count(len(moved)), skipped=format_count(len(result.skipped)),
                  failed=format_count(len(failed)), size=moved_size)
        unavailable = self._undo.offer(worker)
        self.statusBar().showMessage(done + ("\n" + unavailable if unavailable else ""), STATUS_TIMEOUT_MS)
        self._update_actions()
        self._follow.resume()  # the results show the moves; anything else is offered just below
        self._tell_peers(changed)
        if not shown:
            self._mark_changed(result.parents)

    def _show_failed(self, result: MoveResult) -> None:
        """Keep brief warnings; retain all large/limited diagnostic details in a lazy report."""
        failed = result.failed
        if not failed:
            return
        reports = (result.holders.get(node) for node in failed)
        brief = len(failed) <= _LISTED_NAMES and all(
            report is None or (not report.error and len(report.holders) <= _LISTED_NAMES) for report in reports)
        if brief:
            message = (tr("trash_failed", name=failed[0].name) if len(failed) == 1 else
                       tr("trash_failed_many", count=format_count(len(failed)), names=self._name_lines(failed)))
            text = message + self._holder_lines(result)
            if len(text) <= _MAX_REFUSAL_NOTICE and "<" not in text and ">" not in text:
                QMessageBox.warning(self, tr("trash_confirm_title"), text)
                return
        # 1k failures: the old 431k-character label took 2.10 s and omitted query errors.
        self._show_entry_report(FailedEntriesDialog(failed, result.holders, self))

    def _report_copy_errors(self, result: MoveResult | None) -> None:
        if result is not None and result.copy_errors:
            report = QMessageBox(QMessageBox.Icon.Warning, tr("menu_move_drive"), "",
                                 QMessageBox.StandardButton.Ok, self)
            report.setTextFormat(Qt.TextFormat.PlainText)
            report.setText(tr("copy_errors"))
            errors = list(result.copy_errors)
            set_lazy_details(report, lambda: "\n\n".join(
                tr("copy_" + phase + "_failed", source=source, destination=destination, reason=reason)
                for source, destination, phase, reason in errors))
            report.exec()

    def _holder_lines(self, result: MoveResult) -> str:
        lines = []
        for node, report in result.holders.items():
            if report.holders:
                names = ", ".join(tr("trash_holder", name=holder.name, pid=str(holder.pid))
                                  for holder in report.holders[:_LISTED_NAMES])
                lines.append(tr("trash_holders", path=node.path, programs=names))
            if report.incomplete or report.error:
                lines.append(tr("trash_holders_limited", path=node.path))
        return "\n\n" + "\n".join(lines) if lines else ""

    def _rescan_after_trash(self) -> None:
        """Read the next changed folder again, once the user asked (or while Follow changes is on).

        Until then the folders only stay on offer in the notice: a scan the user did not ask for kept
        the window busy after every operation, and again after the next dialog was closed.
        """
        if not self._trash_rescans:
            self._refreshing = False
        self._update_refresh_notice()
        if not self._refreshing and not self._follow.enabled:
            return
        if (self._closing or self.operation_busy or self._worker is not None
                or self._undo.available or not self._trash_rescans):
            return
        node = self._trash_rescans.pop(0)
        exact = node in self._exact_rescans
        self._exact_rescans.discard(node)
        root = self.results.tree_model.root
        if root is not None and node.is_in(root):
            if exact:
                self.rescan_folder(node, exact_allocation=True)
            else:
                self.rescan_folder(node)
        if self._worker is None:
            if self._trash_rescans:
                QTimer.singleShot(0, self._rescan_after_trash)
            else:
                self._refreshing = False
                self._update_refresh_notice()

    def _confirm_protected(self, nodes: list[Node], question_key: str = "protected_question") -> bool:
        """The first of two questions when system or program folders are among ``nodes``: True to go on."""
        guarded = [(node, found) for node in nodes if (found := protection_of(node.path, self._protected)) is not None]
        if not guarded:
            return True
        lines = [f"• {node.path} — {tr(f'protected_{found.reason}')}" for node, found in guarded[:_LISTED_NAMES]]
        if len(guarded) > _LISTED_NAMES:
            lines.append(tr("trash_more", count=format_count(len(guarded) - _LISTED_NAMES)))
        question = tr(question_key, count=format_count(len(guarded)), names="\n".join(lines))
        answer = confirm_entry_move(self, tr("protected_title"), question, protected=True)
        return answer == QMessageBox.StandardButton.Yes

    def _trash_question(self, nodes: list[Node]) -> str:
        size = format_size(sum(node.size for node in nodes), self._unit)
        if len(nodes) == 1:
            return tr("trash_confirm", name=nodes[0].name, size=size)
        return tr("trash_confirm_many", count=format_count(len(nodes)), size=size, names=self._name_lines(nodes))

    def _name_lines(self, nodes: list[Node]) -> str:
        """The biggest of ``nodes`` one per line with their sizes, then how many more there are."""
        ordered = sorted(nodes, key=lambda node: node.size, reverse=True)
        lines = [f"• {node.name} ({format_size(node.size, self._unit)})" for node in ordered[:_LISTED_NAMES]]
        if len(ordered) > _LISTED_NAMES:
            lines.append(tr("trash_more", count=format_count(len(ordered) - _LISTED_NAMES)))
        return "\n".join(lines)

    def _show_in_chart(self, node: Node) -> None:
        self.results.charts.set_view_root(node)
        self.results.tabs.setCurrentIndex(CHART_TAB)

    def _find(self) -> None:
        if self.pages.currentIndex() == RESULTS_PAGE and self.results.outcome is not None:
            self.results.show_search()

    def _run_action(self, key: str, run: Callable[[], object]) -> None:
        """Run a menu action, or say why it waits for the running scan or operation (``_WAIT_FOR_SCAN``)."""
        waits = key in _WAIT_FOR_SCAN or key in _WAIT_FOR_OPERATION
        if waits and self._explain_busy(self._actions[key].text(), scan=key in _WAIT_FOR_SCAN):
            return
        run()

    def _explain_busy(self, action: str, *, scan: bool = True) -> bool:
        """Whether ``action`` has to wait (a scan, with ``scan``, or a source operation); if so, say so."""
        if self._closing:
            return False
        scanning = scan and self._worker is not None
        if not scanning and not self.operation_busy:
            return False
        show_busy(self, action, scanning=scanning)
        return True

    def _trash_selected(self) -> None:
        if self.pages.currentIndex() == RESULTS_PAGE:
            self.move_to_trash(self.results.focused_selection())

    def _delete_selected(self) -> None:
        if self.pages.currentIndex() != RESULTS_PAGE:
            return
        if self.results.in_suggestions():  # the user picks what to delete; FileTree's suggestions never feed it
            self.statusBar().showMessage(tr("permanent_not_suggestions"), STATUS_TIMEOUT_MS)
            return
        self.delete_permanently(self.results.focused_selection())

    def _selection_changed(self, node: Node | None) -> None:
        self._update_folder_context()
        picked = self.results.selected_nodes()
        if len(picked) > 1:
            size = format_size(sum(entry.size for entry in outermost(picked)), self._unit)
            self.statusBar().showMessage(tr("status_selected_many", count=format_count(len(picked)), size=size))
            return
        if node is None:
            self.statusBar().clearMessage()
            return
        size = format_size(node.size, self._unit)
        if node.parent is None:
            self.statusBar().showMessage(tr("status_selected_root", name=node.name, size=size))
            return
        self.statusBar().showMessage(tr("status_selected", name=node.name, size=size,
                                        share=format_share(node.share_of_parent())))

    # --- export -----------------------------------------------------------

    # --- settings, language, units ----------------------------------------

    @property
    def size_unit(self) -> str:
        """The unit sizes are shown in."""
        return self._unit

    def set_unit(self, unit: str) -> None:
        """Show sizes in ``unit`` and remember it."""
        self._unit = unit
        self.settings.setValue("unit", unit)
        self.results.set_unit(unit)
        self.welcome.set_unit(unit)
        self._unit_actions[unit].setChecked(True)
        self.size_unit_changed.emit(unit)

    def change_language(self, code: str) -> None:
        """Switch every text to another language and remember it."""
        set_language(code)
        apply_qt_translation(code)
        self.settings.setValue("language", code)
        self._language_changed()

    def retranslate(self) -> None:
        """Re-read every translated text."""
        apply_language_font(current_language())
        self.setWindowTitle(tr("app_title_admin") if elevation.is_elevated() else tr("app_title"))
        for key, action in self._actions.items():
            text = key if key.startswith("permanent_") else f"action_{key}"
            action.setText(tr(text))
            action.setToolTip(tr(f"{text}_tip"))
            action.setStatusTip(tr(f"{text}_tip"))
        self._reclaim_action.setText(tr("reclaim_action"))
        self._reclaim_action.setToolTip(tr("reclaim_action_tip"))
        self._reclaim_action.setStatusTip(tr("reclaim_action_tip"))
        if elevation.supported() and not elevation.compiled():
            for key in ("elevate", "ask_admin"):
                tip = tr(f"action_{key}_tip") + "\n" + tr("elevate_python_tip")
                self._actions[key].setToolTip(tip)
                self._actions[key].setStatusTip(tip)
        for key, menu in self._menus.items():
            menu.setTitle(tr(key))
        for unit, action in self._unit_actions.items():
            action.setText(tr("unit_auto") if unit == AUTO_UNIT else unit)
        self.path_edit.setPlaceholderText(tr("path_placeholder"))
        self._render_scan_scope()
        self.path_edit.setAccessibleName(tr("overview_path"))
        self._scan_path.setText(tr("overview_scan_path"))
        self._scan_path.setToolTip(tr("overview_scan_path_tip"))
        self.welcome.retranslate()
        self.results.retranslate()
        self.theme_menu.retranslate()
        self.text_size_menu.retranslate()
        self._undo.retranslate()
        self._updates.retranslate()
        self._follow.retranslate()
        self._language_actions[current_language()].setChecked(True)

    def _remember(self, path: str) -> None:
        recent = [path, *(folder for folder in self._recent() if os.path.normcase(folder) != os.path.normcase(path))]
        self.settings.setValue("recent", recent[:_MAX_RECENT])
        self.welcome.set_recent(recent)

    def _recent(self) -> list[str]:
        value = self.settings.value("recent", [])
        if isinstance(value, str):
            return [value]
        return [str(item) for item in value] if isinstance(value, list) else []

    def _restore(self) -> None:
        geometry = self.settings.value("geometry")
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)
        splitter = self.settings.value("splitter")
        if isinstance(splitter, QByteArray):
            self.results.restore_splitter(splitter)
        self._actions["hidden"].setChecked(read_flag(self.settings, "include_hidden", True))
        self._actions["ask_admin"].setChecked(read_flag(self.settings, ASK_ADMIN_KEY, True))
        self._actions["gentle"].setChecked(read_flag(self.settings, "gentle_scan", False))
        self._actions["auto_cpu"].setChecked(read_flag(self.settings, AUTO_CPU_KEY, True))
        self._actions["mft_scan"].setChecked(read_flag(self.settings, MFT_SCAN_KEY, True))
        with QSignalBlocker(self._actions["check_updates"]):
            self._actions["check_updates"].setChecked(self._updates.enabled())
        self._actions["capture_file_times"].setChecked(read_flag(self.settings, "capture_file_times", False))
        self._actions["capture_owners"].setChecked(read_flag(self.settings, "capture_owners", False))
        self._actions["exact_allocation"].setChecked(read_flag(self.settings, "exact_allocation", False))
        self._actions["count_hard_links"].setChecked(read_flag(self.settings, "count_hard_links", False))
        self._actions["follow_changes"].setChecked(read_flag(self.settings, "follow_changes", False))
        self._unit_actions[self._unit].setChecked(True)
        self.results.set_unit(self._unit)
        self.welcome.set_unit(self._unit)
        self.welcome.set_recent(self._recent())

    def closeEvent(self, event: QCloseEvent) -> None:
        """Cancel first; retain the window until zero-time joins permit safe destruction."""
        if self._close_ready:
            super().closeEvent(event)
            return
        if self._close_waiting:
            event.ignore()
            return
        self._close_waiting = True
        self._closing = True
        self.setEnabled(False)
        self.statusBar().showMessage(tr("closing_workers"))
        self._shutdown(wait=False)
        workers = tuple(self.findChildren(QThread))
        if all(worker.wait(0) for worker in workers):
            self._finish_close()
            super().closeEvent(event)
            return
        event.ignore()
        after_threads(workers, self._resume_close, self)

    def _resume_close(self) -> None:
        self._finish_close()
        self.close()

    def _finish_close(self) -> None:
        self._shutdown(wait=True)
        self._close_ready = True
        self.shutdown_finished.emit()

    def _shutdown(self, *, wait: bool) -> None:
        """Invalidate all replies; optional joins are used only after the closing fence has completed."""
        self._closing = True
        self._forget_changed()
        self._update_folder_context()
        self._live_timer.stop()
        self._folder_drops.shutdown(wait=wait)
        self.welcome.shutdown(wait=wait)
        self._follow.shutdown(wait=wait)
        self._updates.shutdown(wait=wait)
        self._undo.shutdown(wait=wait)
        for dialog in (*self._path_dialogs, *self._settings_dialogs):
            dialog.shutdown(wait=wait)
            if wait:
                dialog.reject()
        self._bin_labels.shutdown(wait=wait)
        if self._trash_worker is not None:
            worker = self._trash_worker
            worker.cancel(discard_results=True)
            if wait:
                wait_for(worker)
                self._trash_worker = None
                self._report_copy_errors(worker.result)
        self._stop_delete(wait=wait)
        self.stop_scan(wait=wait)
        for worker in self._scan_workers.copy():
            worker.cancel()
            if wait:
                wait_for(worker)
        self.results.search.stop(wait=wait)
        self.results.duplicates.stop(wait=wait)
        self.results.cleanup.stop(wait=wait)
        self.results.users.stop(wait=wait)
        self.results.changes.stop(wait=wait)
        self.results.details.stop(wait=wait)
        self.results.wait_for_lists(wait=wait)
        for capture in self._captures.copy():
            capture.cancel()
        if not wait:
            return
        for worker in self._analysers.copy():
            wait_for(worker)
        for worker in self._exports.copy():  # a file being written is finished, never left half-written
            wait_for(worker)
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter", self.results.splitter.saveState())
        if self._scan_defaults is None:
            self.settings.setValue("include_hidden", self._actions["hidden"].isChecked())

    # --- drag and drop ----------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Qt: accept a folder reference as Copy so the source must keep its files."""
        if event.possibleActions() & Qt.DropAction.CopyAction and _drop_paths(event.mimeData().urls()):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """Qt: scan a copied folder reference, never acknowledge a source-removing Move."""
        paths = _drop_paths(event.mimeData().urls())
        if paths and event.possibleActions() & Qt.DropAction.CopyAction:
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            self._folder_drops.request(paths)
        else:
            event.ignore()

    # --- building ---------------------------------------------------------

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802 - Qt's name
        """Qt: repaint action icons when the theme (palette) changes."""
        super().changeEvent(event)
        if event.type() == QEvent.Type.PaletteChange and hasattr(self, "_actions"):
            self._paint_action_icons()

    def _connect(self) -> None:
        self.results.details.history_requested.connect(self.show_history)
        self.results.details.budget_requested.connect(self._show_context_budget)
        self.results.completion.records_requested.connect(self.show_recent_actions)
        self.results.completion.undo_requested.connect(self._undo.undo)
        self.results.completion.rescan_requested.connect(self.start_scan)
        self._undo.timer.timeout.connect(self._update_actions)
        self.welcome.drives_changed.connect(self._update_actions)
        self.results.duplicates.link_requested.connect(self.show_duplicate_links)
        self.results.cleanup.review_requested.connect(self.move_to_trash)
        self.results.cleanup.reclaim_requested.connect(self.show_reclaim)
        self.welcome.choose_folder_requested.connect(self.choose_folder)
        self.welcome.scan_requested.connect(self.start_scan)
        self.welcome.presets_requested.connect(self.configure_scan_presets)
        self.welcome.scan_all_requested.connect(self.scan_all_drives)
        self.welcome.overview_requested.connect(self.show_volumes)
        self.welcome.bins_requested.connect(self.show_bins)
        self.welcome.bin_refresh_requested.connect(self.refresh_bin_labels)
        self.results.cleanup.bin_refresh_requested.connect(self.refresh_bin_labels)
        self.results.cleanup.bins_requested.connect(self.show_bins)
        self.results.refresh_notice.requested.connect(self.refresh_changed)
        self.results.scan_bar.stop_requested.connect(self.stop_scan)
        self.results.scan_bar.pause_requested.connect(self.pause_scan)
        self.results.node_menu_requested.connect(self.show_menu_for)
        self.results.chart_menu_requested.connect(lambda node, picked, point:
                                                  self.show_menu_for(node, picked, point, chart=True))
        self.results.apply_chart_settings({key: self.settings.value(key) for key in _CHART_SETTINGS
                                           if self.settings.contains(key)})
        self.results.chart_setting_changed.connect(self.settings.setValue)
        self.results.search.set_saved(saved_searches(self.settings))
        self.results.search.saved_changed.connect(
            lambda searches: self.settings.setValue(SEARCHES_KEY, json.dumps(searches, ensure_ascii=False)))
        self.results.compare_failed.connect(
            lambda reason: QMessageBox.warning(self, tr("compare_title"), tr("compare_failed", reason=reason)))
        self.results.selection_changed.connect(self._selection_changed)
        self.results.charts.mode_changed.connect(lambda _mode: self._update_actions())
        self.results.tabs.currentChanged.connect(lambda _tab: self._update_actions())
        self.results.elevate_requested.connect(self.restart_as_admin)

    # --- dialogs ----------------------------------------------------------

    def folder_context(self) -> FolderContext:
        """Resolve current selection against its owning scan without walking source descendants."""
        if self._closing or self._worker is not None or self.operation_busy:
            return FolderContext(None, "folder_context_closing" if self._closing else "folder_context_busy")
        outcome = self.results.outcome
        if outcome is None:
            return FolderContext(None, "folder_context_empty")
        root = outcome.result.root
        if root.path is None:
            return FolderContext(None, "folder_context_virtual")
        selected = self.results.selected_node() or root
        if not selected.is_in(root) or selected.is_link:
            return FolderContext(None, "folder_context_link" if selected.is_link else "folder_context_stale")
        folder = selected if selected.is_dir else selected.parent
        if folder is None or folder.is_link or folder.path is None:
            return FolderContext(None, "folder_context_stale")
        return FolderContext(folder)

    def _update_folder_context(self) -> None:
        context = self.folder_context()
        self.results.details.set_folder_context(context.node.path if context.node is not None else "",
                                               context.reason, budget_available=self._budget_show is not None)

    def _show_context_budget(self) -> None:
        context = self.folder_context()
        if context.node is not None and self._budget_show is not None:
            self._budget_show(context.node.path)


def _drop_paths(urls: list) -> tuple[str, ...]:
    return tuple(os.path.normpath(url.toLocalFile()) for url in urls if url.isLocalFile() and url.toLocalFile())


def _movable(nodes: Sequence[Node]) -> list[Node]:
    """What moving ``nodes`` to the Recycle Bin really moves: the outermost entries, never the scanned folder."""
    return outermost(node for node in nodes if node.parent is not None)

