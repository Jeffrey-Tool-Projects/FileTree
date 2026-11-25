"""Read the beginning of a recorded file for a preview: bounded, unchanged since the scan, never from the cloud.

The file is opened through the same guard as archive listings: it must still be the scanned regular file, links
and files kept only online are refused, and it is checked again after reading. Nothing is written or run.
"""

from __future__ import annotations

import codecs
import threading
from dataclasses import dataclass

from je_file_tree.core.archives import ArchiveReader, opened, read_archive
from je_file_tree.core.node import Node

IMAGE, TEXT, ARCHIVE, BINARY = "image", "text", "archive", "binary"
IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico"})
ARCHIVE_SUFFIXES = frozenset({".zip", ".7z", ".rar"})
MAX_IMAGE_BYTES = 32 << 20
TEXT_BYTES = 64 << 10
MAX_LINES = 400
MAX_LINE = 2000
MAX_MEMBERS = 200
_CONTROLS = frozenset(range(32)) - {9, 10, 12, 13, 27}
_MOST_CONTROLS = .02
_BOMS = ((codecs.BOM_UTF8, "utf-8-sig"), (codecs.BOM_UTF16_LE, "utf-16"), (codecs.BOM_UTF16_BE, "utf-16"))


class PreviewError(OSError):
    """There is nothing to show for this file."""


@dataclass(frozen=True, slots=True)
class Preview:
    """What was read: text, undecoded picture bytes or member lines, and whether there is more."""

    kind: str
    text: str = ""
    data: bytes = b""
    lines: tuple[tuple[str, int], ...] = ()
    more: bool = False


def suffix_of(name: str) -> str:
    """The lower-case last extension of ``name``, with its dot."""
    return "." + name.rsplit(".", 1)[-1].lower() if "." in name.strip(".") else ""


def read_preview(node: Node, readers: dict[str, ArchiveReader], cancel: threading.Event | None = None) -> Preview:
    """Read a preview of the regular file ``node`` on a worker; raises OSError when it cannot be shown."""
    suffix = suffix_of(node.name)
    if suffix in readers:
        return _archive(node, readers[suffix], cancel)
    with opened(node) as stream:
        if suffix in IMAGE_SUFFIXES:
            data = stream.read(MAX_IMAGE_BYTES + 1)
            if len(data) > MAX_IMAGE_BYTES:
                raise PreviewError("the picture is too large")
            return Preview(IMAGE, data=data)
        data = stream.read(TEXT_BYTES + 1)
    text = decode(data[:TEXT_BYTES], whole=len(data) <= TEXT_BYTES)
    if text is None:
        return Preview(BINARY, more=len(data) > TEXT_BYTES)
    shown, cut = _cut(text)
    return Preview(TEXT, text=shown, more=cut or len(data) > TEXT_BYTES)


def decode(data: bytes, *, whole: bool) -> str | None:
    """Text in UTF-8, or UTF-16 with a byte-order mark; None for anything else."""
    encoding = next((name for mark, name in _BOMS if data.startswith(mark)), "utf-8")
    if encoding != "utf-16" and data and sum(byte in _CONTROLS for byte in data) > _MOST_CONTROLS * len(data):
        return None
    try:
        # A final character cut by the limit is no reason to call a file binary.
        text = codecs.getincrementaldecoder(encoding)().decode(data, final=whole)
    except UnicodeDecodeError:
        return None
    return text.replace("\0", "\N{REPLACEMENT CHARACTER}")


def _cut(text: str) -> tuple[str, bool]:
    lines = text.splitlines()
    long = any(len(line) > MAX_LINE for line in lines[:MAX_LINES])
    return "\n".join(line[:MAX_LINE] for line in lines[:MAX_LINES]), long or len(lines) > MAX_LINES


def _archive(node: Node, reader: ArchiveReader, cancel: threading.Event | None) -> Preview:
    """The first members by path, from the archive's directory only: nothing is extracted."""
    inventory = read_archive(node, reader=reader, cancel=cancel)
    lines: list[tuple[str, int]] = []
    more = bool(inventory.rejected)
    stack = [(child, "") for child in reversed(inventory.children)]
    while stack:
        entry, above = stack.pop()
        if len(lines) >= MAX_MEMBERS:
            more = True
            break
        path = f"{above}{entry.name}{'/' if entry.is_dir else ''}"
        lines.append((path, entry.size))
        stack.extend((child, path) for child in reversed(entry.children))
    return Preview(ARCHIVE, lines=tuple(lines), more=more)
