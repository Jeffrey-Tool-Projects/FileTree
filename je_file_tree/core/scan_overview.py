"""Put saved scans of several computers side by side, folder by folder; only numbers and text, never entries.

A saved scan (*Export → Folder tree (JSON)*) holds folder paths below its own scanned folder. Folders are matched
by those paths, so ``Users/me/Downloads`` of two computers shares a row. Nothing here refers to a file that exists
on this computer, so nothing here can be opened, moved or removed.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from je_file_tree.core.compare import SavedScan, SavedScanError, load_saved
from je_file_tree.core.pacing import give_way

MAX_SCANS = 16
MAX_LABEL = 80
MAX_BYTES = 512 << 20
DEFAULT_ROWS = 1000
DEFAULT_DEPTH = 2


@dataclass(frozen=True, slots=True)
class ImportedScan:
    """One computer's saved scan under the name it is shown by."""

    label: str
    scan: SavedScan


@dataclass(frozen=True, slots=True)
class OverviewRow:
    """One folder path and its size in every scan (None where the scan does not have it)."""

    path: str
    sizes: tuple[int | None, ...]

    @property
    def largest(self) -> int:
        """The largest of its sizes."""
        return max((size for size in self.sizes if size is not None), default=0)

    @property
    def spread(self) -> int:
        """How far apart the scans are; a scan without the folder counts as nothing there."""
        known = [size or 0 for size in self.sizes]
        return max(known) - min(known)


@dataclass(frozen=True, slots=True)
class Overview:
    """The largest folders, and how many there are in all at the chosen depth."""

    scans: tuple[ImportedScan, ...]
    rows: tuple[OverviewRow, ...]
    count: int


def import_scan(file: str | os.PathLike[str]) -> ImportedScan:
    """Read a saved scan; its file name is the first label. Raises ``SavedScanError`` or ``OSError``."""
    path = Path(file)
    if path.stat().st_size > MAX_BYTES:
        raise SavedScanError("the file is too large")
    return ImportedScan(path.stem[:MAX_LABEL] or "scan", load_saved(path))


def unique_label(label: str, taken: Sequence[str]) -> str:
    """``label``, numbered when another scan already has it."""
    label = " ".join(label.split())[:MAX_LABEL] or "scan"
    if label not in taken:
        return label
    number = 2
    while f"{label} ({number})" in taken:
        number += 1
    return f"{label} ({number})"


def overview(scans: Sequence[ImportedScan], *, depth: int = DEFAULT_DEPTH, limit: int = DEFAULT_ROWS,
             cancel: threading.Event | None = None) -> Overview | None:
    """The folders down to ``depth`` levels, the largest first; None once cancelled."""
    if not 1 <= len(scans) <= MAX_SCANS or depth < 0 or limit < 1:
        raise ValueError("unusable overview")
    names: dict[str, str] = {}
    for item in scans:
        for key, folder in item.scan.folders.items():
            give_way()
            if cancel is not None and cancel.is_set():
                return None
            if (key.count("/") + 1 if key else 0) <= depth:
                names.setdefault(key, folder.path)
    rows = []
    for key, path in names.items():
        found = (item.scan.folders.get(key) for item in scans)
        rows.append(OverviewRow(path, tuple(None if folder is None else folder.size for folder in found)))
    rows.sort(key=lambda row: (-row.largest, row.path.lower()))
    return Overview(tuple(scans), tuple(rows[:limit]), len(rows))
