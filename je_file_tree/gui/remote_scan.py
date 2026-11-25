"""File → Scan a remote folder: measure another computer over SSH; the result is a saved scan, not entries."""

from __future__ import annotations

import json
import os

from PySide6.QtCore import QSettings, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from je_file_tree.core.formatting import format_count, format_size, format_time
from je_file_tree.core.remote_scan import (
    RemoteProgress,
    RemoteResult,
    RemoteScan,
    RemoteScanError,
    RemoteScanStoppedError,
    RemoteTarget,
)
from je_file_tree.gui.i18n import format_duration, tr
from je_file_tree.gui.list_transfer import install_copy
from je_file_tree.gui.scan_worker import wait_for
from je_file_tree.gui.text_scale import text_scaled
from je_file_tree.gui.window_fit import fit_window
from je_file_tree.gui.worker_lifecycle import WorkerDialog

REMOTE_KEY = "remote_scan_last"  # host, user, port and path only; there is no secret to keep
_SSH_PORT = 22


class RemoteScanWorker(QThread):
    """Connect and measure off the GUI thread; emits exactly one outcome."""

    progressed = Signal(object)
    succeeded = Signal(object)
    failed = Signal(str)
    stopped = Signal()

    def __init__(self, target: RemoteTarget, parent: QWidget) -> None:
        super().__init__(parent)
        self.scan = RemoteScan(target)

    def run(self) -> None:
        """Thread body."""
        try:
            result = self.scan.run(self.progressed.emit)
        except RemoteScanStoppedError:
            self.stopped.emit()
        except (RemoteScanError, OSError, ValueError) as error:
            self.failed.emit(str(error) or type(error).__name__)
        else:
            self.succeeded.emit(result)


