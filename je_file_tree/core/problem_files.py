"""Find recorded files that tend to cause trouble: empty ones, dead links, long paths and unusable names.

The survey walks the scanned tree. Only links and Windows shortcuts are looked at on disk: a link's own target
text, a small local shortcut's recorded path, and whether an entry exists there, without following anything.
A target on a network or an absent drive is unknown, never called dead.
"""

from __future__ import annotations

import ntpath
import os
import re
import stat
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

from je_file_tree.core.node import Node
from je_file_tree.core.pacing import give_way
from je_file_tree.core.shell_link import MAX_BYTES, ShortcutError, local_target
from je_file_tree.core.snapshot import RECALL_ON_OPEN, unpack_snapshot

EMPTY, DEAD_LINK, LONG_PATH, BAD_NAME = "empty", "dead_link", "long_path", "bad_name"
KINDS = (DEAD_LINK, BAD_NAME, LONG_PATH, EMPTY)
WINDOWS_PATH_LIMIT = 260  # MAX_PATH counts the ending null: 259 characters are the most
MAX_LINKS = 20_000
# Forbidden characters, a final dot or space, or a device name whatever its extension, in one search per name.
_BAD_NAME = re.compile(r"""[<>:"/\\|?*\x00-\x1f]|[ .]$"""
                       r"|^(?:con|prn|aux|nul|conin\$|conout\$|(?:com|lpt)[1-9¹²³]) *(?:\.|$)",
                       re.IGNORECASE)
_RECALL_DATA, _OFFLINE = 0x400000, 0x1000


@dataclass(frozen=True, slots=True)
class ProblemEntry:
    """One entry with everything found about it, and where its link points if that is the problem."""

    node: Node
    kinds: tuple[str, ...]
    target: str = ""


@dataclass(slots=True)
class ProblemFiles:
    """The first entries of each kind, how many there are of each, and links that could not be judged."""

    rows: list[ProblemEntry] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=lambda: dict.fromkeys(KINDS, 0))
    unknown_links: int = 0
    incomplete: bool = False

    @property
    def count(self) -> int:
        """Every problem found, whether or not its entry is listed."""
        return sum(self.counts.values())


def bad_name(name: str) -> bool:
    """Whether Windows refuses or mangles ``name``: forbidden characters, a device name, a final dot or space."""
    return _BAD_NAME.search(name) is not None


def problem_files(root: Node, *, limit: int = 1000, cancel: threading.Event | None = None,
                  platform: str = sys.platform) -> ProblemFiles | None:
    """Survey ``root`` on a worker; None once cancelled."""
    if limit < 1:
        raise ValueError("limit must be positive")
    result = ProblemFiles()
    links: list[Node] = []
    start = len(root.path or "")
    stack: list[tuple[Node, int]] = [(root, start)]
    while stack:
        folder, length = stack.pop()
        if cancel is not None and cancel.is_set():
            return None
        give_way()
        result.incomplete |= bool(folder.error)
        above = length + (0 if not length or folder.name.endswith(("/", "\\")) else 1)
        for child in folder.children:
            size = above + len(child.name)
            if child.is_dir and not child.is_link:
                stack.append((child, size))
            elif _may_point(child, platform):
                links.append(child)
            kinds = _kinds(child, size, platform, named=bool(folder.name))
            if kinds:
                _add(result, ProblemEntry(child, kinds), limit)
    return result if _check_links(result, links, limit, cancel) else None


def _kinds(node: Node, length: int, platform: str, *, named: bool) -> tuple[str, ...]:
    kinds = []
    if named and bad_name(node.name):
        kinds.append(BAD_NAME)
    if platform == "win32" and length >= WINDOWS_PATH_LIMIT:
        kinds.append(LONG_PATH)
    if not node.is_dir and not node.is_link and node.error is None and node.size == 0:
        kinds.append(EMPTY)
    return tuple(kinds)


def _add(result: ProblemFiles, entry: ProblemEntry, limit: int) -> None:
    listed = any(result.counts[kind] < limit for kind in entry.kinds)
    for kind in entry.kinds:
        result.counts[kind] += 1
    if listed:
        result.rows.append(entry)


def _may_point(node: Node, platform: str) -> bool:
    if node.is_link:
        return True
    return (platform == "win32" and not node.is_dir and node.error is None and 0 < node.size <= MAX_BYTES
            and node.name.casefold().endswith(".lnk") and _stored_here(node))


def _stored_here(node: Node) -> bool:
    """Whether reading the file downloads nothing."""
    if node.snapshot is None:
        return False
    return not unpack_snapshot(node.snapshot).attributes & (RECALL_ON_OPEN | _RECALL_DATA | _OFFLINE)


def _check_links(result: ProblemFiles, links: list[Node], limit: int, cancel: threading.Event | None) -> bool:
    for node in links[:MAX_LINKS]:
        if cancel is not None and cancel.is_set():
            return False
        give_way()
        target = _target(node)
        exists = None if target is None else target_exists(target)
        if exists is None:
            result.unknown_links += 1
        elif not exists:
            _add(result, ProblemEntry(node, (DEAD_LINK,), target or ""), limit)
    result.unknown_links += max(0, len(links) - MAX_LINKS)
    return True


def _target(node: Node) -> str | None:
    path = node.path
    if path is None:
        return None
    try:
        if node.is_link:
            text = os.readlink(path)
            return os.path.normpath(os.path.join(os.path.dirname(path), text))
        return _shortcut_target(path)
    except (OSError, ValueError):
        return None


def _shortcut_target(path: str) -> str | None:
    if not stat.S_ISREG(os.lstat(path).st_mode):
        return None
    with Path(path).open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    try:
        return local_target(data) if len(data) <= MAX_BYTES else None
    except ShortcutError:
        return None


def target_exists(target: str) -> bool | None:
    """Whether an entry exists at ``target`` (itself, not what it may link to); None when that cannot be told."""
    if sys.platform == "win32":
        target = target.removeprefix("\\\\?\\")
        drive, tail = ntpath.splitdrive(target)
        if not drive or drive.startswith(("\\\\", "//")) or not tail.startswith(("\\", "/")):
            return None  # network places and volume names: asking could wait for a server
        if not os.path.exists(drive + "\\"):
            return None  # an absent drive says nothing about the file
    try:
        os.lstat(target)
    except FileNotFoundError:
        return False
    except (OSError, ValueError):
        return None
    return True
