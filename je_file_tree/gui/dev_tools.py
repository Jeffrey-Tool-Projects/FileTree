"""What development tools keep in the scan, with their own commands to copy; nothing here runs or removes."""

from __future__ import annotations

import threading
from collections.abc import Sequence
from typing import Any

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from je_file_tree.core.dev_tools import ToolUse, dev_tools
from je_file_tree.core.formatting import format_count, format_size
from je_file_tree.core.node import Node
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.list_transfer import install_copy
from je_file_tree.gui.scan_worker import wait_for
from je_file_tree.gui.tables import SORT_ROLE, Column, _TableModel
from je_file_tree.gui.text_scale import text_scaled
from je_file_tree.gui.tree_model import NODE_ROLE
from je_file_tree.gui.window_fit import fit_window
from je_file_tree.gui.worker_lifecycle import WorkerDialog


class DevToolsModel(_TableModel[ToolUse]):
    """One row per tool."""

    def build_columns(self) -> Sequence[Column[ToolUse]]:
        """Tool, sizes, number of stores and the tool's own commands."""
        return (Column("dev_tools_tool", lambda row: row.tool.name, lambda row: row.tool.name.lower()),
                Column("column_size", lambda row: format_size(row.size, self.unit), lambda row: row.size,
                       numeric=True),
                Column("column_allocated", lambda row: format_size(row.allocated, self.unit),
                       lambda row: row.allocated, numeric=True),
                Column("dev_tools_stores", lambda row: format_count(len(row.nodes)), lambda row: len(row.nodes),
                       numeric=True),
                Column("dev_tools_inspect", lambda row: row.tool.inspect, lambda row: row.tool.inspect),
                Column("dev_tools_clean", _clean, _clean))

    def extra_data(self, row: ToolUse, role: int) -> Any:
        """The largest store for selection, and every store's path as the tooltip."""
        if role == NODE_ROLE:
            return max(row.nodes, key=lambda node: node.size)
        return "\n".join(node.path or node.name for node in row.nodes) if role == Qt.ItemDataRole.ToolTipRole else None


def _clean(row: ToolUse) -> str:
    return row.tool.clean or tr("dev_tools_automatic")


class DevToolsWorker(QThread):
    """Survey the recorded tree off the GUI thread; a cancelled survey emits nothing."""

    ready = Signal(object)

    def __init__(self, root: Node, parent: QWidget) -> None:
        super().__init__(parent)
        self.root, self.cancel = root, threading.Event()

    def run(self) -> None:
        """Emit what was found if the survey completed."""
        result = dev_tools(self.root, cancel=self.cancel)
        if result is not None and not self.cancel.is_set():
            self.ready.emit(result)


class DevToolsDialog(WorkerDialog):
    """Read-only: copy a command to run it yourself, or double-click to select the largest store in the tree."""

    selected = Signal(object)

    def __init__(self, root: Node, unit: str, *, partial: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("action_dev_tools"))
        fit_window(self, 1080, 520)
        self._partial, self._closed = partial, False
        self.model = DevToolsModel(self)
        self.model.unit = unit
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSortRole(SORT_ROLE)
        self.proxy.setSourceModel(self.model)
        self.view = QTableView()
        self.view.setModel(self.proxy)
        self.view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.view.setSortingEnabled(True)
        self.view.sortByColumn(2, Qt.SortOrder.DescendingOrder)
        self.view.doubleClicked.connect(self._select)
        for column, width in enumerate((120, 100, 100, 80, 260, 300)):
            self.view.setColumnWidth(column, text_scaled(width))
        install_copy(self.view)
        self.view.selectionModel().currentChanged.connect(lambda *_indexes: self._update_buttons())
        hint = QLabel(tr("dev_tools_hint"))
        hint.setWordWrap(True)
        self.status = QLabel(tr("dev_tools_reading"))
        self.status.setWordWrap(True)
        self.copy_inspect = QPushButton(tr("dev_tools_copy_inspect"))
        self.copy_clean = QPushButton(tr("dev_tools_copy_clean"))
        self.copy_inspect.clicked.connect(lambda: self._copy(lambda use: use.tool.inspect))
        self.copy_clean.clicked.connect(lambda: self._copy(lambda use: use.tool.clean))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        row = QHBoxLayout()
        for button in (self.copy_inspect, self.copy_clean):
            button.setAutoDefault(False)
            row.addWidget(button)
        row.addWidget(buttons, 1)
        layout = QVBoxLayout(self)
        layout.addWidget(hint)
        layout.addWidget(self.view, 1)
        layout.addWidget(self.status)
        layout.addLayout(row)
        self._update_buttons()
        self.worker = DevToolsWorker(root, self)
        self.worker.ready.connect(self._show)
        self.worker.start()

    def _show(self, found: list[ToolUse]) -> None:
        if self._closed or self.worker.cancel.is_set():
            return
        self.model.set_rows(found)
        text = (tr("dev_tools_none") if not found else
                tr("dev_tools_summary", count=format_count(len(found)),
                   size=format_size(sum(use.allocated for use in found), self.model.unit)))
        partial = self._partial or any(use.incomplete for use in found)
        self.status.setText(text + (" " + tr("special_partial") if partial else ""))
        self._update_buttons()

    def _chosen(self) -> ToolUse | None:
        index = self.view.currentIndex()
        return self.model.row_at(self.proxy.mapToSource(index).row()) if index.isValid() else None

    def _update_buttons(self) -> None:
        use = self._chosen()
        self.copy_inspect.setEnabled(use is not None)
        self.copy_clean.setEnabled(use is not None and bool(use.tool.clean))

    def _copy(self, command) -> None:
        use = self._chosen()
        if use is not None and command(use):
            QApplication.clipboard().setText(command(use))
            self.status.setText(tr("dev_tools_copied", command=command(use)))

    def _select(self, index: QModelIndex) -> None:
        node = index.data(NODE_ROLE)
        if isinstance(node, Node):
            self.selected.emit(node)
            self.accept()

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
