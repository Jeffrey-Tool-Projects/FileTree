"""Chart tooltips, shown through Qt's own tooltip event once the mouse rests (U-20261119-04).

Measured 2026-11-19 on the development machine: one ``QToolTip.showText`` costs 35-45 ms, whatever
the text, because it moves and repaints the native tooltip window. The charts used to call it on
every hover change, so moving across the bar chart stalled about 90 ms per row. Qt sends
``QEvent.ToolTip`` only after the mouse rests (briefly once a tooltip has just been shown), so each
chart answers that event instead and the hover highlight alone follows the mouse.
"""

from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QHelpEvent
from PySide6.QtWidgets import QToolTip, QWidget


def show_chart_tip(widget: QWidget, event: QHelpEvent, text: str | None, area: QRect | None = None) -> bool:
    """Answer a tooltip event: show ``text`` (hidden once the mouse leaves ``area``), or hide it for None."""
    if text is None:
        QToolTip.hideText()
        event.ignore()
    else:
        QToolTip.showText(event.globalPos(), text, widget, area if area is not None else QRect())
    return True
