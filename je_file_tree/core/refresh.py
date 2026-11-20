"""Put a fresh listing of one scanned folder in place, keeping the subfolders it did not read again.

Follow changes learns which folders' own entries changed. Reading such a folder with
``ScanOptions(keep=kept_subfolders(folder))`` lists it again but leaves each subfolder it already holds
unread (marked ``KEPT``); ``refill`` then puts that listing into the same ``Node`` and hangs the kept
subfolders back, so a change directly in the scanned folder no longer reads the whole scan again.
A kept subfolder is matched by name and file identity, so one that was replaced is read instead.
"""

from __future__ import annotations

import os
from collections.abc import Iterable

from je_file_tree.core.node import Node
from je_file_tree.core.scanner import EXCLUDED, HIDDEN_OMITTED, KEPT, PARTIAL_FOLDER
from je_file_tree.core.snapshot import unpack_snapshot

_KEEPABLE = (None, PARTIAL_FOLDER, HIDDEN_OMITTED)  # read folders; one that failed or was stopped is read again


def kept_subfolders(folder: Node) -> frozenset[tuple[str, int, int]]:
    """``(name, device, file number)`` of the read subfolders directly in ``folder`` that a refresh may keep."""
    keep = set()
    for child in folder.children:
        if child.is_dir and not child.is_link and child.error in _KEEPABLE and child.snapshot is not None:
            device, number = unpack_snapshot(child.snapshot).identity
            if number:
                keep.add((child.name, device, number))
    return frozenset(keep)


def _identity(node: Node) -> tuple[int, int] | None:
    return None if node.snapshot is None else unpack_snapshot(node.snapshot).identity


def refill(folder: Node, fresh: Node) -> frozenset[str] | None:
    """Make ``folder`` hold ``fresh`` (a listing of it), correcting every total above it.

    ``folder`` keeps its identity, so the window's place in the tree and a root stay valid; its other
    old entries are detached. Returns the names of the subfolders kept, or None with nothing changed
    when a ``KEPT`` entry has no subfolder of the same name and identity left in ``folder``.
    """
    if not isinstance(folder.children, list) or not isinstance(fresh.children, list):
        return None
    known = {child.name: child for child in folder.children if child.is_dir and not child.is_link}
    swaps = []
    for index, child in enumerate(fresh.children):
        if child.error != KEPT:
            continue
        old = known.get(child.name)
        if old is None or _identity(old) is None or _identity(old) != _identity(child):
            return None
        swaps.append((index, old))
    children = fresh.children
    for index, old in swaps:
        children[index] = old
    kept = {id(old) for _, old in swaps}
    for child in folder.children:
        if id(child) not in kept:
            child.parent = None
    for child in children:
        child.parent = folder
    before = folder.size, folder.allocated, folder.file_count, folder.dir_count
    own = 0.0 if folder.parent is None or fresh.snapshot is None else unpack_snapshot(fresh.snapshot).modified_ns / 1e9
    folder.children = children
    folder.snapshot, folder.error = fresh.snapshot, fresh.error
    _total(folder, own)
    _correct_above(folder, before)
    return frozenset(old.name for _, old in swaps)


def _total(folder: Node, own: float) -> None:
    """Add up ``folder``'s direct entries the way the scanner does and sort them largest first."""
    children = folder.children
    folder.size = sum(child.size for child in children)
    folder.allocated = sum(child.allocated for child in children)
    folder.file_count = sum(child.file_count for child in children)
    folder.dir_count = sum(1 + child.dir_count for child in children
                           if child.is_dir and not child.is_link and child.error != EXCLUDED)
    folder.modified = max([own, *(child.modified for child in children)])
    if isinstance(children, list):
        children.sort(key=lambda child: (-child.size, child.name.lower()))


def _correct_above(folder: Node, before: tuple[int, int, int, int]) -> None:
    size, allocated = folder.size - before[0], folder.allocated - before[1]
    files, folders = folder.file_count - before[2], folder.dir_count - before[3]
    node = folder.parent
    while node is not None:
        node.size += size
        node.allocated += allocated
        node.file_count += files
        node.dir_count += folders
        node.modified = max(node.modified, folder.modified)
        node = node.parent


def refreshed_errors(errors: Iterable[tuple[str, str]], folder: str, kept: frozenset[str],
                     fresh: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    """``errors`` without those a refill of ``folder`` replaced, plus the listing's own ``fresh`` ones.

    What was recorded inside a kept subfolder stays; ``folder`` itself and everything else in it was
    read again.
    """
    prefix = folder.rstrip("\\/") + os.sep

    def replaced(path: str) -> bool:
        if path == folder:
            return True
        return path.startswith(prefix) and path[len(prefix):].split(os.sep, 1)[0] not in kept

    return [error for error in errors if not replaced(error[0])] + list(fresh)
