"""The optional preview under Details: a picture, the beginning of a text or an archive's members."""

from __future__ import annotations

import threading
from dataclasses import replace

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSettings, QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QImage, QImageReader, QPixmap
from PySide6.QtWidgets import QCheckBox, QLabel, QPlainTextEdit, QVBoxLayout, QWidget

from je_file_tree.archive_formats import rar_members, seven_zip_members
from je_file_tree.core.archives import ArchiveCancelledError, zip_members
from je_file_tree.core.formatting import AUTO_UNIT, format_size
from je_file_tree.core.node import Node
from je_file_tree.core.preview import ARCHIVE, BINARY, IMAGE, Preview, PreviewError, read_preview
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.scan_worker import wait_for

PREVIEW_KEY = "details_preview"
_READERS = {".zip": zip_members, ".7z": seven_zip_members, ".rar": rar_members}
_PICTURE = QSize(480, 300)
_ALLOCATION_MIB = 128
_DELAY_MS = 250


def decode_picture(data: bytes) -> QImage:
    """Decode a picture no larger than the pane needs, within a memory limit; raises when it cannot be."""
    buffer = QBuffer()
    buffer.setData(QByteArray(data))
    buffer.open(QIODevice.OpenModeFlag.ReadOnly)
    reader = QImageReader(buffer)
    reader.setAllocationLimit(_ALLOCATION_MIB)
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid() and (size.width() > _PICTURE.width() or size.height() > _PICTURE.height()):
        reader.setScaledSize(size.scaled(_PICTURE, Qt.AspectRatioMode.KeepAspectRatio))
    image = reader.read()
    if image.isNull():
        raise PreviewError(reader.errorString())
    return image


class PreviewWorker(QThread):
    """Read and decode one preview off the GUI thread."""

    ready = Signal(object, object)
    failed = Signal()

    def __init__(self, node: Node, parent: QWidget) -> None:
        super().__init__(parent)
        self.captured = replace(node, name=node.path, parent=None)
        self.cancel = threading.Event()

    def run(self) -> None:
        """Emit the preview and its decoded picture, or that there is none."""
        try:
            preview = read_preview(self.captured, _READERS, self.cancel)
            image = decode_picture(preview.data) if preview.kind == IMAGE else None
        except ArchiveCancelledError:
            return
        except (OSError, ValueError, ImportError):
            if not self.cancel.is_set():
                self.failed.emit()
            return
        if not self.cancel.is_set():
            self.ready.emit(preview, image)


class PreviewPane(QWidget):
    """Reads nothing until it is turned on; then one selected file at a time, after a short pause."""

    def __init__(self, settings: QSettings | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.unit = AUTO_UNIT
        self._node: Node | None = None
        self._active = False
        self._preview: Preview | None = None
        self._status = "preview_none"
        self._current: PreviewWorker | None = None
        self._running: set[PreviewWorker] = set()
        self.enabled = QCheckBox()
        self.enabled.setChecked(settings is not None and settings.value(PREVIEW_KEY, False, type=bool))
        self.enabled.toggled.connect(self._toggled)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setProperty("role", "caption")
        self.picture = QLabel()
        self.picture.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.text.setTabChangesFocus(True)
        self.text.setMinimumHeight(140)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        for widget in (self.enabled, self.status, self.picture, self.text):
            layout.addWidget(widget)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(_DELAY_MS)
        self._timer.timeout.connect(self._start)
        self.retranslate()
        self._show()

    def set_node(self, node: Node | None, *, active: bool) -> None:
        """Follow the selection; ``active`` is whether the pane is on screen with a finished scan."""
        self.stop()
        self._node, self._active, self._preview = node, active, None
        self._status = "preview_none"
        self.picture.clear()
        self._show()
        if active and self.enabled.isChecked() and self._previewable():
            self._status = "preview_reading"
            self._show()
            self._timer.start()

    def _previewable(self) -> bool:
        node = self._node
        return (node is not None and not node.is_dir and not node.is_link and node.error is None
                and node.snapshot is not None and node.path is not None)

    def _toggled(self, enabled: bool) -> None:
        if self._settings is not None:
            self._settings.setValue(PREVIEW_KEY, enabled)
        self.set_node(self._node, active=self._active)

    def _start(self) -> None:
        if self._node is None or not self._previewable():
            return
        worker = PreviewWorker(self._node, self)
        worker.ready.connect(lambda preview, image: self._ready(worker, preview, image))
        worker.failed.connect(lambda: self._failed(worker))
        worker.finished.connect(lambda: self._running.discard(worker))
        worker.finished.connect(worker.deleteLater)
        self._current = worker
        self._running.add(worker)
        worker.start()

    def _ready(self, worker: PreviewWorker, preview: Preview, image: QImage | None) -> None:
        if worker is not self._current:
            return
        self._current, self._preview = None, preview
        if image is not None:
            self.picture.setPixmap(QPixmap.fromImage(image))
        self._status = ("preview_binary" if preview.kind == BINARY else
                        "preview_more" if preview.more else "preview_whole")
        self._show()

    def _failed(self, worker: PreviewWorker) -> None:
        if worker is self._current:
            self._current = None
            self._status = "preview_failed"
            self._show()

    def _show(self) -> None:
        on, preview = self.enabled.isChecked(), self._preview
        self.status.setVisible(on)
        self.status.setText(tr(self._status))
        self.picture.setVisible(on and preview is not None and preview.kind == IMAGE)
        body = ""
        if preview is not None and preview.kind == ARCHIVE:
            body = "\n".join(f"{format_size(size, self.unit):>12}  {path}" for path, size in preview.lines)
        elif preview is not None:
            body = preview.text
        self.text.setVisible(on and bool(body))
        self.text.setPlainText(body)

    def retranslate(self) -> None:
        """Re-read the texts, keeping what is shown."""
        self.enabled.setText(tr("preview_show"))
        self.enabled.setToolTip(tr("preview_show_tip"))
        self.text.setAccessibleName(tr("preview_show"))
        self.picture.setAccessibleName(tr("preview_show"))
        self._show()

    def stop(self, *, wait: bool = False) -> None:
        """Drop the pending or running read; ``wait`` joins its thread."""
        self._timer.stop()
        self._current = None
        for worker in list(self._running):
            worker.cancel.set()
            if wait:
                wait_for(worker)
