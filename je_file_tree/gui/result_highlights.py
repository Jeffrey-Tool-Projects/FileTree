"""Bounded result guidance using captured worker statistics, without filesystem queries."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QSizePolicy, QToolButton, QVBoxLayout, QWidget

from je_file_tree.core.advice import Adviser
from je_file_tree.core.coverage import Coverage
from je_file_tree.core.formatting import AUTO_UNIT, format_count, format_size
from je_file_tree.core.node import Node
from je_file_tree.gui import advice_text
from je_file_tree.gui.i18n import tr

_SHOWN = 3  # folders and files named, each on its own row


class ResultHighlights(QWidget):
    """Collapsible next steps; retained node references never grant source-operation authority."""

    folder_requested = Signal(object)
    file_requested = Signal(object)
    cleanup_requested = Signal()
    problems_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.unit = AUTO_UNIT
        self._folders: tuple[Node, ...] | None = None
        self._coverage: Coverage | None = None
        self._state = "empty"
        self._cleanup: tuple[int, int] | None = None
        self._files: tuple[Node, ...] = ()
        self._adviser: Adviser | None = None
        self.toggle = QToolButton()
        self.toggle.setCheckable(True)
        self.toggle.setChecked(True)
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.body = QWidget()
        self.message = QLabel()
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        self.message.setWordWrap(True)
        self.folders_label, self.files_label = QLabel(), QLabel()
        self.folders = [QPushButton() for _ in range(_SHOWN)]
        self.files = [QPushButton() for _ in range(_SHOWN)]
        for index, (folder, file) in enumerate(zip(self.folders, self.files, strict=True)):
            folder.clicked.connect(lambda _checked=False, row=index: self._choose(row))
            file.clicked.connect(lambda _checked=False, row=index: self._choose_file(row))
            for button in (folder, file):
                button.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.cleanup = QPushButton()
        self.cleanup.clicked.connect(self.cleanup_requested)
        self.problems = QPushButton()
        self.problems.clicked.connect(self.problems_requested)
        self.problems.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        grid = QGridLayout(self.body)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.addWidget(self.message, 0, 0, 1, _SHOWN + 1)
        for row, (caption, buttons) in enumerate(((self.folders_label, self.folders),
                                                  (self.files_label, self.files)), start=1):
            caption.setProperty("role", "caption")
            grid.addWidget(caption, row, 0)
            for index, button in enumerate(buttons, start=1):
                grid.addWidget(button, row, index)
        actions = QGridLayout()
        actions.addWidget(self.cleanup, 0, 0)
        actions.addWidget(self.problems, 0, 1)
        actions.setColumnStretch(0, 1)
        actions.setColumnStretch(1, 2)
        grid.addLayout(actions, 3, 0, 1, _SHOWN + 1)  # under the message, folder and file rows
        for column in range(1, _SHOWN + 1):
            grid.setColumnStretch(column, 1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.toggle)
        layout.addWidget(self.body)
        self.toggle.toggled.connect(self._expand)
        self._expand(True)

    def show_scan(self, folders: tuple[Node, ...] | None, state: str, coverage: Coverage | None) -> None:
        """Render at most three direct folders and already captured coverage counters."""
        self._folders, self._state, self._coverage = folders, state, coverage
        self.retranslate()

    def show_files(self, files: tuple[Node, ...], adviser: Adviser | None) -> None:
        """Name at most three captured largest files, each with its removal advice."""
        self._files, self._adviser = files[:_SHOWN], adviser
        self.retranslate()

    def show_cleanup(self, summary: tuple[int, int] | None) -> None:
        """None means pending; an empty completed result is explicitly distinct."""
        self._cleanup = summary
        self.retranslate()

    def _expand(self, expanded: bool) -> None:
        self.body.setVisible(expanded)
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)

    def _choose(self, row: int) -> None:
        if self._folders is not None and row < len(self._folders):
            self.folder_requested.emit(self._folders[row])

    def _choose_file(self, row: int) -> None:
        if row < len(self._files):
            self.file_requested.emit(self._files[row])

    def retranslate(self) -> None:
        """Update text without changing expansion, tree selection or list position."""
        self.toggle.setText(tr("highlights_title"))
        self.toggle.setAccessibleDescription(tr("highlights_title"))
        key = "highlights_waiting" if self._folders is None else (
            "highlights_partial" if self._state == "partial" else "highlights_folders")
        self.message.setText(tr(key))
        self.message.setVisible(key != "highlights_folders")  # the row captions say it once results are complete
        self.folders_label.setText(tr("highlights_folders_label"))
        self.folders_label.setToolTip(tr("highlights_folders"))
        self.files_label.setText(tr("highlights_files_label"))
        self.files_label.setToolTip(tr("highlights_files"))
        self.folders_label.setVisible(bool(self._folders))
        self.files_label.setVisible(bool(self._files))
        for index, button in enumerate(self.folders):
            node = self._folders[index] if self._folders and index < len(self._folders) else None
            button.setVisible(node is not None)
            if node is not None:
                text = tr("highlights_folder", name=node.name, size=format_size(node.size, self.unit))
                button.setText(text.replace("&", "&&"))
                button.setAccessibleName(text)
                button.setToolTip(node.path or node.name)
        for index, button in enumerate(self.files):
            self._show_file(button, self._files[index] if index < len(self._files) else None)
        self._show_actions()

    def _show_file(self, button: QPushButton, node: Node | None) -> None:
        button.setVisible(node is not None)
        if node is None:
            return
        text = tr("highlights_folder", name=node.name, size=format_size(node.size, self.unit))
        button.setText(text.replace("&", "&&"))
        advice = self._adviser.advice(node) if self._adviser is not None else None
        button.setIcon(advice_text.dot(advice.kind) if advice is not None else QIcon())
        answer = "" if advice is None else advice_text.summary(advice)
        button.setAccessibleName(text if advice is None else f"{text} — {advice_text.label(advice)}")
        button.setToolTip("\n".join(part for part in (node.path or node.name, answer) if part))

    def _show_actions(self) -> None:
        ready = self._state in ("complete", "partial")
        self.cleanup.setEnabled(ready)
        self.cleanup.setText(tr("highlights_cleanup_waiting") if self._cleanup is None else tr(
            "highlights_cleanup", count=format_count(self._cleanup[0]), size=format_size(self._cleanup[1], self.unit)))
        self.cleanup.setToolTip(tr("highlights_cleanup_hint"))
        coverage = self._coverage
        self.problems.setEnabled(ready)
        text = tr("highlights_coverage_unknown") if coverage is None else tr(
            "highlights_coverage", skipped=format_count(coverage.skipped_folders),
            denied=format_count(coverage.inaccessible_folders), pending=format_count(coverage.pending_folders))
        self.problems.setText(text)
        self.problems.setToolTip(text)
        self.problems.setAccessibleName(text)
