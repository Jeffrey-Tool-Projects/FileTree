"""Read where a Windows shortcut (``.lnk``) points, from the local path it records; nothing is resolved or run."""

from __future__ import annotations

import struct

MAX_BYTES = 1 << 20
_HEADER = 0x4C
_CLASS = bytes.fromhex("0114020000000000c000000000000046")
_HAS_ID_LIST, _HAS_LINK_INFO = 0x1, 0x2
_LOCAL = 0x1
_UNICODE_HEADER = 0x24
_LINK_INFO_HEADER = 0x1C


class ShortcutError(ValueError):
    """Not a shortcut, or a damaged one."""


def local_target(data: bytes) -> str | None:
    """The local path ``data`` points to; None when it records none (a web page, a network place, an app)."""
    if len(data) < _HEADER or struct.unpack_from("<I", data)[0] != _HEADER or data[4:20] != _CLASS:
        raise ShortcutError("not a shortcut")
    flags = struct.unpack_from("<I", data, 20)[0]
    offset = _HEADER
    try:
        if flags & _HAS_ID_LIST:
            offset += 2 + struct.unpack_from("<H", data, offset)[0]
        return _link_info(data, offset) if flags & _HAS_LINK_INFO else None
    except (struct.error, IndexError, UnicodeDecodeError) as error:
        raise ShortcutError("damaged shortcut") from error


def _link_info(data: bytes, start: int) -> str | None:
    size, header, flags, _volume, base, _network, suffix = struct.unpack_from("<7I", data, start)
    info = data[start:start + size]
    if len(info) != size or size < _LINK_INFO_HEADER:
        raise ShortcutError("damaged shortcut")
    if not flags & _LOCAL:
        return None
    if header >= _UNICODE_HEADER:
        wide_base, wide_suffix = struct.unpack_from("<2I", info, _LINK_INFO_HEADER)
        path = _wide(info, wide_base) + _wide(info, wide_suffix)
    else:
        path = _narrow(info, base) + _narrow(info, suffix)
    return path or None


def _wide(info: bytes, offset: int) -> str:
    end = offset
    while info[end:end + 2] != b"\0\0":
        if end + 2 > len(info):
            raise ShortcutError("damaged shortcut")
        end += 2
    return info[offset:end].decode("utf-16-le")


def _narrow(info: bytes, offset: int) -> str:
    """Text in the writer's code page, which the file does not name: anything but ASCII stays unknown."""
    end = info.index(b"\0", offset) if b"\0" in info[offset:] else len(info)
    return info[offset:end].decode("ascii")
