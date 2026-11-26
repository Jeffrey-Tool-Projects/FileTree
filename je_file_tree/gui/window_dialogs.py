"""The tools, reviews and settings opened from the menus."""

from __future__ import annotations

import os
from collections.abc import Sequence

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from je_file_tree import __version__
from je_file_tree.core.formatting import format_count
from je_file_tree.core.history import ScanHistory
from je_file_tree.gui import elevation, shell_integration
from je_file_tree.gui.bin_dialog import BinDialog
from je_file_tree.gui.cleanup_policy_dialog import CleanupPolicyDialog
from je_file_tree.gui.command_palette import CommandPalette, ShortcutsDialog
from je_file_tree.gui.dev_tools import DevToolsDialog
from je_file_tree.gui.disks_dialog import DisksDialog
from je_file_tree.gui.exclusions_dialog import ExclusionsDialog
from je_file_tree.gui.file_times import FileTimesDialog
from je_file_tree.gui.git_history import GitHistoryDialog
from je_file_tree.gui.help_dialog import HelpDialog
from je_file_tree.gui.history import HistoryDialog, HistorySettings, history_folder, history_limit
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.live_compare import LiveCompareDialog
from je_file_tree.gui.problem_files import ProblemFilesDialog
from je_file_tree.gui.programs import ProgramsDialog
from je_file_tree.gui.projects import ProjectsDialog
from je_file_tree.gui.recent_actions import RecentActions
from je_file_tree.gui.reclaim_dialog import ReclaimDialog, reclaim_sources
from je_file_tree.gui.remote_scan import RemoteScanDialog
from je_file_tree.gui.scan_overview import ScanOverviewDialog
from je_file_tree.gui.scan_presets import ScanPresetsDialog
from je_file_tree.gui.settings_dialog import SettingsDialog
from je_file_tree.gui.shell_dialog import ShellIntegrationDialog
from je_file_tree.gui.special_files import SpecialFilesDialog
from je_file_tree.gui.virtual_disks import VirtualDisksDialog
from je_file_tree.gui.volumes import VolumesDialog
from je_file_tree.gui.window_settings import CLEANUP_POLICY_KEY, STATUS_TIMEOUT_MS


