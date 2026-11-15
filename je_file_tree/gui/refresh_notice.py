"""The line above the results after an operation changed files: the scan is older than the disk now.

FileTree scans when it is asked to. After a move to the Recycle Bin, a copy, a rename or any other
operation that changed files, the folders concerned are remembered and offered here; they are read
again when the button is pressed, never by themselves (*Follow changes* is the opt-in for that).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from je_file_tree.core.formatting import format_count
from je_file_tree.gui.i18n import tr


class RefreshNotice(QFrame):
    """How many scanned folders changed since they were read, with the button that reads them again."""

    requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pending = 0
        self._label = QLabel()
        self._label.setTextFormat(Qt.TextFormat.PlainText)
        self._label.setWordWrap(True)
        self.button = QPushButton()
        self.button.clicked.connect(self.requested)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)
        row.addWidget(self._label, 1)
        row.addWidget(self.button)
        self.hide()
        self.retranslate()

    @property
    def pending(self) -> int:
        """The number of changed folders on offer (0 while the line is hidden)."""
        return self._pending

    def show_pending(self, pending: int, *, enabled: bool) -> None:
        """Offer ``pending`` changed folders, or hide the line when there are none."""
        self._pending = pending
        self.button.setEnabled(enabled)
        self.retranslate()
        self.setVisible(pending > 0)

    def retranslate(self) -> None:
        """Re-read every translated text."""
        self._label.setText(tr("refresh_notice", count=format_count(self._pending)))
        self.button.setText(tr("refresh_now"))
        self.button.setToolTip(tr("refresh_now_tip"))
