"""Archive one scanned folder to a new ZIP file; moving the original stays a separate, asked-for step."""

from __future__ import annotations

import os
import threading
import time

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from je_file_tree.core.formatting import format_count, format_size
from je_file_tree.core.node import Node
from je_file_tree.core.zip_archive import (
    ArchiveProof,
    ArchiveRefusedError,
    ArchiveStoppedError,
    create_archive,
    plan_archive,
)
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.scan_worker import wait_for
from je_file_tree.gui.window_fit import fit_window
from je_file_tree.gui.worker_lifecycle import WorkerDialog

_REASONS = ("target", "exists", "inside", "name", "streams", "copy_unsupported", "folder_required", "verify")
_STEPS = 1000
_INTERVAL = .1  # seconds between two progress signals


class ZipWorker(QThread):
    """Check, pack, read back and publish off the GUI thread."""

    progressed = Signal(str, int)
    succeeded = Signal(object)
    refused = Signal(str, str)
    failed = Signal(str)
    stopped = Signal()

    def __init__(self, root: Node, node: Node, target: str, parent: QWidget) -> None:
        super().__init__(parent)
        self.root, self.node, self.target = root, node, target
        self.cancel = threading.Event()
        self._told = 0.0

    def run(self) -> None:
        """Emit exactly one outcome."""
        try:
            plan = plan_archive(self.root, self.node, self.target, self.cancel)
            proof = create_archive(plan, self._progress, self.cancel)
        except ArchiveStoppedError:
            self.stopped.emit()
        except ArchiveRefusedError as refusal:
            self.refused.emit(refusal.reason, refusal.path)
        except (OSError, ValueError) as error:
            if self.cancel.is_set():
                self.stopped.emit()
            else:
                self.failed.emit(str(error) or type(error).__name__)
        else:
            self.succeeded.emit(proof)

    def _progress(self, phase: str, done: int, total: int) -> None:
        now = time.monotonic()
        if now - self._told >= _INTERVAL or done >= total:
            self._told = now
            self.progressed.emit(phase, done * _STEPS // max(total, 1))


class ZipDialog(WorkerDialog):
    """Starts only on request; ``move_requested`` tells that the user then asked to move the original."""

    def __init__(self, root: Node, node: Node, target: str, unit: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("zip_title"))
        fit_window(self, 640, 320)
        self.root, self.node, self.target, self.unit = root, node, target, unit
        self.proof: ArchiveProof | None = None
        self.move_requested = False
        self._closed = False
        self.worker: ZipWorker | None = None
        facts = QLabel(tr("zip_facts", path=node.path or node.name, target=os.path.normpath(target),
                          files=format_count(node.file_count), size=format_size(node.size, unit)))
        facts.setTextFormat(Qt.TextFormat.PlainText)
        facts.setWordWrap(True)
        facts.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        hint = QLabel(tr("zip_hint"))
        hint.setWordWrap(True)
        self.bar = QProgressBar()
        self.bar.setRange(0, _STEPS)
        self.bar.setTextVisible(False)
        self.status = QLabel()
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        self.start, self.stop = QPushButton(tr("zip_start")), QPushButton(tr("action_stop"))
        self.move = QPushButton(tr("zip_move"))
        self.start.clicked.connect(self.begin)
        self.stop.clicked.connect(self.cancel)
        self.move.clicked.connect(self._ask_to_move)
        self.stop.setEnabled(False)
        self.move.setEnabled(False)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        row = QHBoxLayout()
        for button in (self.start, self.stop, self.move):
            button.setAutoDefault(False)
            row.addWidget(button)
        row.addWidget(close, 1)
        layout = QVBoxLayout(self)
        for widget in (facts, hint, self.bar, self.status):
            layout.addWidget(widget)
        layout.addStretch(1)
        layout.addLayout(row)

    def begin(self) -> None:
        """Start packing once."""
        if self.worker is not None and self.worker.isRunning() or self.proof is not None:
            return
        self.start.setEnabled(False)
        self.stop.setEnabled(True)
        self.status.setText(tr("zip_checking"))
        worker = ZipWorker(self.root, self.node, self.target, self)
        worker.progressed.connect(self._progress)
        worker.succeeded.connect(self._done)
        worker.refused.connect(self._refused)
        worker.failed.connect(lambda reason: self._ended(tr("zip_failed", reason=reason)))
        worker.stopped.connect(lambda: self._ended(tr("zip_stopped")))
        self.worker = worker
        worker.start()

    def cancel(self) -> None:
        """Ask the worker to stop; the temporary file is removed and nothing appears under the target name."""
        if self.worker is not None:
            self.worker.cancel.set()
        self.stop.setEnabled(False)

    def _progress(self, phase: str, step: int) -> None:
        if not self._closed and self.stop.isEnabled():
            self.bar.setValue(step)
            self.status.setText(tr(f"zip_{phase}"))

    def _done(self, proof: ArchiveProof) -> None:
        self.proof = proof
        self.stop.setEnabled(False)
        self.bar.setValue(_STEPS)
        self.move.setEnabled(not self._closed)
        self.status.setText(tr("zip_done", files=format_count(proof.plan.files),
                               size=format_size(proof.plan.bytes, self.unit),
                               archive=format_size(proof.size, self.unit)))

    def _refused(self, reason: str, path: str) -> None:
        self._ended(tr("zip_reason_" + (reason if reason in _REASONS else "changed"), path=path))

    def _ended(self, text: str) -> None:
        self.stop.setEnabled(False)
        self.start.setEnabled(True)
        self.bar.setValue(0)
        self.status.setText(text)

    def _ask_to_move(self) -> None:
        self.move_requested = self.proof is not None
        self.accept()

    def shutdown(self, *, wait: bool = True) -> None:
        """Stop and join the worker."""
        self._closed = True
        if self.worker is not None:
            self.worker.cancel.set()
            if wait:
                wait_for(self.worker)

    def done(self, result: int) -> None:
        """Join the worker before closing."""
        if self.defer_done(result):
            return
        self.shutdown()
        super().done(result)
