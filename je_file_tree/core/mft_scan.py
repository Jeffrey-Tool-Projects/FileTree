"""Scan folders of an NTFS volume from its master file table instead of listing every folder.

Listing costs a call into the file system per folder and a query per entry; most of a scan's time is
spent there, inside Windows (``docs/updates`` U-20261115-02, -04). The master file table (MFT) holds
one record per file with the same metadata, and ``je_file_tree._native.mft_open`` reads all of it in
one pass over the volume. ``table_reader`` then answers the scanner's folder reads from memory, in the
format of the native folder reader, so exclusions, hidden entries, links, cancelling and everything
after the scan work as they always do.

Measured 2026-11-15 on a 237 GB system volume (NVMe, 1.56 million records, 1.42 million names): the
table is read and indexed in 2.0 to 2.4 s. Compared with ``os.lstat`` over 807,657 entries of the
users folder: 190 differed, in size or modification time only; the timings of whole scans are in
``docs/updates`` U-20261115-05.

What it does not change: every operation still compares a fresh ``os.lstat`` with the recorded
snapshot first. Where the table described an entry differently (it can be a few seconds behind the
running system) the entry is refused as changed, and rescanning its folder, which lists it the
ordinary way, records it afresh.

It is used only when all of this holds, and the scan lists folders as before otherwise:

* the scan asked for it (``ScanOptions.mft``) and ``FILE_TREE_MFT_SCAN`` is not ``0``;
* the scan starts at a folder of a lettered drive (not a network path);
* the volume is NTFS and the process may read it (an administrator);
* no record failed its consistency check, and the table describes the folder the scan starts from
  exactly as ``os.lstat`` does. That also rules out a folder reached through a link or a mounted volume:
  its volume number is another one.

The whole table is read whatever the folder (owner decision, 2026-11-15: use the table whenever it can
be used). On the volume measured that is 2.0 to 2.4 s before the first entry appears, which is more than
listing a small folder takes. The window rescans a single folder of a finished scan by listing it, so
that what an operation just changed is read from the running system, not from the table on disk.

A table also names what a listing is refused: the contents of folders this account may not open.
Those entries are shown with their sizes; operations on them are refused like on any unreadable entry.
"""

from __future__ import annotations

import os
import sys

from je_file_tree.core import native_scan
from je_file_tree.core.snapshot import pack_snapshot, path_metadata

DISABLE_VARIABLE = "FILE_TREE_MFT_SCAN"  # set to 0 to always list folders
_DRIVE_PREFIX_LENGTH = 3  # "C:\\"
_REFERENCE_BYTES = slice(8, 16)  # the file reference inside a snapshot: the low half of its file number
_REFERENCE_MASK = (1 << 64) - 1


def drive_of(root_path: str) -> str | None:
    """``"C:"`` when ``root_path`` is an absolute path on a lettered drive, else None."""
    prefix = root_path[:_DRIVE_PREFIX_LENGTH]
    if len(prefix) != _DRIVE_PREFIX_LENGTH or prefix[1:] not in (":\\", ":/") or not prefix[0].isascii() or (
            not prefix[0].isalpha()):
        return None
    return prefix[:2]


def table_reader(root_path: str) -> native_scan.Reader | None:
    """``read(path, file_times)`` over the master file table of the drive holding the folder ``root_path``.

    None when the table is not to be used (see the module text); the caller then lists folders.
    """
    drive = drive_of(root_path)
    chosen = native_scan.chosen() if drive is not None else None
    if chosen is None or sys.platform != "win32" or os.environ.get(DISABLE_VARIABLE, "1") == "0":
        return None
    native, change_time, short = chosen
    if not hasattr(native, "mft_open"):
        return None  # a module built before it could read the table
    try:
        table = native.mft_open(drive)
        if native.mft_info(table)[3]:
            return None  # a damaged record could hide a whole folder
        reference = os.lstat(root_path).st_ino & _REFERENCE_MASK
        for file_times in (False, True):
            expected = pack_snapshot(path_metadata(os.lstat(root_path)), file_times=file_times)
            if native.mft_snapshot(table, reference, file_times, change_time, short) != expected:
                return None
    except (OSError, ValueError):
        return None  # not NTFS, not allowed to read the volume, or the root is not what the table says
    return _reader(native, table, (change_time, short), root_path, reference)


def _reader(native: object, table: object, choices: tuple[bool, bool], root_path: str,
            root: int) -> native_scan.Reader:
    folders = {root_path: root}  # the reference of each folder found and not read yet, by path
    change_time, short = choices

    def read(path: str, file_times: bool) -> list[native_scan.Row]:
        try:
            reference = folders.pop(path)
        except KeyError:
            raise FileNotFoundError(path) from None
        rows = native.mft_rows(table, reference, file_times, change_time, short)  # type: ignore[attr-defined]
        for row in rows:
            if row[1] == native_scan.KIND_FOLDER:
                folders[os.path.join(path, row[0])] = int.from_bytes(row[4][_REFERENCE_BYTES], "little")
        return rows

    return read
