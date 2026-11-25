"""File → Compare computers: saved scans side by side, with a CSV or HTML report; never any file operation."""

from __future__ import annotations

import os
import threading
from collections.abc import Sequence

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from je_file_tree.core.compare import SavedScanError
from je_file_tree.core.export import export_table_csv
from je_file_tree.core.formatting import format_count, format_size
from je_file_tree.core.report import Report, ReportTable, write_html
from je_file_tree.core.scan_overview import (
    DEFAULT_DEPTH,
    MAX_LABEL,
    MAX_SCANS,
    ImportedScan,
    Overview,
    import_scan,
    overview,
    unique_label,
)
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.list_transfer import install_copy
from je_file_tree.gui.scan_worker import wait_for
from je_file_tree.gui.text_scale import text_scaled
from je_file_tree.gui.window_fit import fit_window
from je_file_tree.gui.worker_lifecycle import WorkerDialog

_MAX_DEPTH = 50
_SORT = Qt.ItemDataRole.UserRole


class OverviewWorker(QThread):
    """Read new files, then put every scan side by side."""

    ready = Signal(object, object)

    def __init__(self, scans: Sequence[ImportedScan], files: Sequence[str], depth: int, parent: QWidget) -> None:
        super().__init__(parent)
        self.scans, self.files, self.depth = list(scans), list(files), depth
        self.cancel = threading.Event()

    def run(self) -> None:
        """Emit the overview (None when no scan is left) and the files that could not be read."""
        scans, failed = list(self.scans), []
        for file in self.files:
            if self.cancel.is_set():
                return
            try:
                imported = import_scan(file)
            except (OSError, SavedScanError) as error:
                failed.append(f"{file}: {error}")
                continue
            label = unique_label(imported.label, [scan.label for scan in scans])
            scans.append(ImportedScan(label, imported.scan))
        result = overview(scans, depth=self.depth, cancel=self.cancel) if scans else None
        if not self.cancel.is_set():
            self.ready.emit(result, failed)


class _Number(QTableWidgetItem):
    def __lt__(self, other: QTableWidgetItem) -> bool:
        return self.data(_SORT) < other.data(_SORT)


