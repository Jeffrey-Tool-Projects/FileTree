"""The question, worker and report of *Delete permanently*.

``MainWindow.delete_permanently`` is the only caller: it asks with ``confirm_permanent_delete``
every time and is the only place that creates a ``PermanentDeleteWorker``. Nothing here picks
entries; the worker deletes exactly the approved ones through ``core.permanent_delete``.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Sequence

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import QMessageBox, QWidget

from je_file_tree.core.analysis import AnalysisCancelledError, Summary, summarise
from je_file_tree.core.formatting import format_count, format_size
from je_file_tree.core.node import Node
from je_file_tree.core.operation_journal import OperationJournal, OperationOutcome, OperationRecord
from je_file_tree.core.permanent_delete import PENDING, DeleteResult, delete_entries
from je_file_tree.core.protected import Protection
from je_file_tree.gui.entry_report import EntryReportDialog
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.strings import EN
from je_file_tree.gui.tables import Column, _TableModel

LISTED = 8  # entries named in the question; the rest are counted
JOURNAL_REASON = "permanent_delete"


def confirm_permanent_delete(parent: QWidget, title: str, text: str) -> QMessageBox.StandardButton:
    """Ask Yes/No in plain text; No is the default, and Escape or closing the box answer No."""
    dialog = QMessageBox(QMessageBox.Icon.Warning, title, "",
                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, parent)
    dialog.setTextFormat(Qt.TextFormat.PlainText)
    dialog.setText(text)
    dialog.setDefaultButton(QMessageBox.StandardButton.No)
    dialog.setEscapeButton(QMessageBox.StandardButton.No)
    try:
        answer = QMessageBox.StandardButton(dialog.exec())
        return answer if answer == QMessageBox.StandardButton.Yes else QMessageBox.StandardButton.No
    finally:
        dialog.deleteLater()


def permanent_question(nodes: Sequence[Node], unit: str) -> str:
    """The question: the entries (largest first, at most ``LISTED`` named), count, total size, no undo."""
    size = format_size(sum(node.size for node in nodes), unit)
    if len(nodes) == 1:
        text = tr("permanent_confirm", name=nodes[0].name, size=size, path=nodes[0].path)
    else:
        ordered = sorted(nodes, key=lambda node: node.size, reverse=True)
        lines = [f"• {node.path} ({format_size(node.size, unit)})" for node in ordered[:LISTED]]
        if len(ordered) > LISTED:
            lines.append(tr("trash_more", count=format_count(len(ordered) - LISTED)))
        text = tr("permanent_confirm_many", count=format_count(len(nodes)), size=size, names="\n".join(lines))
    if any(node.is_dir and not node.is_link for node in nodes):
        text += "\n\n" + tr("permanent_confirm_folders")
    return text


def refuse_managed(parent: QWidget, nodes: Sequence[Node]) -> None:
    """Explain, before any question, that Windows-managed entries are never deleted by FileTree."""
    lines = [f"• {node.path}" for node in nodes[:LISTED]]
    if len(nodes) > LISTED:
        lines.append(tr("trash_more", count=format_count(len(nodes) - LISTED)))
    notice = QMessageBox(QMessageBox.Icon.Warning, tr("permanent_title"), "", QMessageBox.StandardButton.Ok, parent)
    notice.setTextFormat(Qt.TextFormat.PlainText)
    notice.setText(tr("permanent_managed", names="\n".join(lines)))
    try:
        notice.exec()
    finally:
        notice.deleteLater()


def reason_text(reason: str) -> str:
    """The translated explanation of a refusal reason key (an unknown key is shown as it is)."""
    key = f"permanent_skip_{reason}"
    return tr(key) if key in EN else reason


def report_rows(result: DeleteResult) -> list[tuple[str, str]]:
    """Every entry left in place or not deleted, with why, in the order it happened."""
    rows = [(path, reason_text(reason)) for path, reason in result.refused]
    rows.extend((path, tr("permanent_pending") if detail == PENDING else tr("permanent_failed", reason=detail))
                for path, detail in result.failed)
    return rows


def report_summary(result: DeleteResult, unit: str) -> str:
    """One line: what was deleted and how many entries were left or failed."""
    return tr("permanent_done", removed=format_count(result.removed_entries),
              size=format_size(result.removed_bytes, unit), refused=format_count(len(result.refused)),
              failed=format_count(len(result.failed)))


class PermanentReportModel(_TableModel[tuple[str, str]]):
    """Paths and reasons as plain text, with no file-operation roles."""

    def build_columns(self) -> Sequence[Column[tuple[str, str]]]:
        """Full path and the reason it is still there."""
        return (Column("column_path", lambda row: row[0], lambda row: row[0]),
                Column("column_problem", lambda row: row[1], lambda row: row[1]))


class PermanentReportDialog(EntryReportDialog):
    """Read-only list of everything left in place or not deleted; closing it approves nothing."""

    def __init__(self, rows: Sequence[tuple[str, str]], summary: str, parent: QWidget | None = None) -> None:
        model = PermanentReportModel()
        model.set_rows(rows)
        super().__init__(model, tr("permanent_report_title"), summary, parent)


class PermanentDeleteWorker(QThread):
    """Delete one approved batch off the GUI thread; cancellation is checked between entries."""

    progressed = Signal(int)
    done = Signal(object)

    def __init__(self, root: Node, nodes: list[Node], places: list[Protection],
                 approvals: dict[Node, Protection | None], journal: OperationJournal | None,
                 parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.root, self.nodes = root, nodes
        self._places, self._approvals, self._journal = places, approvals, journal
        self._cancel = threading.Event()
        self._summary_cancel = threading.Event()
        self._events: dict[Node, OperationRecord] = {}
        self.summary_now = time.time()
        self.removed_summary: Summary | None = None
        self.journal_errors: list[str] = []
        self.result: DeleteResult | None = None

    @property
    def cancelled(self) -> bool:
        """Whether stopping was asked for."""
        return self._cancel.is_set()

    def cancel(self, *, discard_results: bool = False) -> None:
        """Stop after the entry being removed; closing may also skip the view statistics."""
        self._cancel.set()
        if discard_results:
            self._summary_cancel.set()

    def run(self) -> None:
        """Thread body: record the approval, delete, record each outcome; the GUI updates on ``done``."""
        if self._record_approval():
            result = delete_entries(self.root, self.nodes, places=self._places, approved=self._approvals,
                                    cancel=self._cancel, progress=self.progressed.emit, finished=self._record)
        else:
            result = DeleteResult(refused=[(node.path, "journal") for node in self.nodes],
                                  parents=[node.parent for node in self.nodes if node.parent is not None])
        self._prepare_statistics(result)
        self.result = result
        self.done.emit(result)

    def _record_approval(self) -> bool:
        if self._journal is None:
            return True
        batch = uuid.uuid4().hex
        self._events = {node: OperationRecord.approved(batch, node, JOURNAL_REASON) for node in self.nodes}
        return self._append(list(self._events.values()))

    def _record(self, node: Node, status: str, detail: str) -> None:
        event = self._events.get(node)
        if self._journal is not None and event is not None and not self._append(
                [event.finished(OperationOutcome(status, detail))]):
            self._cancel.set()  # keep what happened, but delete nothing more without a record

    def _append(self, records: list[OperationRecord]) -> bool:
        try:
            self._journal.append(records)
        except (OSError, ValueError) as error:
            self.journal_errors.append(str(error))
            return False
        return True

    def _prepare_statistics(self, result: DeleteResult) -> None:
        """Totals of the removed subtrees for the view, read here so the GUI thread need not walk them."""
        if not result.removed or self.root.accounting is not None:
            return
        try:
            self.removed_summary = summarise(Node("", True, children=result.removed), limit=0,
                                             now=self.summary_now, cancel=self._summary_cancel)
        except AnalysisCancelledError:
            return  # closing: the outcome is kept, the view statistics are not needed