class DialogActions:
    """Part of ``MainWindow``: the tools, reviews and settings opened from the menus."""

    def show_virtual_disks(self) -> None:
        """Own virtual-disk reviews and rebuild the full captured root after attempted compaction."""
        if self._worker is not None or self.operation_busy or self.results.outcome is None:
            return
        outcome = self.results.outcome
        dialog = VirtualDisksDialog(outcome.result.root, self._unit, self, partial=outcome.partial,
                                    journal=self._journal if outcome.result.root.path is not None else None)
        dialog.selected.connect(self.results.select_node)
        dialog.execution_requested.connect(self._undo.expire)
        self._path_dialogs.add(dialog)
        self._update_actions()
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            self._path_dialogs.discard(dialog)
            dialog.deleteLater()
            self._update_actions()
        if not self._closing and dialog.changed and self.results.outcome is outcome:
            self._analyser = None
            self.results.clear_capacity()
            self._bin_labels.refresh()
            self._mark_changed([outcome.result.root])
        elif self._trash_rescans:
            self._rescan_after_trash()

    def show_programs(self) -> None:
        """Review Windows registrations/game names against the current recorded tree on an owned worker."""
        if (not elevation.supported() or self._worker is not None or self.operation_busy
                or self.results.outcome is None):
            return
        outcome = self.results.outcome
        dialog = ProgramsDialog(outcome.result.root, self._unit, self, partial=outcome.partial)
        dialog.selected.connect(self.results.select_node)
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            dialog.deleteLater()

    def configure_history(self) -> None:
        """Persist enable/cap changes only after OK; the running scan retains its captured configuration."""
        dialog = HistorySettings(self.settings, self)
        try:
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.settings.setValue("history_enabled", dialog.enabled.isChecked())
                self.settings.setValue("history_limit_mib", dialog.limit.value())
        finally:
            dialog.deleteLater()

    def configure_scan_presets(self) -> None:
        """Manage named choices; loading changes inputs but never starts or replaces a scan."""
        if self._worker is not None or self.operation_busy or self._closing or self._settings_dialogs:
            return
        try:
            scope = self.capture_scan_scope()
            dialog = ScanPresetsDialog(self.settings, scope if isinstance(scope, str) else "",
                                       self._scan_options(), self)
        except (ValueError, TypeError, RecursionError):
            QMessageBox.warning(self, tr("action_scan_presets"), tr("presets_read_failed"))
            return
        self._settings_dialogs.add(dialog)
        self._update_actions()
        try:
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.chosen is not None and not self._closing:
                self._apply_scan_preset(dialog.chosen)
        finally:
            dialog.shutdown()
            self._settings_dialogs.discard(dialog)
            self._update_actions()
            dialog.deleteLater()

    def show_file_times(self) -> None:
        """Query optional recorded file dates on an owned worker, without opening scanned payloads."""
        if self._worker is not None or self.operation_busy or self.results.outcome is None:
            return
        outcome = self.results.outcome
        dialog = FileTimesDialog(outcome.result.root, self._unit, partial=outcome.partial, parent=self)
        dialog.selected.connect(self.results.select_node)
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            dialog.deleteLater()

    def show_history(self) -> None:
        """Review local history for the full current root and reuse the Changes worker for comparison."""
        context = self.folder_context()
        if context.node is None:
            return
        root = self.results.outcome.result.root
        store = ScanHistory(history_folder(), max_bytes=history_limit(self.settings) * 1024 * 1024)
        folder = context.node
        relative = os.path.relpath(folder.path, root.path)
        dialog = HistoryDialog(store, root.path, self._unit, self,
                               folder="" if relative == "." else relative, loaded_root=root)
        dialog.compare_requested.connect(self.results.compare_saved)
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            dialog.deleteLater()

    def show_bins(self) -> None:
        """Review OS bin metadata and exact-scope emptying after two explicit questions."""
        if self._worker is not None or self.operation_busy:
            return
        dialog = BinDialog(self._unit, self)
        requested: list[str] = []
        dialog.scan_requested.connect(requested.append)
        dialog.emptied.connect(self._bin_emptied)
        self._path_dialogs.add(dialog)
        self._update_actions()
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            self._path_dialogs.discard(dialog)
            self._update_actions()
            dialog.deleteLater()
            self.refresh_bin_labels()
        if requested and not self._closing:
            self.start_scan(requested[-1])

    def _bin_emptied(self, _root: str) -> None:
        self._analyser = None
        self.results.clear_capacity()

    def show_volumes(self) -> None:
        """Show mounted volumes and scan an explicitly activated root."""
        if self._worker is not None or self.operation_busy:
            return
        dialog = VolumesDialog(self._unit, self, settings=self.settings)
        dialog.scan_requested.connect(self.start_scan)
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            dialog.deleteLater()

    def show_disks(self) -> None:
        """Show the physical disks, their health and partitions; nothing on a disk is changed."""
        if self._worker is not None or self.operation_busy:
            return
        dialog = DisksDialog(self._unit, self)
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            dialog.deleteLater()

    def edit_exclusions(self) -> None:
        """Edit the folders to skip while scanning; they apply from the next scan."""
        dialog = ExclusionsDialog(self.exclusions(), self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.set_exclusions(dialog.patterns())
        self.statusBar().showMessage(tr("exclusions_saved", count=format_count(len(dialog.patterns()))),
                                     STATUS_TIMEOUT_MS)

    def show_settings(self) -> None:
        """Every setting in one window; it changes them through the menu actions."""
        dialog = SettingsDialog(self)
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()

    def edit_shortcuts(self) -> None:
        """Choose the keys of menu commands; every tab uses them."""
        dialog = ShortcutsDialog(self._shortcuts, self)
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()

    def show_palette(self) -> None:
        """Find a menu command by typing and run it exactly as its menu entry would."""
        dialog = CommandPalette(self.menuBar(), self)
        try:
            chosen = dialog.chosen if dialog.exec() == QDialog.DialogCode.Accepted else None
        finally:
            dialog.deleteLater()
        if chosen is not None:
            chosen.trigger()

    def edit_cleanup_policy(self) -> None:
        """Preview and save clean-up settings independently of scan exclusions."""
        if self._worker is not None or self.operation_busy:
            return
        dialog = CleanupPolicyDialog(self._cleanup_policy, self.results.tree_model.root, self._unit, self)
        try:
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._cleanup_policy = dialog.policy()
                self.settings.setValue(CLEANUP_POLICY_KEY, self._cleanup_policy.dumps())
                self.results.cleanup.set_policy(self._cleanup_policy)
                self.statusBar().showMessage(tr("policy_saved"), STATUS_TIMEOUT_MS)
        finally:
            dialog.shutdown()
            dialog.deleteLater()

    def edit_shell_integration(self) -> None:
        """Keep the native settings worker and modal guard owned until every request joins."""
        if (self._closing or self._settings_dialogs or self.operation_busy
                or not shell_integration.supported()):
            return
        dialog = ShellIntegrationDialog(self)
        self._settings_dialogs.add(dialog)
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            self._settings_dialogs.discard(dialog)
            dialog.deleteLater()

    def show_special_files(self) -> None:
        """Explain cloud and special file metadata without reading or downloading any contents."""
        outcome = self.results.outcome
        if outcome is None or self._worker is not None or self.operation_busy:
            return
        self._run_survey(SpecialFilesDialog(outcome.result.root, self._unit, parent=self,
                                            partial=outcome.partial or bool(outcome.result.errors)))

    def show_problem_files(self) -> None:
        """List empty files, dead links, long paths and unusable names among the scanned entries."""
        outcome = self.results.outcome
        if outcome is None or self._worker is not None or self.operation_busy:
            return
        self._run_survey(ProblemFilesDialog(outcome.result.root, self._unit, parent=self,
                                            partial=outcome.partial or bool(outcome.result.errors)))

    def show_remote_scan(self) -> None:
        """Measure a folder of another computer over SSH; its saved scan can then be compared."""
        dialog = RemoteScanDialog(self.settings, self._unit, self)
        chosen: list[str] = []
        dialog.compare_requested.connect(chosen.append)
        self._settings_dialogs.add(dialog)  # quitting from the tray ends the connection instead of waiting for it
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            self._settings_dialogs.discard(dialog)
            dialog.deleteLater()
        if chosen and not self._closing:
            self.show_scan_overview(chosen)

    def show_scan_overview(self, files: Sequence[str] = ()) -> None:
        """Put saved scans of several computers side by side; they grant no file operation here."""
        dialog = ScanOverviewDialog(self._unit, self)
        dialog.add_files(files)
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            dialog.deleteLater()

    def show_dev_tools(self) -> None:
        """Show what development tools keep in the scan and their own commands; nothing is run."""
        outcome = self.results.outcome
        if outcome is None or self._worker is not None or self.operation_busy:
            return
        self._run_survey(DevToolsDialog(outcome.result.root, self._unit, parent=self,
                                        partial=outcome.partial or bool(outcome.result.errors)))

    def _run_survey(self, dialog: SpecialFilesDialog | ProblemFilesDialog | DevToolsDialog) -> None:
        dialog.selected.connect(self.results.select_node)
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            dialog.deleteLater()

    def compare_live_folders(self) -> None:
        """Choose two existing folders for an independent read-only comparison."""
        if self._worker is not None or self.operation_busy:
            return
        left = QFileDialog.getExistingDirectory(self, tr("compare_choose_left"), self._last_path or "")
        if not left:
            return
        right = QFileDialog.getExistingDirectory(self, tr("compare_choose_right"), left)
        if not right:
            return
        dialog = LiveCompareDialog((left, right), self._unit, self)
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            dialog.deleteLater()

    def show_git_history(self) -> None:
        """Inspect the selected working folder's largest reachable Git history objects."""
        outcome = self.results.outcome
        if outcome is None or self._worker is not None or self.operation_busy:
            return
        node = self.results.selected_node() or outcome.result.root
        folder = node if node.is_dir else node.parent
        if folder is None or folder.path is None or folder.is_link:
            return
        if folder.name == ".git" and folder.parent is not None:
            folder = folder.parent
        dialog = GitHistoryDialog(folder.path, self._unit, self)
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            dialog.deleteLater()

    def show_projects(self) -> None:
        """Explain recorded project/generated bytes and review only current-policy eligible entries."""
        outcome = self.results.outcome
        if outcome is None or self._worker is not None or self.operation_busy:
            return
        dialog = ProjectsDialog(outcome.result.root, self._unit, self._cleanup_policy,
                                partial=outcome.partial, parent=self)
        dialog.selected.connect(self.results.select_node)
        dialog.review_requested.connect(self.move_to_trash)
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            dialog.deleteLater()

    def show_reclaim(self) -> None:
        """Plan how to free a chosen amount; the checked entries go only through ``move_to_trash``."""
        sources = reclaim_sources(self.results)
        if sources is None or sources.root.path is None or self._worker is not None or self.operation_busy:
            return
        dialog = ReclaimDialog(sources, self._unit, self)
        dialog.selected.connect(self.results.select_node)
        dialog.review_requested.connect(self.move_to_trash)

        def refresh() -> None:
            dialog.update_sources(reclaim_sources(self.results))

        self.results.cleanup.summary_changed.connect(refresh)
        try:
            dialog.exec()
        finally:
            self.results.cleanup.summary_changed.disconnect(refresh)
            dialog.deleteLater()

    def show_help(self) -> None:
        """Open the how-to-use window."""
        HelpDialog(self, self.text_size_menu).exec()

    def show_recent_actions(self) -> None:
        """Open the retained metadata trail, without proposing or restoring any entry."""
        dialog = RecentActions(self._journal, self)
        try:
            dialog.exec()
        finally:
            dialog.shutdown()
            dialog.deleteLater()

    def show_folder_budgets(self) -> None:
        """Open the shared manager even when no contextual folder is available."""
        if self._budget_show is None:
            return
        context = self.folder_context()
        self._budget_show(context.node.path if context.node is not None else "")

    def show_about(self) -> None:
        """Show the version."""
        QMessageBox.about(self, tr("action_about"), tr("about_text", version=__version__))
