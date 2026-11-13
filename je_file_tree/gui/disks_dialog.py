"""Read-only physical disks: health, reported counters and partition layout, queried off the GUI thread."""

from __future__ import annotations

from collections.abc import Callable, Sequence
import sys
import threading

from PySide6.QtCore import QModelIndex, QRect, QThread, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPalette
from PySide6.QtWidgets import (QAbstractItemView, QDialogButtonBox, QHBoxLayout, QLabel, QMessageBox, QPushButton,
                               QTableView, QVBoxLayout, QWidget)

from je_file_tree.core.disks import (COUNTERS_REPORTED, DiskSurvey, Partition, PhysicalDisk, Segment,
                                     layout_segments, physical_disks)
from je_file_tree.core.formatting import format_count, format_size
from je_file_tree.gui.colours import blend, readable_ink
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.list_transfer import install_copy
from je_file_tree.gui.scan_worker import wait_for
from je_file_tree.gui.system_files import open_system_tool
from je_file_tree.gui.tables import Column, _TableModel
from je_file_tree.gui.worker_lifecycle import WorkerDialog, queue_worker, retire_worker

Provider = Callable[..., DiskSurvey | None]

# Fixed Windows tools (see system_files.open_system_tool): never a command chosen at run time.
TOOLS = (("disk_management", "disks_tool_management"), ("optimize", "disks_tool_optimize"),
         ("disks_volumes", "disks_tool_volumes"), ("storage", "disks_tool_storage"))
_HUES = ("#4e79a7", "#f28e2b", "#59a14f", "#b07aa1", "#76b7b2", "#edc948", "#e15759", "#9c755f")
_LABEL_WIDTH = 48
_MIN_SEGMENT = 8


def _size(value: int | None, unit: str) -> str:
    return tr("disks_unknown") if value is None else format_size(value, unit)


def _or_unknown(text: str) -> str:
    return text or tr("disks_unknown")


def _mounts(part: Partition) -> str:
    return ", ".join(part.mounts)


class DisksModel(_TableModel[PhysicalDisk]):
    """Device name, model, media, connection, partition table, size and health of each physical disk."""

    def build_columns(self) -> Sequence[Column[PhysicalDisk]]:
        """Translated texts are computed on demand, so a language change only needs a refresh."""
        return (Column("disks_col_disk", lambda row: row.identifier, lambda row: row.identifier),
                Column("disks_col_model", lambda row: _or_unknown(row.model), lambda row: row.model.casefold()),
                Column("disks_col_media", lambda row: tr(f"disks_media_{row.media}"), lambda row: row.media),
                Column("disks_col_bus", lambda row: _or_unknown(row.bus), lambda row: row.bus),
                Column("disks_col_style", lambda row: _or_unknown(row.style), lambda row: row.style),
                Column("disks_col_size", lambda row: _size(row.size, self.unit), lambda row: row.size or -1,
                       numeric=True),
                Column("disks_col_health", lambda row: tr(f"disks_state_{row.health}"), lambda row: row.health))


class PartitionsModel(_TableModel[Partition]):
    """Number, type, label, drive letters or mount points, file system, start and size of each partition."""

    def build_columns(self) -> Sequence[Column[Partition]]:
        """Unknown values say so instead of looking empty."""
        return (Column("disks_col_number", lambda row: "" if row.index is None else str(row.index),
                       lambda row: -1 if row.index is None else row.index, numeric=True),
                Column("disks_col_kind", lambda row: _or_unknown(row.kind), lambda row: row.kind),
                Column("disks_col_label", lambda row: row.label, lambda row: row.label.casefold()),
                Column("disks_col_mounts", _mounts, _mounts),
                Column("disks_col_fs", lambda row: _or_unknown(row.filesystem), lambda row: row.filesystem),
                Column("disks_col_offset", lambda row: _size(row.offset, self.unit), lambda row: row.offset or -1,
                       numeric=True),
                Column("disks_col_size", lambda row: _size(row.size, self.unit), lambda row: row.size or -1,
                       numeric=True))


