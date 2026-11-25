"""The "How to use FileTree" window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from je_file_tree.gui.i18n import tr
from je_file_tree.gui.text_scale import scaled_font
from je_file_tree.gui.text_size import TextSizeMenu, text_size_controller
from je_file_tree.gui.window_fit import fit_window

_READING_SCALE = 1.3  # continuous text is read at a larger size than labels and lists
_READING_STYLE = "p, li { line-height: 145%; margin-bottom: 6px; } h2 { margin-top: 18px; }"


class HelpDialog(QDialog):
    """Shows the help text of the current language at a size for reading.

    With ``text_sizes`` (the View → Text size menu) its commands and shortcuts work in this window too,
    so text that is still too small can be changed where it is noticed.
    """

    def __init__(self, parent: QWidget | None = None, text_sizes: TextSizeMenu | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("help_title"))
        fit_window(self, 820, 680)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.document().setDocumentMargin(14)
        browser.document().setDefaultStyleSheet(_READING_STYLE)
        self.browser = browser
        self._fit_text()
        browser.setHtml(tr("help_html"))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        row = QHBoxLayout()
        if text_sizes is not None:
            for action in (text_sizes.smaller, text_sizes.larger, text_sizes.reset):
                self._add_command(row, action)
        row.addWidget(buttons, 1)
        layout = QVBoxLayout(self)
        layout.addWidget(browser)
        layout.addLayout(row)
        text_size_controller().changed.connect(self._fit_text)

    def _add_command(self, row: QHBoxLayout, action: QAction) -> None:
        self.addAction(action)  # its shortcut works here as well as in the menu
        button = QToolButton()
        button.setDefaultAction(action)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        row.addWidget(button)

    def _fit_text(self, _percent: int = 0) -> None:
        self.browser.setFont(scaled_font(QApplication.font(), _READING_SCALE))
