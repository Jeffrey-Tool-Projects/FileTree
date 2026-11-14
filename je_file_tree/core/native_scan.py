"""The optional native folder reader of the Windows scanner, used only when it is proven equal.

``je_file_tree._native`` lists a folder and reads every entry's metadata without the interpreter
lock. Measured 2026-11-14 on 80,000 small files (warm cache, 8 logical processors): the Python
scanner took 3.3 s with any number of threads, because every entry costs an ``os.lstat`` call and
Python work under the lock. The figures with the native reader are next to ``scanner._read_native``.

Recorded snapshots are compared with a fresh ``os.lstat`` before every later operation, so the
native bytes must equal ``pack_snapshot(os.lstat(path))`` exactly. ``reader`` therefore checks the
module against ``os.lstat`` on this interpreter and this system before handing it out, once per
process, and answers None when the module is absent, switched off or disagrees. The scanner then
reads folders in Python, with the same results. That check reads this interpreter's own files, so
``agrees_on`` repeats it for the folder a scan starts from: another volume or file system may identify
its files differently (Python 3.12 on a volume without 128-bit file numbers, for example).

Python 3.11 reports a 32-bit volume number and a 64-bit file number where later versions report 64 and
128 bits (found 2026-11-14: the reader was refused on 3.11.9), so the module has a query for each.
"""

from __future__ import annotations

import os
import sys
import threading
from collections.abc import Callable

from je_file_tree.core.snapshot import pack_snapshot

Row = tuple[str, int, int, float, bytes | None, int]
"""name, kind, size, modified, snapshot, attributes; see the kinds below."""
Reader = Callable[[str, bool], list[Row]]

KIND_FILE, KIND_FOLDER, KIND_ASK_PYTHON = 0, 1, 2
DISABLE_VARIABLE = "FILE_TREE_NATIVE_SCAN"  # set to 0 to read folders in Python
_FORMATS = 2  # a snapshot without and one with file times
_lock = threading.Lock()
_checked = False
_reader: Reader | None = None
_chosen: tuple[object, int, bool] | None = None  # the module, its query and which time is st_ctime


def reader() -> Reader | None:
    """``read(path, file_times)`` listing one folder natively, or None to read it in Python."""
    global _checked, _reader  # noqa: PLW0603 - one calibration per process
    if not _checked:
        with _lock:
            if not _checked:
                _reader = _calibrated()
                _checked = True
    return _reader


def agrees_on(path: str) -> bool:
    """Whether the calibrated reader also equals ``os.lstat`` for ``path``, the folder a scan starts from.

    False (read in Python) when there is no calibrated reader or the folder cannot be compared.
    """
    chosen = _chosen if reader() is not None else None
    return chosen is not None and _matched(chosen[0], path, chosen[1], chosen[2]) == _FORMATS


def reset() -> None:
    """Forget the calibration (tests switch the reader on and off)."""
    global _checked, _reader, _chosen  # noqa: PLW0603
    with _lock:
        _checked, _reader, _chosen = False, None, None


def _calibrated() -> Reader | None:
    global _chosen  # noqa: PLW0603 - set with the reader, under the lock
    if sys.platform != "win32" or os.environ.get(DISABLE_VARIABLE, "1") == "0":
        return None
    try:
        from je_file_tree import _native  # noqa: PLC0415 - optional: absent without a compiler or on other systems
    except ImportError:
        return None
    queries = [_native.QUERY_BY_HANDLE, _native.QUERY_BY_HANDLE_SHORT]
    if _native.by_name_available():
        queries.insert(0, _native.QUERY_BY_NAME)  # the fastest: no handle per entry
    for query in queries:
        for change_time in (False, True):  # which Windows time this interpreter reports as st_ctime
            if _agrees(_native, query, change_time):
                def read(path: str, file_times: bool, *, _query: int = query,
                         _change: bool = change_time) -> list[Row]:
                    return _native.read_folder(path, file_times, _change, _query)
                _chosen = (_native, query, change_time)
                return read
    return None


def _agrees(native: object, query: int, change_time: bool) -> bool:
    """Whether the native snapshots of known entries equal ``os.lstat``'s, with and without file times."""
    # A compiled program has no source files: its ``__file__`` names a place that does not exist
    # (found 2026-11-14 in a Nuitka build, where the reader was refused for that reason alone).
    samples = [path for path in (sys.executable, os.path.dirname(sys.executable), os.path.abspath(__file__),
                                 os.path.dirname(os.path.abspath(__file__))) if path and os.path.lexists(path)]
    matched = 0
    for path in samples:
        found = _matched(native, path, query, change_time)
        if found is None:
            return False
        matched += found
    return matched >= _FORMATS  # at least one entry was really compared, in both formats


def _matched(native: object, path: str, query: int, change_time: bool) -> int | None:
    """How many snapshot formats of ``path`` were compared and equal; None when one differs or fails."""
    matched = 0
    for file_times in (False, True):
        try:
            expected = pack_snapshot(os.lstat(path), file_times=file_times)
            found = native.snapshot(path, file_times, change_time, query)  # type: ignore[attr-defined]
            if found is None:
                continue  # a link or special entry: Python answers for those anyway
            confirmed = pack_snapshot(os.lstat(path), file_times=file_times)
        except (OSError, ValueError):
            return None
        if found not in (expected, confirmed):  # two reads rule out a change in between
            return None
        matched += 1
    return matched
