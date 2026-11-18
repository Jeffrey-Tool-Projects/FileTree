"""A running scan's live refreshes are spaced by what each one cost the window (U-20261118-01)."""

import time

from PySide6.QtCore import QEventLoop, QObject, QTimer

from je_file_tree.gui.live_refresh import FASTEST_MS, SLOWEST_MS, SPACING, LiveRefresh, interval_for


def _run(qapp, milliseconds):
    """Run the event loop for ``milliseconds``, letting it wait (and announce that) between events."""
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def test_the_wait_is_a_multiple_of_the_busy_time_within_bounds():
    assert interval_for(0) == FASTEST_MS
    assert interval_for(FASTEST_MS / SPACING - 1) == FASTEST_MS
    assert interval_for(300) == 300 * SPACING
    assert interval_for(10_000) == SLOWEST_MS


def test_a_costly_refresh_spaces_the_next_one_and_a_cheap_one_restores_the_pace(qapp):
    owner = QObject()
    costs = [0.3, 0.0]
    calls = []

    def refresh():
        cost = costs[min(len(calls), len(costs) - 1)]
        calls.append(time.perf_counter())
        time.sleep(cost)

    live = LiveRefresh(refresh, owner)
    live.start()
    assert live.interval == FASTEST_MS
    _run(qapp, FASTEST_MS + 600)  # the first, costly refresh ran and the loop went idle after it
    assert len(calls) == 1
    assert 300 * SPACING <= live.interval <= SLOWEST_MS
    spaced = live.interval
    _run(qapp, spaced + 800)  # the cheap second refresh brings the period back to the fastest
    assert len(calls) >= 2
    assert calls[1] - calls[0] >= spaced / 1000 * 0.9
    assert live.interval == FASTEST_MS
    live.stop()
    assert not live.isActive()


def test_a_new_start_begins_at_the_fastest_pace_and_stop_drops_a_late_measurement(qapp):
    owner = QObject()
    live = LiveRefresh(lambda: time.sleep(0.3), owner)
    live.start()
    _run(qapp, FASTEST_MS + 600)
    assert live.interval > FASTEST_MS
    live.start()
    assert live.interval == FASTEST_MS
    live._tick()
    live.stop()  # the scan ended before the window went idle: the measurement changes nothing
    _run(qapp, 50)
    assert live.interval == FASTEST_MS and not live.isActive()