class PartitionBar(QWidget):
    """Draw a disk's partitions in proportion to their size; clicking one selects it."""

    partition_clicked = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(34)
        self.disk: PhysicalDisk | None = None
        self.segments: tuple[Segment, ...] = ()
        self.selected: int | None = None

    def set_disk(self, disk: PhysicalDisk | None) -> None:
        """Show ``disk`` (or nothing) with no partition selected."""
        self.disk, self.selected = disk, None
        self.segments = () if disk is None else layout_segments(disk)
        self.update()

    def set_selected(self, position: int | None) -> None:
        """Highlight the partition at ``position`` in the disk's partition list."""
        self.selected = position
        self.update()

    def segment_rects(self) -> list[QRect]:
        """Pixel rectangles of the segments, side by side; every partition stays wide enough to see and click.

        A 100 MB system partition on a 256 GB disk is 0.04 % of it: drawn to scale it would vanish, so tiny
        partitions get a minimum width and the larger segments give up the difference in proportion.
        """
        area = self.rect().adjusted(1, 1, -1, -1)
        wanted = [segment.width * area.width() for segment in self.segments]
        small = [segment.partition is not None and width < _MIN_SEGMENT
                 for segment, width in zip(self.segments, wanted, strict=True)]
        flexible = sum(width for width, tiny in zip(wanted, small, strict=True) if not tiny)
        scale = max(0.0, area.width() - _MIN_SEGMENT * sum(small)) / flexible if flexible > 0 else 0.0
        rects, left = [], float(area.left())
        for width, tiny in zip(wanted, small, strict=True):
            size = _MIN_SEGMENT if tiny else width * scale
            rects.append(QRect(round(left), area.top(), max(1, round(left + size) - round(left)), area.height()))
            left += size
        return rects

    def _label(self, segment: Segment) -> str:
        if segment.partition is None or self.disk is None:
            return tr("disks_free_space")
        part = self.disk.partitions[segment.partition]
        return part.mounts[0] if part.mounts else part.kind or ("" if part.index is None else f"#{part.index}")

    def paintEvent(self, event: QPaintEvent) -> None:
        """Qt: free space in the window colour, partitions in distinct hues, the selection highlighted."""
        painter = QPainter(self)
        palette = self.palette()
        base = palette.color(QPalette.ColorRole.Base)
        painter.fillRect(self.rect(), base)
        for segment, box in zip(self.segments, self.segment_rects(), strict=True):
            if segment.partition is None:
                fill = palette.color(QPalette.ColorRole.Window)
            elif segment.partition == self.selected:
                fill = palette.color(QPalette.ColorRole.Highlight)
            else:
                fill = blend(QColor(_HUES[segment.partition % len(_HUES)]), base, 0.75)
            painter.fillRect(box, fill)
            painter.setPen(palette.color(QPalette.ColorRole.Mid))
            painter.drawRect(box.adjusted(0, 0, -1, -1))
            if box.width() >= _LABEL_WIDTH:
                painter.setPen(readable_ink(fill))
                text = painter.fontMetrics().elidedText(self._label(segment), Qt.TextElideMode.ElideRight,
                                                        box.width() - 6)
                painter.drawText(box.adjusted(3, 0, -3, 0), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Qt: report the clicked partition (free space is ignored)."""
        point = event.position().toPoint()
        for segment, box in zip(self.segments, self.segment_rects(), strict=True):
            if segment.partition is not None and box.contains(point):
                self.partition_clicked.emit(segment.partition)
                return
        super().mousePressEvent(event)


class DisksWorker(QThread):
    """Run the read-only disk query outside the GUI thread; Refresh/close suppress late results."""

    ready = Signal(object)

    def __init__(self, provider: Provider, parent: QWidget) -> None:
        super().__init__(parent)
        self.cancel = threading.Event()
        self._provider = provider

    def run(self) -> None:
        """Emit the survey unless it was cancelled."""
        survey = self._provider(cancel=self.cancel)
        if survey is not None and not self.cancel.is_set():
            self.ready.emit(survey)


def _table(model: _TableModel, widths: Sequence[int]) -> QTableView:
    view = QTableView()
    view.setModel(model)
    view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    view.verticalHeader().hide()
    for column, width in enumerate(widths):
        view.setColumnWidth(column, width)
    install_copy(view)
    return view


class DisksDialog(WorkerDialog):
    """List physical disks with their health and partitions; FileTree changes nothing on any disk here."""

    def __init__(self, unit: str, parent: QWidget | None = None, provider: Provider = physical_disks) -> None:
        super().__init__(parent)
        self.resize(1100, 640)
        self._closed = False
        self._provider = provider
        self.survey: DiskSurvey | None = None
        self.disks = DisksModel(self)
        self.partitions = PartitionsModel(self)
        self.disks.unit = self.partitions.unit = unit
        self.disk_view = _table(self.disks, (150, 260, 120, 100, 110, 100, 100))
        self.disk_view.selectionModel().currentRowChanged.connect(self._disk_changed)
        self.partition_view = _table(self.partitions, (40, 130, 130, 240, 90, 100, 100))
        self.partition_view.selectionModel().currentRowChanged.connect(
            lambda current, _previous: self.bar.set_selected(current.row() if current.isValid() else None))
        self.bar = PartitionBar()
        self.bar.partition_clicked.connect(self.partition_view.selectRow)
        self.hint, self.health, self.counters, self.note, self.status = (QLabel() for _ in range(5))
        for label in (self.hint, self.health, self.counters, self.note, self.status):
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.refresh_button = QPushButton()
        self.refresh_button.clicked.connect(lambda _checked=False: self.refresh())
        self.tool_buttons = {tool: QPushButton() for tool, _key in TOOLS}
        buttons = QHBoxLayout()
        buttons.addWidget(self.refresh_button)
        for tool, button in self.tool_buttons.items():
            if sys.platform != "win32":
                button.hide()  # the fixed tools exist only on Windows
            button.clicked.connect(lambda _checked=False, chosen=tool: self.open_tool(chosen))
            buttons.addWidget(button)
        buttons.addStretch(1)
        self.close_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.close_box.rejected.connect(self.reject)
        buttons.addWidget(self.close_box)
        layout = QVBoxLayout(self)
        for widget, stretch in ((self.hint, 0), (self.disk_view, 2), (self.health, 0), (self.counters, 0),
                                (self.note, 0), (self.bar, 0), (self.partition_view, 2), (self.status, 0)):
            layout.addWidget(widget, stretch)
        layout.addLayout(buttons)
        self.retranslate()
        self.refresh()

    def retranslate(self) -> None:
        """Re-read every text in the current language."""
        self.setWindowTitle(tr("disks_title"))
        self.hint.setText(tr("disks_hint"))
        self.bar.setAccessibleName(tr("disks_bar_name"))
        self.refresh_button.setText(tr("disks_refresh"))
        for tool, key in TOOLS:
            self.tool_buttons[tool].setText(tr(key))
        self.disks.refresh()
        self.partitions.refresh()
        self._show_status()
        self._show_details(self.selected_disk())
        self.bar.update()

    def selected_disk(self) -> PhysicalDisk | None:
        """The disk whose details are shown."""
        return self.disks.row_at(self.disk_view.currentIndex().row())

    def refresh(self) -> None:
        """Query the disks again; a running query is cancelled and its answer ignored."""
        if self._closed:
            return
        previous = getattr(self, "worker", None)
        if previous is not None:
            previous.cancel.set()
            retire_worker(previous, self)
        self.survey = None
        self._show_status()
        self.worker = DisksWorker(self._provider, self)
        worker = self.worker
        worker.ready.connect(lambda survey: self.worker is worker and self._show(survey))
        queue_worker(worker, lambda: not self._closed and self.worker is worker and not worker.cancel.is_set(), self)

    def _show(self, survey: DiskSurvey) -> None:
        if self._closed or self.worker.cancel.is_set():
            return
        self.survey = survey
        self.disks.set_rows(survey.disks)
        self._show_status()
        if survey.disks:
            self.disk_view.selectRow(0)
        else:
            self._show_details(None)

    def _show_status(self) -> None:
        survey = self.survey
        if survey is None:
            text, tip = tr("disks_reading"), ""
        elif survey.problem is not None:
            text, tip = tr(f"disks_problem_{survey.problem}"), survey.detail
        else:
            text = tr("disks_summary", count=format_count(len(survey.disks))) if survey.disks else tr("disks_none")
            tip = ""
        self.status.setText(text)
        self.status.setToolTip(tip)

    def _disk_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        self._show_details(self.disks.row_at(current.row()) if current.isValid() else None)

    def _show_details(self, disk: PhysicalDisk | None) -> None:
        if disk is None:
            self.partitions.set_rows([])
            self.bar.set_disk(None)
            self.health.setText(tr("disks_select"))
            self.counters.clear()
            self.note.clear()
            self.note.setVisible(False)
            return
        if self.bar.disk is not disk:
            self.partitions.set_rows(disk.partitions)
            self.bar.set_disk(disk)
        self.health.setText(tr("disks_health_line", state=tr(f"disks_state_{disk.health}"),
                               meaning=tr(f"disks_meaning_{disk.health}")))
        self.counters.setText(self._counters(disk))
        note = "" if disk.counters == COUNTERS_REPORTED else tr(f"disks_counters_{disk.counters}")
        if not disk.partitions:
            note = " ".join(part for part in (note, tr("disks_no_partitions")) if part)
        self.note.setText(note)
        self.note.setVisible(bool(note))

    @staticmethod
    def _counters(disk: PhysicalDisk) -> str:
        missing = tr("disks_not_reported")
        return tr("disks_counters",
                  temperature=missing if disk.temperature is None else tr("disks_temperature_value",
                                                                          degrees=disk.temperature),
                  wear=missing if disk.wear is None else tr("disks_wear_value", percent=disk.wear),
                  hours=missing if disk.power_on_hours is None else tr("disks_hours_value",
                                                                       hours=format_count(disk.power_on_hours)))

    def open_tool(self, tool: str) -> None:
        """Open one of the fixed Windows tools; FileTree itself changes nothing on the disks."""
        if not open_system_tool(tool, ""):
            QMessageBox.warning(self, self.windowTitle(), tr("system_tool_failed"))

    def shutdown(self, *, wait: bool = True) -> None:
        """Cancel the query and, when asked, join it before the dialog goes away."""
        self._closed = True
        self.worker.cancel.set()
        if wait:
            wait_for(self.worker)

    def done(self, result: int) -> None:
        """Qt: ignore queued replies and join before closing."""
        if self.defer_done(result):
            return
        self.shutdown()
        super().done(result)
