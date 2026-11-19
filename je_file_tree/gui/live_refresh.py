"""Space a running scan's live refreshes by what each one cost the window.

A live refresh shows what the scan added: the folder tree relays out every shown row, the treemap
redraws. Its cost grows with the rows on screen: with 100,000 shown folders one refresh kept the window
busy about 0.7 s, against a fixed 700 ms period, so the window was never free between two refreshes
(U-20261118-01). Each refresh is therefore timed until the window's event loop is about to wait again,
which includes the layout and painting Qt defers to the following event pass, and the next one waits
``SPACING`` times that long, between ``FASTEST_MS`` and ``SLOWEST_MS``.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from PySide6.QtCore import QAbstractEventDispatcher, QObject, QTimer

FASTEST_MS = 700  # the period while refreshes are cheap
SLOWEST_MS = 5000  # the scan still shows progress this often, however many rows are shown
SPACING = 4  # wait four times a refresh's busy time: refreshes take at most a fifth of the window's time


def interval_for(busy_ms: float) -> int:
    """The wait before the next refresh after one that kept the window busy ``busy_ms``."""
    return round(min(SLOWEST_MS, max(FASTEST_MS, busy_ms * SPACING)))


class LiveRefresh(QObject):
    """A repeating timer for ``refresh`` whose period follows the measured cost of each call."""

    def __init__(self, refresh: Callable[[], None], parent: QObject) -> None:
        super().__init__(parent)
        self._refresh = refresh
        self._timer = QTimer(self)
        self._timer.setInterval(FASTEST_MS)
        self._timer.timeout.connect(self._tick)
        self._started: float | None = None
        self._dispatcher: QAbstractEventDispatcher | None = None

    @property
    def interval(self) -> int:
        """The current period in milliseconds."""
        return self._timer.interval()

    def isActive(self) -> bool:  # noqa: N802 - mirrors QTimer
        """Whether refreshes are running."""
        return self._timer.isActive()

    def start(self) -> None:
        """Start refreshing at the fastest period (a new scan starts with an empty tree)."""
        self._timer.start(FASTEST_MS)

    def stop(self) -> None:
        """Stop refreshing; a measurement still pending is dropped when it arrives."""
        self._timer.stop()

    def _tick(self) -> None:
        self._started = time.perf_counter()
        self._refresh()
        dispatcher = QAbstractEventDispatcher.instance()
        if dispatcher is not None and self._dispatcher is None:
            self._dispatcher = dispatcher
            dispatcher.aboutToBlock.connect(self._settled)

    def _settled(self) -> None:
        """The event loop is about to wait: the refresh and the work it queued are done."""
        dispatcher, self._dispatcher = self._dispatcher, None
        if dispatcher is not None:
            dispatcher.aboutToBlock.disconnect(self._settled)
        started, self._started = self._started, None
        if started is None or not self._timer.isActive():
            return
        interval = interval_for((time.perf_counter() - started) * 1000)
        if interval != self._timer.interval():
            self._timer.setInterval(interval)