class RemoteScanDialog(WorkerDialog):
    """Nothing connects until Scan; the result can be saved and compared, never opened, moved or removed."""

    compare_requested = Signal(str)

    def __init__(self, settings: QSettings, unit: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("action_remote_scan"))
        fit_window(self, 860, 600)
        self.settings, self.unit, self._closed = settings, unit, False
        self.worker: RemoteScanWorker | None = None
        self.result_: RemoteResult | None = None
        self.saved = ""
        self.host, self.user, self.path = QLineEdit(), QLineEdit(), QLineEdit(".")
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(_SSH_PORT)
        self.user.setPlaceholderText(tr("remote_user_default"))
        self.path.setPlaceholderText(".")
        self.start, self.stop = QPushButton(tr("remote_start")), QPushButton(tr("action_stop"))
        self.save, self.compare = QPushButton(tr("remote_save")), QPushButton(tr("remote_compare"))
        self.start.clicked.connect(self.begin)
        self.stop.clicked.connect(self.cancel)
        self.save.clicked.connect(self._save)
        self.compare.clicked.connect(self._compare)
        self.status = QLabel()
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([tr("column_path"), tr("column_size"), tr("column_modified")])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setColumnWidth(0, text_scaled(520))
        install_copy(self.table)
        self._assemble()
        self._restore()
        self._update()

    def _assemble(self) -> None:
        hint = QLabel(tr("remote_hint"))
        hint.setWordWrap(True)
        form = QFormLayout()
        for key, field in (("host", self.host), ("user", self.user), ("port", self.port), ("path", self.path)):
            label = QLabel(tr(f"remote_{key}"))
            label.setBuddy(field)
            field.setAccessibleName(tr(f"remote_{key}"))
            form.addRow(label, field)
        row = QHBoxLayout()
        for button in (self.start, self.stop, self.save, self.compare):
            button.setAutoDefault(False)
            row.addWidget(button)
        row.addStretch(1)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(hint)
        layout.addLayout(form)
        layout.addLayout(row)
        layout.addWidget(self.status)
        layout.addWidget(QLabel(tr("remote_largest")))
        layout.addWidget(self.table, 1)
        layout.addWidget(close)

    def _restore(self) -> None:
        try:
            last = json.loads(str(self.settings.value(REMOTE_KEY, "")))
            target = RemoteTarget(last["host"], last["path"], last["user"], last["port"])
        except (ValueError, KeyError, TypeError, RecursionError):
            return
        self.host.setText(target.host)
        self.user.setText(target.user)
        self.port.setValue(target.port)
        self.path.setText(target.path)

    @property
    def running(self) -> bool:
        """Whether a connection is being made or used."""
        return self.worker is not None

    def begin(self) -> None:
        """Connect to what the form names; an unusable form is explained and changes nothing."""
        if self.running:
            return
        try:
            target = RemoteTarget(self.host.text().strip(), self.path.text().strip() or ".", self.user.text().strip(),
                                  self.port.value())
        except ValueError:
            self.status.setText(tr("remote_invalid"))
            return
        self.settings.setValue(REMOTE_KEY, json.dumps({"host": target.host, "user": target.user, "port": target.port,
                                                       "path": target.path}))
        self.result_, self.saved = None, ""
        self.table.setRowCount(0)
        worker = RemoteScanWorker(target, self)
        worker.progressed.connect(self._progress)
        worker.succeeded.connect(self._done)
        worker.failed.connect(lambda reason: self._ended(tr("remote_failed", reason=reason)))
        worker.stopped.connect(lambda: self._ended(tr("scan_cancelled")))
        self.worker = worker
        self.status.setText(tr("remote_connecting", host=target.host))
        self._update()
        worker.start()

    def cancel(self) -> None:
        """End the connection."""
        if self.worker is not None:
            self.worker.scan.stop()
        self.stop.setEnabled(False)

    def _counts(self, counts: RemoteProgress) -> str:
        return tr("remote_counts", folders=format_count(counts.folders), files=format_count(counts.files),
                  size=format_size(counts.bytes, self.unit), unread=format_count(counts.unread))

    def _progress(self, counts: RemoteProgress) -> None:
        if self.running and not self._closed:
            self.status.setText(self._counts(counts))

    def _done(self, result: RemoteResult) -> None:
        self.result_ = result
        self.table.setRowCount(len(result.largest))
        for row, file in enumerate(result.largest):
            for column, text in enumerate((file.path, format_size(file.size, self.unit), format_time(file.modified))):
                self.table.setItem(row, column, QTableWidgetItem(text))
        self._ended(tr("remote_done", label=result.label, counts=self._counts(result.progress),
                       duration=format_duration(result.seconds)))

    def _ended(self, text: str) -> None:
        worker, self.worker = self.worker, None
        if worker is not None:
            wait_for(worker)
            worker.deleteLater()
        self.status.setText(text)
        self._update()

    def _update(self) -> None:
        for field in (self.host, self.user, self.port, self.path):
            field.setEnabled(not self.running)
        self.start.setEnabled(not self.running)
        self.stop.setEnabled(self.running)
        self.save.setEnabled(self.result_ is not None)
        self.compare.setEnabled(bool(self.saved))

    def _save(self) -> None:
        if self.result_ is None:
            return
        target, _ = QFileDialog.getSaveFileName(self, tr("remote_save"), f"{self.host.text().strip()}.json",
                                                tr("json_filter"))
        if not target:
            return
        try:
            self.result_.save(target)
        except OSError as error:
            QMessageBox.warning(self, tr("export_title"), tr("export_failed", reason=str(error)))
            return
        self.saved = target
        self.status.setText(tr("remote_saved", path=os.path.normpath(target)))
        self._update()

    def _compare(self) -> None:
        if self.saved:
            self.compare_requested.emit(self.saved)
            self.accept()

    def shutdown(self, *, wait: bool = True) -> None:
        """End the connection and join the worker."""
        self._closed = True
        if self.worker is not None:
            self.worker.scan.stop()
            if wait:
                wait_for(self.worker)

    def done(self, result: int) -> None:
        """Join the worker before closing."""
        if self.defer_done(result):
            return
        self.shutdown()
        super().done(result)
