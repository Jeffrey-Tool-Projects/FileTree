"""Compact no-follow filesystem snapshots for revalidating a later approved operation."""

from __future__ import annotations

import os
import math
import stat
import struct
import sys
from dataclasses import dataclass
from types import SimpleNamespace
from typing import cast

_FORMAT = struct.Struct("<Q16sq16s16sIII")
_TIMES = struct.Struct("<dd")
_IDENTITY = struct.Struct("<Q16s48xI")  # the first two fields and the last one of ``_FORMAT``
NO_FILE_NUMBER = bytes(16)
_LINK_TAGS = frozenset({0xA0000003, 0xA000000C})
_LINK_FLAG = 0x10000
RECALL_ON_OPEN = 0x40000
_NORMAL = 0x80


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Identity and metadata of the entry itself, never of a symlink/junction target."""

    device: int
    inode: int
    size: int
    modified_ns: int
    changed_ns: int
    mode: int
    attributes: int
    links: int

    @property
    def is_link(self) -> bool:
        """Whether the entry is a symlink or Windows junction."""
        return bool(self.mode & _LINK_FLAG)

    @property
    def is_dir(self) -> bool:
        """Whether this entry is a directory (possibly a junction)."""
        return stat.S_ISDIR(self.mode & ~_LINK_FLAG)

    @property
    def identity(self) -> tuple[int, int]:
        """Device and file number; a zero file number denotes unavailable identity."""
        return self.device, self.inode


def pack_snapshot(info: os.stat_result, *, file_times: bool = False) -> bytes:
    """Pack metadata; optionally retain file atime/birthtime from the same stat, without another call.

    Times add 16 bytes only to regular-file snapshots (100k-entry measurement: +16 versus +64
    bytes for two float fields, measured 2026-10-07). Directory/link times remain unavailable.
    POSIX ctime is metadata-change time, never used as creation time.
    """
    link = stat.S_ISLNK(info.st_mode) or getattr(info, "st_reparse_tag", 0) in _LINK_TAGS
    mode = stat.S_IFMT(info.st_mode) | (_LINK_FLAG if link else 0)
    packed = _FORMAT.pack(info.st_dev, info.st_ino.to_bytes(16, "little"), info.st_size,
                        info.st_mtime_ns.to_bytes(16, "little", signed=True),
                        info.st_ctime_ns.to_bytes(16, "little", signed=True), mode,
                        getattr(info, "st_file_attributes", 0), info.st_nlink)
    if file_times and stat.S_ISREG(info.st_mode) and not link:
        birth = getattr(info, "st_birthtime", info.st_ctime if sys.platform == "win32" else 0.0)
        packed += _TIMES.pack(info.st_atime, birth)
    return packed


def unpack_snapshot(data: bytes) -> Snapshot:
    """Decode a snapshot only when its fields are needed."""
    if len(data) not in (_FORMAT.size, _FORMAT.size + _TIMES.size):
        raise ValueError("Invalid filesystem snapshot length")
    device, inode, size, modified, changed, mode, attributes, links = _FORMAT.unpack_from(data)
    return Snapshot(device, int.from_bytes(inode, "little"), size,
                    int.from_bytes(modified, "little", signed=True), int.from_bytes(changed, "little", signed=True),
                    mode, attributes, links)


def link_identity(data: bytes) -> tuple[int, bytes, int]:
    """Device, file number and link count, for a walk over every file that needs nothing else.

    The file number is its 16 little-endian bytes, ``NO_FILE_NUMBER`` when the identity is unknown.
    Measured 2026-11-15 on 686,000 files: building a ``Snapshot`` per file took most of the 3.6 s the
    capacity ledger needed; with this the ledger takes 1.1 s and reports the same numbers.
    """
    if len(data) not in (_FORMAT.size, _FORMAT.size + _TIMES.size):
        raise ValueError("Invalid filesystem snapshot length")
    return _IDENTITY.unpack_from(data)


def snapshot_times(data: bytes | None) -> tuple[float | None, float | None]:
    """Optional recorded access/creation times; invalid, nonpositive or absent values stay unknown."""
    if data is None or len(data) != _FORMAT.size + _TIMES.size:
        return None, None
    accessed, created = _TIMES.unpack_from(data, _FORMAT.size)
    return (_usable_time(accessed), _usable_time(created))


def stable_snapshot(data: bytes) -> bytes:
    """Identity/size/change metadata only: optional access dates cannot invalidate a content read."""
    unpack_snapshot(data)  # Validate both supported snapshot lengths.
    return data[:_FORMAT.size]


def _usable_time(value: float) -> float | None:
    return value if math.isfinite(value) and value > 0 else None


def path_metadata(info: os.stat_result, listed_attributes: int = 0) -> os.stat_result:
    """``info`` of a path with the recall-on-open attribute taken from its directory listing instead.

    Windows documents ``FILE_ATTRIBUTE_RECALL_ON_OPEN`` (0x40000) for directory listings only. A query
    of one path by name (``os.lstat`` since Python 3.12) can report the same bit for an ordinary file
    that no program has opened yet, and stops once one has. Measured 2026-11-14 on Windows 11: 1,606
    of 6,265 files of the SysWOW64 system folder had it, their listing and a query by handle did not, and
    the scan counted them as taking no space. Without a listing (the default) the bit is cleared.
    A file with no other attribute then reads as ``FILE_ATTRIBUTE_NORMAL``, which is what its listing
    and a query by handle report for it.
    """
    attributes = getattr(info, "st_file_attributes", 0)
    wanted = attributes & ~RECALL_ON_OPEN | listed_attributes & RECALL_ON_OPEN
    if wanted == attributes:
        return info
    wanted = wanted or _NORMAL
    copy = SimpleNamespace(**{name: getattr(info, name) for name in dir(info) if name.startswith("st_")})
    copy.st_file_attributes = wanted
    return cast(os.stat_result, copy)


def stat_snapshot(path: str) -> bytes:
    """Read the entry without following a link, including Windows file identity."""
    return pack_snapshot(path_metadata(os.lstat(path)))