class ScanOverviewDialog(WorkerDialog):
    """Add, name and remove saved scans; the table and the reports show recorded sizes only."""

    def __init__(self, unit: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("action_scan_overview"))
        fit_window(self, 1100, 620)
        self.unit, self._closed = unit, False
        self._scans: list[ImportedScan] = []
        self._overview: Overview | None = None
        self._current: OverviewWorker | None = None
        self._running: set[OverviewWorker] = set()
        hint = QLabel(tr("overview_scans_hint"))
        hint.setWordWrap(True)
        self.list = QListWidget()
        self.list.setMaximumHeight(text_scaled(110))
        self.list.setAccessibleName(tr("overview_scans_list"))
        self.list.currentRowChanged.connect(lambda _row: self._update_buttons())
        self.add, self.rename, self.remove = (QPushButton(tr(f"overview_scans_{key}"))
                                              for key in ("add", "rename", "remove"))
        self.add.clicked.connect(self._choose_files)
        self.rename.clicked.connect(self._rename)
        self.remove.clicked.connect(self._remove)
        self.depth = QSpinBox()
        self.depth.setRange(1, _MAX_DEPTH)
        self.depth.setValue(DEFAULT_DEPTH)
        self.depth.setPrefix(tr("overview_scans_depth") + " ")
        self.depth.valueChanged.connect(lambda _value: self._refresh([]))
        self.table = QTableWidget(0, 0)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        install_copy(self.table)
        self.status = QLabel(tr("overview_scans_empty"))
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.csv, self.html = QPushButton(tr("overview_scans_csv")), QPushButton(tr("overview_scans_html"))
        self.csv.clicked.connect(lambda: self._export("csv"))
        self.html.clicked.connect(lambda: self._export("html"))
        self._assemble(hint)
        self._update_buttons()

    def _assemble(self, hint: QLabel) -> None:
        side = QVBoxLayout()
        for button in (self.add, self.rename, self.remove):
            button.setAutoDefault(False)
            side.addWidget(button)
        side.addWidget(self.depth)
        side.addStretch(1)
        top = QHBoxLayout()
        top.addWidget(self.list, 1)
        top.addLayout(side)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        bottom = QHBoxLayout()
        for button in (self.csv, self.html):
            button.setAutoDefault(False)
            bottom.addWidget(button)
        bottom.addWidget(close, 1)
        layout = QVBoxLayout(self)
        layout.addWidget(hint)
        layout.addLayout(top)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.status)
        layout.addLayout(bottom)

    # --- scans ----------------------------------------------------------------

    def _choose_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, tr("overview_scans_add"), "", tr("json_filter"))
        self.add_files(files)

    def add_files(self, files: Sequence[str]) -> None:
        """Read more saved scans on a worker, up to the limit."""
        room = MAX_SCANS - len(self._scans)
        if files:
            self._refresh(list(files[:room]), dropped=len(files) - room)

    def _rename(self) -> None:
        row = self.list.currentRow()
        if not 0 <= row < len(self._scans):
            return
        label, accepted = QInputDialog.getText(self, tr("overview_scans_rename"), tr("overview_scans_label"),
                                               text=self._scans[row].label)
        others = [scan.label for index, scan in enumerate(self._scans) if index != row]
        if accepted and label.strip():
            self._scans[row] = ImportedScan(unique_label(label[:MAX_LABEL], others), self._scans[row].scan)
            self._refresh([])

    def _remove(self) -> None:
        row = self.list.currentRow()
        if 0 <= row < len(self._scans):
            del self._scans[row]
            self._refresh([])

    def _refresh(self, files: list[str], *, dropped: int = 0) -> None:
        if self._current is not None:
            files = [*self._current.files, *files]
            self._current.cancel.set()
        worker = OverviewWorker(self._scans, files, self.depth.value(), self)
        worker.ready.connect(lambda result, failed: self._ready(worker, result, failed, dropped))
        worker.finished.connect(lambda: self._running.discard(worker))
        worker.finished.connect(worker.deleteLater)
        self._current = worker
        self._running.add(worker)
        self.status.setText(tr("overview_scans_reading"))
        self._update_buttons()
        worker.start()

    def _ready(self, worker: OverviewWorker, result: Overview | None, failed: list[str], dropped: int) -> None:
        if self._closed or worker is not self._current:
            return
        self._current, self._overview = None, result
        self._scans = list(result.scans) if result is not None else []
        self._fill()
        parts = [tr("overview_scans_empty") if result is None else
                 tr("overview_scans_summary", shown=format_count(len(result.rows)), count=format_count(result.count))]
        if dropped > 0:
            parts.append(tr("overview_scans_limit", limit=str(MAX_SCANS)))
        if failed:
            parts.append(tr("overview_scans_failed") + "\n" + "\n".join(failed[:MAX_SCANS]))
        self.status.setText("\n".join(parts))
        self._update_buttons()

    # --- the table and reports ---------------------------------------------------

    def _header(self) -> list[str]:
        return [tr("column_folder"), *(scan.label for scan in self._scans), tr("overview_scans_spread")]

    def _fill(self) -> None:
        row = self.list.currentRow()
        self.list.clear()
        for scan in self._scans:
            item = QListWidgetItem(tr("overview_scans_item", label=scan.label, saved=scan.scan.saved or "—",
                                      size=format_size(scan.scan.size, self.unit)))
            item.setToolTip(scan.scan.root or tr("multi_roots"))
            self.list.addItem(item)
        self.list.setCurrentRow(min(row, len(self._scans) - 1))
        rows = self._overview.rows if self._overview is not None else ()
        header = self._header()
        self.table.setSortingEnabled(False)
        self.table.clear()
        self.table.setColumnCount(len(header))
        self.table.setHorizontalHeaderLabels(header)
        self.table.setRowCount(len(rows))
        for number, line in enumerate(rows):
            self.table.setItem(number, 0, QTableWidgetItem(line.path or tr("overview_scans_total")))
            for column, size in enumerate((*line.sizes, line.spread), start=1):
                self.table.setItem(number, column, self._size_item(size))
        self.table.setColumnWidth(0, text_scaled(380))
        self.table.setSortingEnabled(True)

    def _size_item(self, size: int | None) -> QTableWidgetItem:
        item = _Number("—" if size is None else format_size(size, self.unit))
        item.setData(_SORT, -1 if size is None else size)
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return item

    def _export(self, kind: str) -> None:
        result = self._overview
        if result is None:
            return
        target, _ = QFileDialog.getSaveFileName(self, tr(f"overview_scans_{kind}"), f"computers.{kind}",
                                                tr(f"{kind}_filter"))
        if not target:
            return
        try:
            if kind == "csv":
                export_table_csv(self._header(), [[line.path, *("" if size is None else str(size) for size in
                                                                line.sizes), str(line.spread)]
                                                  for line in result.rows], target)
            else:
                write_html(self._report(result), [], target)
        except OSError as error:
            QMessageBox.warning(self, tr("export_title"), tr("export_failed", reason=str(error)))
            return
        self.status.setText(tr("export_done", count=format_count(len(result.rows)), path=os.path.normpath(target)))

    def _report(self, result: Overview) -> Report:
        scans = ReportTable(tr("overview_scans_list"),
                            (tr("overview_scans_label"), tr("column_path"), tr("history_time"), tr("column_size")),
                            tuple((scan.label, scan.scan.root or tr("multi_roots"), scan.scan.saved,
                                   format_size(scan.scan.size, self.unit)) for scan in result.scans),
                            len(result.scans))
        folders = ReportTable(tr("column_folders"), tuple(self._header()),
                              tuple((line.path or tr("overview_scans_total"),
                                     *("—" if size is None else format_size(size, self.unit)
                                       for size in (*line.sizes, line.spread))) for line in result.rows),
                              result.count)
        return Report(tr("action_scan_overview"), tr("overview_scans_hint"), (scans, folders))

    def _update_buttons(self) -> None:
        chosen = 0 <= self.list.currentRow() < len(self._scans)
        idle = self._current is None
        self.add.setEnabled(len(self._scans) < MAX_SCANS)
        self.rename.setEnabled(chosen and idle)
        self.remove.setEnabled(chosen and idle)
        for button in (self.csv, self.html):
            button.setEnabled(idle and self._overview is not None)

    # --- closing ----------------------------------------------------------------

    def shutdown(self, *, wait: bool = True) -> None:
        """Invalidate queued replies and join every owned worker."""
        self._closed, self._current = True, None
        for worker in self._running.copy():
            worker.cancel.set()
            if wait:
                wait_for(worker)

    def done(self, result: int) -> None:
        """Join background work before closing."""
        if self.defer_done(result):
            return
        self.shutdown()
        super().done(result)
