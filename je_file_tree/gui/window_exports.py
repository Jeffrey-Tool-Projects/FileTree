"""Saving, printing and reporting what the window shows."""

from __future__ import annotations

import os
from collections.abc import Callable

from PySide6.QtPrintSupport import QPrintDialog
from PySide6.QtWidgets import QAbstractItemView, QDialog, QFileDialog, QMessageBox

from je_file_tree.core import export
from je_file_tree.core.node import Node
from je_file_tree.gui.graphics_export import SVG_MODES, capture_svg, save_graphic
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.list_transfer import ListCapture, ListStream
from je_file_tree.gui.printing import print_view, save_view_pdf, view_printer
from je_file_tree.gui.report_dialog import ReportDialog
from je_file_tree.gui.scan_worker import ExportWorker
from je_file_tree.gui.window_settings import STATUS_TIMEOUT_MS


class ExportActions:
    """Part of ``MainWindow``: saving, printing and reporting what the window shows."""

    def export_report(self, kind: str) -> None:
        """Export a bounded whole-scan HTML or Excel report through an owned cancellable modal worker."""
        outcome = self.results.outcome
        if outcome is None or self._worker is not None or self.operation_busy or self._analysers:
            return
        target, _ = QFileDialog.getSaveFileName(self, tr("action_export_report_" + kind),
                                                f"report.{kind}", tr(kind + "_filter"))
        if not target:
            return
        try:
            dialog = ReportDialog(outcome, kind, target, self._unit, self.results.charts, self)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, tr("export_title"), tr("export_failed", reason=str(error)))
            return
        try:
            dialog.exec()
            if dialog.saved:
                self.settings.setValue("export_dir", os.path.dirname(target))
        finally:
            dialog.shutdown()
            dialog.deleteLater()

    def export_list(self) -> None:
        """Stream the active list in displayed order to CSV using bounded GUI capture and ExportWorker."""
        view = self.results.current_list()
        if view is None or self.results.outcome is None:
            return
        target, _ = QFileDialog.getSaveFileName(self, tr('action_export_list'), 'list.csv', tr('csv_filter'))
        if not target:
            return
        self.statusBar().showMessage(tr('export_running', path=target))
        if not self.results.advice_arriving(view):
            self._export_list_to(view, target)
            return
        # The clean-up analysis is about to change the removal advice this list shows: capture after it.
        outcome, changed = self.results.outcome, self.results.cleanup.summary_changed

        def resume() -> None:
            if self.results.advice_arriving(view):
                return
            changed.disconnect(resume)
            if self._closing:
                return
            if self.results.outcome is not outcome:
                QMessageBox.warning(self, tr('export_title'), tr('export_failed', reason=tr('list_changed')))
                return
            self._export_list_to(view, target)

        changed.connect(resume)

    def _export_list_to(self, view: QAbstractItemView, target: str) -> None:
        stream = ListStream()
        capture = ListCapture(view, self, stream=stream)
        self._captures.add(capture)
        capture.finished.connect(lambda: self._captures.discard(capture))
        capture.finished.connect(capture.deleteLater)
        worker = ExportWorker(lambda: export.export_table_csv(capture.header, stream.rows(), target), self)
        worker.done.connect(lambda count: self._export_done(target, count))
        worker.failed.connect(lambda reason: self._list_export_failed(capture, reason))
        worker.finished.connect(capture.cancel)
        worker.finished.connect(lambda: self._exports.discard(worker))
        worker.finished.connect(worker.deleteLater)
        self._exports.add(worker)
        worker.start()
        capture.start()

    def _list_export_failed(self, capture: ListCapture, reason: str) -> None:
        capture.cancel()
        if not self._closing:
            QMessageBox.warning(self, tr('export_title'), tr('export_failed', reason=reason))

    def print_current_view(self) -> None:
        """Offer the system print dialog for one page containing the visible results."""
        if self.results.outcome is None or self._worker is not None or self.operation_busy:
            return
        image = self.results.grab().toImage()
        printer = view_printer(image)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            print_view(image, printer)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, tr("action_print_view"), tr("print_failed", reason=str(error)))
            return
        self.statusBar().showMessage(tr("print_submitted"), STATUS_TIMEOUT_MS)

    def export_view_pdf(self) -> None:
        """Export captured results through Qt's PDF engine on an atomic-writing worker."""
        if self.results.outcome is None or self._worker is not None or self.operation_busy:
            return
        target, _ = QFileDialog.getSaveFileName(self, tr("action_export_view_pdf"), "view.pdf", tr("pdf_filter"))
        if not target:
            return
        image = self.results.grab().toImage()
        worker = ExportWorker(lambda: save_view_pdf(image, target), self)
        worker.done.connect(lambda _count: self.statusBar().showMessage(tr("view_pdf_exported", path=target)))
        worker.failed.connect(lambda reason: QMessageBox.warning(self, tr("export_title"),
                                                                 tr("export_failed", reason=reason)))
        worker.finished.connect(lambda: self._exports.discard(worker))
        worker.finished.connect(worker.deleteLater)
        self._exports.add(worker)
        worker.start()

    def export_chart(self, kind: str) -> None:
        """Capture the visible chart as PNG, or full bounded bars/rings as vector SVG."""
        if self.results.outcome is None or self._worker is not None or self.operation_busy:
            return
        charts = self.results.charts
        if kind == "svg" and charts.mode not in SVG_MODES:
            return
        target, _ = QFileDialog.getSaveFileName(self, tr("action_export_chart_" + kind),
                                                f"chart.{kind}", tr(kind + "_filter"))
        if not target:
            return
        try:
            graphic = capture_svg(charts) if kind == "svg" else charts.currentWidget().grab().toImage()
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, tr("export_title"), tr("export_failed", reason=str(error)))
            return
        worker = ExportWorker(lambda: save_graphic(target, graphic), self)
        worker.done.connect(lambda _count: self.statusBar().showMessage(tr("graphic_exported", path=target)))
        worker.failed.connect(lambda reason: QMessageBox.warning(self, tr("export_title"),
                                                                 tr("export_failed", reason=reason)))
        worker.finished.connect(lambda: self._exports.discard(worker))
        worker.finished.connect(worker.deleteLater)
        self._exports.add(worker)
        worker.start()

    def export_results(self, kind: str) -> None:
        """Save the results: ``"folders"`` or ``"largest"`` as CSV, ``"json"`` as JSON."""
        outcome = self.results.outcome
        if outcome is None:
            return
        is_json = kind == "json"
        name = outcome.result.root.name or tr("multi_roots")
        suggested = f"{_safe_name(name)}-{kind}.{'json' if is_json else 'csv'}"
        start = os.path.join(str(self.settings.value("export_dir", os.path.expanduser("~"))), suggested)
        target, _ = QFileDialog.getSaveFileName(self, tr("export_title"), start,
                                                tr("json_filter") if is_json else tr("csv_filter"))
        if not target:
            return
        root = outcome.result.root
        largest = self.results.largest_model.rows()
        writers: dict[str, Callable[[], int]] = {
            "folders": lambda: export.export_folders_csv(root, target),
            "largest": lambda: export.export_files_csv(largest, target),
            "json": lambda: _write_json(root, target),
        }
        worker = ExportWorker(writers[kind], self)
        worker.done.connect(lambda count: self._export_done(target, count))
        worker.failed.connect(lambda reason: QMessageBox.warning(self, tr("export_title"),
                                                                 tr("export_failed", reason=reason)))
        worker.finished.connect(lambda: self._exports.discard(worker))
        worker.finished.connect(worker.deleteLater)
        self._exports.add(worker)
        self.statusBar().showMessage(tr("export_running", path=target))
        worker.start()

    def _export_done(self, target: str, count: int) -> None:
        self.settings.setValue("export_dir", os.path.dirname(target))
        self.statusBar().showMessage(tr("export_done", count=count, path=target), STATUS_TIMEOUT_MS)


def _write_json(root: Node, target: str) -> int:
    """Write the folder tree as JSON; returns the number of folders written."""
    export.export_json(root, target)
    return root.dir_count + 1


def _safe_name(name: str) -> str:
    cleaned = "".join(character if character.isalnum() or character in "-_" else "_" for character in name)
    return cleaned.strip("_") or "scan"
