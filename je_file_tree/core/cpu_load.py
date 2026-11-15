"""How much of the processors other programs are using, for sizing a scan's reading threads.

A scan reads folders on several threads. While another program needs the processors, those threads
compete with it; ``WorkerGovernor`` watches the whole machine's processor time, takes this process's own
share out, and allows about as many reading threads as other programs leave processors free: never more
than the chosen number of threads and never fewer than one.

Measured 2026-11-15 on 696,000 files / 126,000 folders (NVMe, warm cache, 8 logical processors, native
reader): 2 threads 19.9 s, 4 threads 12.1 s, 8 threads 12.7 and 13.5 s (53-56 s of processor time
against 38 s). More threads than the default do not make this scan faster, so the governor only ever
lowers the count below the chosen number and brings it back; it never goes past it.

The same scan with four threads chosen: alone it stayed at 4 throughout (10.8 s). With five other
processes each keeping a processor busy it read with 3 threads (2 for a fifth of the readings) and took
23.4 s using 56.8 s of processor time, against 20.5 s and 61.9 s at a fixed four.

Windows reads ``GetSystemTimes`` and Linux ``/proc/stat``. Elsewhere there is no reading, and the count
stays at the chosen number.
"""

from __future__ import annotations

import ctypes
import os
import sys
import time
from collections.abc import Callable

SAMPLE_SECONDS = 0.5  # one comparison per half second: long enough for the 15.6 ms Windows clock tick
_FILETIME_SECONDS = 1e-7
_PROC_STAT = "/proc/stat"
_IDLE_COLUMNS = (3, 4)  # idle and iowait in the "cpu" line
_COUNTED_COLUMNS = 8  # user nice system idle iowait irq softirq steal; guest time is already in user

SystemTimes = Callable[[], "tuple[float, float] | None"]


def system_times() -> tuple[float, float] | None:
    """Processor seconds since boot as ``(busy, total)`` over every processor, or None when unknown."""
    try:
        if sys.platform == "win32":
            return _windows_times()
        if sys.platform.startswith("linux"):
            return _linux_times()
    except (OSError, ValueError):
        return None
    return None


def _windows_times() -> tuple[float, float]:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    pointer = ctypes.POINTER(ctypes.c_ulonglong)  # a FILETIME is one little-endian 64-bit count
    kernel.GetSystemTimes.argtypes = [pointer, pointer, pointer]
    kernel.GetSystemTimes.restype = ctypes.c_int
    idle, system, user = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
    if not kernel.GetSystemTimes(ctypes.byref(idle), ctypes.byref(system), ctypes.byref(user)):
        raise ctypes.WinError(ctypes.get_last_error())
    total = system.value + user.value  # the kernel figure includes idle time
    return (total - idle.value) * _FILETIME_SECONDS, total * _FILETIME_SECONDS


def _linux_times() -> tuple[float, float]:
    with open(_PROC_STAT, encoding="ascii") as stream:
        fields = stream.readline().split()
    if not fields or fields[0] != "cpu":
        raise ValueError("unexpected /proc/stat")
    ticks = [int(value) for value in fields[1:1 + _COUNTED_COLUMNS]]
    idle = sum(ticks[column] for column in _IDLE_COLUMNS if column < len(ticks))
    rate = os.sysconf("SC_CLK_TCK")
    return (sum(ticks) - idle) / rate, sum(ticks) / rate


class WorkerGovernor:
    """How many threads may read folders right now (``limit``), from 1 to ``ceiling``.

    ``update`` is cheap and may be called as often as wanted: it compares two readings at most once
    per ``SAMPLE_SECONDS`` and moves ``limit`` one step at a time, so a short burst elsewhere does not
    make the count jump about.
    """

    def __init__(self, ceiling: int, *, times: SystemTimes = system_times,
                 own: Callable[[], float] = time.process_time,
                 clock: Callable[[], float] = time.monotonic, processors: int | None = None) -> None:
        self.ceiling = max(1, ceiling)
        self.limit = self.ceiling
        self._times, self._own, self._clock = times, own, clock
        self._processors = processors or os.cpu_count() or 1
        self._last = self._read()
        self._due = clock() + SAMPLE_SECONDS

    def _read(self) -> tuple[float, float, float] | None:
        reading = self._times()
        return None if reading is None else (reading[0], reading[1], self._own())

    def update(self) -> int:
        """The number of threads allowed now."""
        now = self._clock()
        if now < self._due:
            return self.limit
        self._due = now + SAMPLE_SECONDS
        last, current = self._last, self._read()
        self._last = current
        if last is None or current is None:
            self.limit = self.ceiling  # no reading: the chosen number, as without a governor
            return self.limit
        total = current[1] - last[1]
        if total <= 0:
            return self.limit
        others = (current[0] - last[0] - (current[2] - last[2])) / total
        free = self._processors * (1 - min(max(others, 0.0), 1.0))
        target = min(self.ceiling, max(1, int(free + 0.5)))
        self.limit += (target > self.limit) - (target < self.limit)
        return self.limit
