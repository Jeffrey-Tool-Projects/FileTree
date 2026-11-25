"""Files that tend to cause trouble, in a read-only, cancellable list; double-click selects one in the tree."""

from __future__ import annotations

import os
import threading
from collections.abc import Sequence
from typing import Any

from PySide6.QtCore import QSortFilterProxyModel, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from je_file_tree.core.formatting import format_count, format_size, format_time
from je_file_tree.core.node import Node
from je_file_tree.core.problem_files import KINDS, ProblemEntry, ProblemFiles, problem_files
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.list_transfer import install_copy
from je_file_tree.gui.scan_worker import wait_for
from je_file_tree.gui.tables import SORT_ROLE, Column, _TableModel
from je_file_tree.gui.text_scale import text_scaled
from je_file_tree.gui.tree_model import NODE_ROLE
from je_file_tree.gui.window_fit import fit_window
from je_file_tree.gui.worker_lifecycle import WorkerDialog


class ProblemFilesModel(_TableModel[ProblemEntry]):
    """What was found about each entry, and where a dead link points."""

    def build_columns(self) -> Sequence[Column[ProblemEntry]]:
        """Name, findings, link target, size, time and folder."""
        return (Column("column_name", lambda row: row.node.name, lambda row: row.node.name.lower()),
                Column("problem_files_found", _found, _found),
                Column("problem_files_target", lambda row: row.target, lambda row: row.target.lower()),
                Column("column_size", lambda row: format_size(row.node.size, self.unit), lambda row: row.node.size,
                       numeric=True),
                Column("column_modified", lambda row: format_time(row.node.modified), lambda row: row.node.modified),
                Column("column_folder", lambda row: os.path.dirname(row.node.path or ""),
                       lambda row: row.node.path or ""))

    def extra_data(self, row: ProblemEntry, role: int) -> Any:
        """Expose the scanned node for activation and a full path tooltip."""
        if role == NODE_ROLE:
            return row.node
        return row.node.path if role == Qt.ItemDataRole.ToolTipRole else None


def _found(row: ProblemEntry) -> str:
    return ", ".join(tr(f"problem_files_{kind}") for kind in row.kinds)


class ProblemFilesWorker(QThread):
    """Survey off the GUI thread; a cancelled survey emits nothing."""

    ready = Signal(object)

    def __init__(self, root: Node, parent: QWidget) -> None:
        super().__init__(parent)
        self.root, self.cancel = root, threading.Event()

    def run(self) -> None:
        """Emit the findings if the survey completed."""
        result = problem_files(self.root, cancel=self.cancel)
        if result is not None and not self.cancel.is_set():
            self.ready.emit(result)


class ProblemFilesDialog(WorkerDialog):
    """Inspect the completed scan; nothing here changes a file."""

    selected = Signal(object)

    def __init__(self, root: Node, unit: str, *, partial: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("action_problem_files"))
        fit_window(self, 1100, 580)
        self._partial, self._closed = partial, False
        self._result: ProblemFiles | None = None
        self.model = ProblemFilesModel(self)
        self.model.unit = unit
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSortRole(SORT_ROLE)
        self.proxy.setSourceModel(self.model)
        self.view = QTableView()
        self.view.setModel(self.proxy)
        self.view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.view.setSortingEnabled(True)
        self.view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.view.doubleClicked.connect(self._select)
        for column, width in enumerate((200, 200, 220, 90, 140, 340)):
            self.view.setColumnWidth(column, text_scaled(width))
        install_copy(self.view)
        self.filter = QComboBox()
        self.filter.setAccessibleName(tr("problem_files_found"))
        self.filter.addItem(tr("problem_files_all"), None)
        for kind in KINDS:
            self.filter.addItem(tr(f"problem_files_{kind}"), kind)
        self.filter.currentIndexChanged.connect(lambda _index: self._fill())
        hint = QLabel(tr("problem_files_hint"))
        hint.setWordWrap(True)
        self.status = QLabel(tr("problem_files_reading"))
        self.status.setWordWrap(True)
        self.stop_button = QPushButton(tr("action_stop"))
        self.stop_button.clicked.connect(self.stop)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        bar = QHBoxLayout()
        bar.addWidget(self.filter)
        bar.addStretch(1)
        bar.addWidget(self.stop_button)
        layout = QVBoxLayout(self)
        layout.addWidget(hint)
        layout.addLayout(bar)
        layout.addWidget(self.view, 1)
        layout.addWidget(self.status)
        layout.addWidget(buttons)
        self.worker = ProblemFilesWorker(root, self)
        self.worker.ready.connect(self._show)
        self.worker.start()

    def _show(self, result: ProblemFiles) -> None:
        if self._closed or self.worker.cancel.is_set():
            return
        self._result = result
        self.stop_button.setEnabled(False)
        for index, kind in enumerate(KINDS, start=1):
            self.filter.setItemText(index, f"{tr(f'problem_files_{kind}')} ({format_count(result.counts[kind])})")
        self._fill()
        text = tr("problem_files_summary", shown=format_count(len(result.rows)), count=format_count(result.count),
                  unknown=format_count(result.unknown_links))
        self.status.setText(text + (" " + tr("special_partial") if self._partial or result.incomplete else ""))

    def _fill(self) -> None:
        kind = self.filter.currentData()
        rows = self._result.rows if self._result is not None else []
        self.model.set_rows([row for row in rows if kind is None or kind in row.kinds])

    def _select(self, index) -> None:
        node = index.data(NODE_ROLE)
        if isinstance(node, Node):
            self.selected.emit(node)
            self.accept()

    def stop(self) -> None:
        """Cancel the survey; no incomplete list is presented as complete."""
        self.worker.cancel.set()
        self.stop_button.setEnabled(False)
        self.status.setText(tr("scan_cancelled"))

    def shutdown(self, *, wait: bool = True) -> None:
        """Invalidate queued replies and join the owned worker before destruction."""
        self._closed = True
        self.worker.cancel.set()
        if wait:
            wait_for(self.worker)

    def done(self, result: int) -> None:
        """Join background work before closing."""
        if self.defer_done(result):
            return
        self.shutdown()
        super().done(result)
