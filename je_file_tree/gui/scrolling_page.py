"""A page that fills its window while it fits and scrolls when the window is smaller than its minimum."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QScrollArea, QWidget


class ScrollingPage(QScrollArea):
    """Show ``page`` at the size of the window, but never below its minimum size.

    Without this a page's minimum height is its window's: the results page needed a window of 786 pixels
    at the system's text size and 1129 at 200 %, against 672 available on a 1920 x 1080 laptop at 150 %
    display scaling (2026-11-25), so the lower part of the window was off the screen.

    ``setWidgetResizable`` is not used: for a page with wrapping labels it asks for the preferred height,
    not the minimum, and scrolled a 1200 x 800 window the page fits in.
    """

    def __init__(self, page: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setWidget(page)
        page.setAutoFillBackground(False)  # setWidget turns it on; the window's own background shows through
        self.viewport().setAutoFillBackground(False)
        page.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802 - Qt's name
        """Qt: the page's minimum changes with its content, its active view and the text size."""
        if watched is self.widget() and event.type() == QEvent.Type.LayoutRequest:
            self._fit()
        return super().eventFilter(watched, event)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 - Qt's name
        """Qt: fill the new size, also when a scroll bar has taken its share of it."""
        super().resizeEvent(event)
        self._fit()

    def _fit(self) -> None:
        page = self.widget()
        page.resize(self.viewport().size().expandedTo(page.minimumSizeHint().expandedTo(page.minimumSize())))
