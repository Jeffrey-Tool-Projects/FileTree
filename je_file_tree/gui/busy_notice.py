"""Say why an action did nothing: a scan or another operation is running and it has to wait.

While a scan runs (or a move to the Recycle Bin, a deletion, an undo or a review in this or another
tab), the actions that would read or change the scanned entries cannot start. Pressing one used to do
nothing at all; now it stays enabled and, when used, says why it waits and what ends the wait. The
notice goes to the status bar and, as a tooltip, next to the pointer, where the user just clicked.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QMainWindow, QToolTip

from je_file_tree.gui.i18n import tr

NOTICE_MS = 8000  # as long as the window's other status messages


def action_name(text: str) -> str:
    """A menu text as it reads in a sentence: no mnemonic ampersands or trailing ellipsis."""
    name = text.replace("&&", "\0").replace("&", "").replace("\0", "&").strip()
    for ending in ("…", "..."):
        if name.endswith(ending):
            name = name[:-len(ending)].rstrip()
    return name


def busy_text(action: str, *, scanning: bool) -> str:
    """The notice for ``action``, which waits for the running scan or for another operation."""
    return tr("busy_scanning" if scanning else "busy_operation", action=action_name(action))


def show_busy(window: QMainWindow, action: str, *, scanning: bool) -> str:
    """Show why ``action`` did not start, in the status bar and next to the pointer; returns the text."""
    text = busy_text(action, scanning=scanning)
    window.statusBar().showMessage(text, NOTICE_MS)
    pointer = QCursor.pos()
    inside = window.rect().contains(window.mapFromGlobal(pointer))
    bar = window.statusBar()
    where = pointer if inside else bar.mapToGlobal(QPoint(0, 0))
    QToolTip.showText(where, text, window, window.rect(), NOTICE_MS)
    return text
