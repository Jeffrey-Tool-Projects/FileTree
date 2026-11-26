"""Actions, menus and the toolbar, and what is enabled when."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import QPushButton, QToolBar

from je_file_tree.core.trash_size import TrashUsage
from je_file_tree.gui import elevation, shell_integration
from je_file_tree.gui.bin_labels import bin_key
from je_file_tree.gui.change_watch import supported as follow_supported
from je_file_tree.gui.fluent_icons import palette_icon
from je_file_tree.gui.graphics_export import SVG_MODES
from je_file_tree.gui.i18n import LANGUAGES
from je_file_tree.gui.list_transfer import ListCapture
from je_file_tree.gui.text_size import TextSizeMenu
from je_file_tree.gui.themes import ThemeMenu
from je_file_tree.gui.updates import UpdateNotice
from je_file_tree.gui.window_settings import ASK_ADMIN_KEY, AUTO_CPU_KEY, MFT_SCAN_KEY, UNITS

_ACTION_ICONS = {"open": "folder", "rescan": "refresh", "stop": "stop", "help": "help"}


class WindowMenus:
    """Part of ``MainWindow``: actions, menus and the toolbar, and what is enabled when."""

    def _build_actions(self) -> None:
        self._updates = UpdateNotice(self.settings, self)
        self._captures: set[ListCapture] = set()
        definitions: list[tuple[str, QKeySequence | str | None, Callable[[], object]]] = [
            ("open", QKeySequence.StandardKey.Open, self.choose_folder),
            ("multi_scan", None, self.choose_roots),
            ("rescan", QKeySequence.StandardKey.Refresh, self.rescan),
            ("stop", "Esc", self.stop_scan),
            ("export_folders", None, lambda: self.export_results("folders")),
            ("export_largest", None, lambda: self.export_results("largest")),
            ("export_list", None, self.export_list),
            ("export_json", None, lambda: self.export_results("json")),
            ("export_chart_png", None, lambda: self.export_chart("png")),
            ("export_chart_svg", None, lambda: self.export_chart("svg")),
            ("print_view", QKeySequence.StandardKey.Print, self.print_current_view),
            ("export_view_pdf", None, self.export_view_pdf),
            ("export_report_html", None, lambda: self.export_report("html")),
            ("export_report_xlsx", None, lambda: self.export_report("xlsx")),
            ("trash", QKeySequence.StandardKey.Delete, self._trash_selected),
            ("permanent_delete", "Shift+Del", self._delete_selected),
            ("find", QKeySequence.StandardKey.Find, self._find),
            ("compare", None, self.choose_saved_scan),
            ("recent_actions", None, self.show_recent_actions),
            ("special_files", None, self.show_special_files),
            ("problem_files", None, self.show_problem_files),
            ("dev_tools", None, self.show_dev_tools),
            ("scan_overview", None, self.show_scan_overview),
            ("remote_scan", None, self.show_remote_scan),
            ("live_compare", None, self.compare_live_folders),
            ("git_history", None, self.show_git_history),
            ("history", None, self.show_history),
            ("recurring", None, self.show_recurring),
            ("history_settings", None, self.configure_history),
            ("scan_presets", None, self.configure_scan_presets),
            ("projects", None, self.show_projects),
            ("programs", None, self.show_programs),
            ("virtual_disks", None, self.show_virtual_disks),
            ("file_times", None, self.show_file_times),
            ("capture_file_times", None, lambda: None),
            ("capture_owners", None, lambda: None),
            ("exact_allocation", None, lambda: None),
            ("count_hard_links", None, lambda: None),
            ("follow_changes", None, lambda: None),
            ("background_monitor", None, self.configure_background),
            ("folder_budgets", None, self.show_folder_budgets),
            ("volumes", None, self.show_volumes),
            ("disks", None, self.show_disks),
            ("bins", None, self.show_bins),
            ("quit", "Ctrl+Q", self.quit_application),  # Windows has no standard Quit key
            ("hidden", None, lambda: self.settings.setValue("include_hidden", self._actions["hidden"].isChecked())),
            ("elevate", None, self.restart_as_admin),
            ("exclusions", None, self.edit_exclusions),
            ("cleanup_policy", None, self.edit_cleanup_policy),
            ("shell_integration", None, self.edit_shell_integration),
            ("settings", "Ctrl+,", self.show_settings),
            ("shortcuts", None, self.edit_shortcuts),
            ("palette", "Ctrl+K", self.show_palette),
            ("gentle", None, lambda: self.settings.setValue("gentle_scan", self._actions["gentle"].isChecked())),
            ("scan_workers", None, self.configure_workers),
            ("auto_cpu", None, lambda: self.settings.setValue(AUTO_CPU_KEY, self._actions["auto_cpu"].isChecked())),
            ("mft_scan", None, lambda: self.settings.setValue(MFT_SCAN_KEY, self._actions["mft_scan"].isChecked())),
            ("ask_admin", None, lambda: self.settings.setValue(ASK_ADMIN_KEY, self._actions["ask_admin"].isChecked())),
            ("help", QKeySequence.StandardKey.HelpContents, self.show_help),
            ("about", None, self.show_about),
            ("check_updates", None, lambda: None),
        ]
        for key, shortcut, handler in definitions:
            action = QAction(self)
            if shortcut is not None:
                action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(lambda _checked=False, run=handler, name=key: self._run_action(name, run))
            self._actions[key] = action
        self._reclaim_action = QAction(self)
        self._reclaim_action.triggered.connect(
            lambda _checked=False: self._explain_busy(self._reclaim_action.text()) or self.show_reclaim())
        self._configure_actions()

    def _configure_actions(self) -> None:
        self._actions["check_updates"].setCheckable(True)
        self._actions["check_updates"].toggled.connect(self._updates.configure)
        self._actions["follow_changes"].setCheckable(True)
        self._actions["follow_changes"].setEnabled(follow_supported())
        self._actions["follow_changes"].toggled.connect(self._follow.configure)
        self._actions["background_monitor"].setEnabled(False)
        self._actions["folder_budgets"].setEnabled(False)
        self._actions["recurring"].setEnabled(False)
        self._actions["hidden"].setCheckable(True)
        self._actions["ask_admin"].setCheckable(True)
        self._actions["gentle"].setCheckable(True)
        self._actions["auto_cpu"].setCheckable(True)
        self._actions["mft_scan"].setCheckable(True)
        self._actions["mft_scan"].setVisible(elevation.supported())
        self._actions["capture_file_times"].setCheckable(True)
        self._actions["capture_file_times"].toggled.connect(
            lambda checked: self.settings.setValue("capture_file_times", checked))
        self._actions["capture_owners"].setCheckable(True)
        self._actions["capture_owners"].setVisible(elevation.supported())
        self._actions["capture_owners"].toggled.connect(
            lambda checked: self.settings.setValue("capture_owners", checked))
        self._actions["exact_allocation"].setCheckable(True)
        self._actions["exact_allocation"].setVisible(elevation.supported())
        self._actions["exact_allocation"].toggled.connect(
            lambda checked: self.settings.setValue("exact_allocation", checked))
        self._actions["count_hard_links"].setCheckable(True)
        self._actions["count_hard_links"].toggled.connect(
            lambda checked: self.settings.setValue("count_hard_links", checked))
        self._actions["elevate"].setVisible(elevation.can_elevate())
        self._actions["ask_admin"].setVisible(elevation.supported())
        self._actions["shell_integration"].setVisible(shell_integration.supported())
        self._actions["programs"].setVisible(elevation.supported())

    def _build_menus(self) -> None:
        bar = self.menuBar()
        file_menu = bar.addMenu("")
        for key in ("open", "multi_scan", "rescan", "stop", "find"):
            file_menu.addAction(self._actions[key])
        export_menu = file_menu.addMenu("")
        for key in ("export_folders", "export_largest", "export_json", "export_chart_png", "export_chart_svg"):
            export_menu.addAction(self._actions[key])
        export_menu.addAction(self._actions["export_view_pdf"])
        export_menu.addAction(self._actions["export_list"])
        for key in ("export_report_html", "export_report_xlsx"):
            export_menu.addAction(self._actions[key])
        file_menu.addAction(self._actions["print_view"])
        file_menu.addAction(self._actions["compare"])
        for key in ("recent_actions", "special_files", "problem_files", "live_compare", "git_history", "projects",
                    "dev_tools", "scan_overview", "remote_scan", "history", "programs", "virtual_disks", "file_times",
                    "recurring", "folder_budgets"):
            file_menu.addAction(self._actions[key])
        file_menu.addSeparator()
        file_menu.addAction(self._reclaim_action)
        file_menu.addAction(self._actions["trash"])
        file_menu.addAction(self._actions["permanent_delete"])
        file_menu.addAction(self._actions["elevate"])
        file_menu.addSeparator()
        file_menu.addAction(self._actions["quit"])
        view_menu = bar.addMenu("")
        view_menu.addAction(self._actions["volumes"])
        view_menu.addAction(self._actions["disks"])
        view_menu.addAction(self._actions["bins"])
        unit_menu = view_menu.addMenu("")
        units = QActionGroup(self)
        for unit in UNITS:
            action = unit_menu.addAction(unit)
            action.setCheckable(True)
            units.addAction(action)
            action.triggered.connect(lambda _checked=False, chosen=unit: self.set_unit(chosen))
            self._unit_actions[unit] = action
        language_menu = view_menu.addMenu("")
        languages = QActionGroup(self)
        for code, name in LANGUAGES.items():
            action = language_menu.addAction(name)
            action.setCheckable(True)
            languages.addAction(action)
            action.triggered.connect(lambda _checked=False, chosen=code: self.change_language(chosen))
            self._language_actions[code] = action
        view_menu.addSeparator()
        self.theme_menu, self.text_size_menu = (ThemeMenu(view_menu, self.settings),
                                                TextSizeMenu(view_menu, self.settings))
        view_menu.addAction(self._actions["hidden"])
        view_menu.addAction(self._actions["exclusions"])
        view_menu.addAction(self._actions["ask_admin"])
        options_menu = bar.addMenu("")
        for key in ("settings", "shortcuts"):
            options_menu.addAction(self._actions[key])
        options_menu.addSeparator()
        for key in ("cleanup_policy", "gentle", "scan_workers", "auto_cpu", "mft_scan", "scan_presets",
                    "history_settings", "check_updates", "follow_changes", "background_monitor",
                    "capture_file_times", "capture_owners", "exact_allocation", "count_hard_links",
                    "shell_integration"):
            options_menu.addAction(self._actions[key])
        help_menu = bar.addMenu("")
        for key in ("palette", "help", "about"):
            help_menu.addAction(self._actions[key])
        self._menus = {"menu_file": file_menu, "menu_export": export_menu, "menu_view": view_menu,
                       "menu_unit": unit_menu, "menu_language": language_menu, "menu_help": help_menu,
                       "menu_options": options_menu}

    def _build_toolbar(self) -> None:
        toolbar = QToolBar()
        toolbar.setObjectName("main_toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.setIconSize(QSize(18, 18))
        self._paint_action_icons()
        toolbar.addAction(self._actions["open"])
        toolbar.addAction(self._actions["rescan"])
        toolbar.addAction(self._actions["stop"])
        toolbar.addSeparator()
        self.path_edit.setClearButtonEnabled(True)
        toolbar.addWidget(self.path_edit)
        self._scan_path = QPushButton()
        self._scan_path.clicked.connect(self.start_prepared_scan)
        self.path_edit.returnPressed.connect(self._scan_path.click)
        self.path_edit.textChanged.connect(self._path_input_changed)
        toolbar.addWidget(self._scan_path)
        toolbar.addSeparator()
        toolbar.addAction(self._actions["help"])
        self.addToolBar(toolbar)

    def _paint_action_icons(self) -> None:
        """Draw the tool bar's line icons in the current palette's text colour."""
        for key, name in _ACTION_ICONS.items():
            self._actions[key].setIcon(palette_icon(name, self.palette()))

    def _update_path_button(self) -> None:
        ready = (self.capture_scan_scope() is not None and not self._prepared_errors
                 and not self.operation_busy and not self._closing)
        self._scan_path.setEnabled(ready)

    def _update_actions(self) -> None:
        self._update_folder_context()
        self._update_path_button()
        if self.operation_busy:
            self.pending_source_workers()
        if self._operations is not None:
            self._operations.refresh(self)
        # Actions in _WAIT_FOR_SCAN / _WAIT_FOR_OPERATION stay enabled while a scan or an operation runs, so
        # that using one says why it waits (_run_action) instead of a greyed item doing nothing.
        scanning = self._worker is not None or self.operation_busy
        self._actions["elevate"].setEnabled(not self._closing and not self._settings_dialogs)
        self._actions["scan_presets"].setEnabled(not self._closing and not self._settings_dialogs)
        self.welcome.presets.setEnabled(self._actions["scan_presets"].isEnabled() and not scanning)
        self._actions["recurring"].setEnabled(self._recurring_show is not None)
        self._actions["stop"].setEnabled(scanning)
        for key in ("open", "multi_scan", "cleanup_policy", "live_compare", "volumes", "disks", "bins"):
            self._actions[key].setEnabled(True)
        self._actions["rescan"].setEnabled(bool(self._last_path or self._last_roots))
        # A running scan's live tree can be selected before there is an outcome: its actions explain the wait.
        self._update_result_actions(self.results.outcome is not None
                                    or scanning and self.results.tree_model.root is not None)
        self.welcome.scan_all.setEnabled(not scanning and bool(self.welcome.drive_rows))
        self._update_bin_buttons()
        self._update_refresh_notice()

    def _update_result_actions(self, shown: bool) -> None:
        """Enable the actions on the results on screen (``shown``); a running scan makes them explain instead."""
        for key in ("export_folders", "export_largest", "export_json", "export_chart_png", "find", "compare",
                    "print_view", "export_view_pdf", "special_files", "problem_files", "projects", "programs",
                    "dev_tools", "virtual_disks", "file_times"):
            self._actions[key].setEnabled(shown)
        self._actions["export_chart_svg"].setEnabled(shown and self.results.charts.mode in SVG_MODES)
        for key in ("export_report_html", "export_report_xlsx"):
            self._actions[key].setEnabled(shown and not self._analysers)
        self._actions["export_list"].setEnabled(shown and self.results.current_list() is not None)
        outcome = self.results.outcome
        virtual = outcome is not None and outcome.result.root.path is None
        for key in ("trash", "permanent_delete", "history", "git_history"):
            self._actions[key].setEnabled(shown and not virtual)
        self._reclaim_action.setEnabled(shown and not virtual)

    def _update_bin_buttons(self) -> None:
        ready = not self._closing and self._worker is None and not self.operation_busy
        idle = ready and not self._bin_labels.busy
        self.welcome.bin_refresh.setEnabled(idle)
        self.results.cleanup.bin_refresh.setEnabled(idle and self.results.outcome is not None)
        self.results.completion.set_actions(undo=ready and self._undo.available, rescan=ready)

    def refresh_bin_labels(self) -> None:
        """Refresh read-only drive totals off the GUI thread, retaining the current scan's scope."""
        if self._closing or self._worker is not None or self.operation_busy:
            return
        outcome = self.results.outcome
        self._bin_labels.refresh((outcome.result.root.path or "") if outcome is not None else "")

    def _bin_metadata_ready(self, rows: dict[str, TrashUsage], root: str) -> None:
        self.welcome.set_bin_metadata(rows)
        if self.results.outcome is not None:
            self.results.cleanup.set_bin_metadata(root, rows.get(bin_key(root)) if root else None)
