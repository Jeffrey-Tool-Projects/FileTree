"""Read-only native change feeds request fresh scans; notifications never grant source authority."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import os
import stat
import sys
import threading

from je_file_tree.core.coverage import coverage_of
from je_file_tree.core.node import Node
from je_file_tree.core.pacing import give_way
from je_file_tree.core.snapshot import stat_snapshot, unpack_snapshot

MAX_FOLDERS = 1_000_000
MAX_SHARED = 65536
MAX_CHANGED = 256
POLL_SECONDS = 0.25


@dataclass(frozen=True, slots=True)
class ChangeBatch:
    """Folders whose own entries changed, folders to read whole, or a full-root request after loss.

    ``folders`` and ``trees`` are reported paths inside the scan, never targets: the window maps each to
    the deepest folder it scanned there (``node.folder_holding``) and reads that folder again.
    """

    folders: tuple[str, ...] = ()
    full: bool = False
    reason: str = ""
    trees: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WatchFolder:
    """A captured ordinary folder identity, never a notification-derived filesystem target."""

    path: str
    device: int
    inode: int


@dataclass(frozen=True, slots=True)
class WatchFile:
    """One observed shared ordinary inode and its captured parents, including external-alias changes."""

    path: str
    device: int
    inode: int
    parents: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WatchScope:
    """Compact native feed metadata, separate from the scan tree and all operation approvals."""

    folders: tuple[WatchFolder, ...]
    shared: tuple[WatchFile, ...] = ()


def _shared_file(node: Node, device: int, files: dict) -> None:
    if node.is_dir or node.is_link or node.snapshot is None:
        return
    info = unpack_snapshot(node.snapshot)
    if not stat.S_ISREG(info.mode) or info.links <= 1:
        return
    if info.device != device or not info.inode or node.path is None or node.parent is None:
        raise ValueError("Shared watched file lacks a captured same-volume identity")
    if info.identity not in files:
        files[info.identity] = (node.path, set())
    files[info.identity][1].add(node.parent.path)
    if len(files) > MAX_SHARED:
        raise ValueError("Follow changes exceeds the shared-inode limit")


def captured_scope(root: Node, cancel: threading.Event) -> WatchScope:
    """Capture complete physical scopes off the GUI thread; links and mount nodes remain excluded."""
    if root.path is None or root.is_link or not root.is_dir or root.snapshot is None:
        raise ValueError("Follow changes requires a captured physical folder")
    coverage = coverage_of(root, cancel=cancel)
    if coverage is None:
        return WatchScope(())
    if not coverage.complete or coverage.unsafe:
        raise ValueError("Follow changes requires complete scan coverage")
    result, shared = [], {}
    device = unpack_snapshot(root.snapshot).device
    if not device:
        raise ValueError("Follow changes lacks a volume identity")
    for node in root.iter_nodes():
        if cancel.is_set():
            return WatchScope(())
        _shared_file(node, device, shared)
        if node.is_dir:
            give_way()
            if node.is_link:
                continue
            if node.snapshot is None:
                raise ValueError("Follow changes lacks a folder identity")
            info = unpack_snapshot(node.snapshot)
            if info.is_link or info.device != device or not info.inode or node.path is None:
                raise ValueError("Follow changes has an unknown folder identity")
            result.append(WatchFolder(node.path, info.device, info.inode))
            if len(result) > MAX_FOLDERS:
                raise ValueError("Follow changes exceeds the captured-folder limit")
    files = tuple(WatchFile(path, key[0], key[1], tuple(sorted(parents)))
                  for key, (path, parents) in shared.items())
    return WatchScope(tuple(result), files)


def check_folder(folder: WatchFolder) -> None:
    """Reject changed/linked folder paths; a passing observation grants no filesystem operation."""
    info = unpack_snapshot(stat_snapshot(folder.path))
    if (info.is_link or not stat.S_ISDIR(info.mode) or info.identity != (folder.device, folder.inode)
            or info.attributes & 0x400):
        raise ValueError("Watched folder identity changed")


def changed(folders: set[str], *, full: bool = False, reason: str = "", trees: set[str] | frozenset[str] = frozenset()
            ) -> ChangeBatch:
    """Bound an event batch; past ``MAX_CHANGED`` paths, the deepest give way to their parent folders, read whole.

    A build touching a thousand folders refreshes the few folders holding them instead of the whole scan.
    """
    if full:
        return ChangeBatch(full=True, reason=reason or "overflow")
    folders, trees = set(folders), set(trees)
    while len(folders) + len(trees) > MAX_CHANGED:
        deepest = max(map(_depth, folders | trees))
        if not deepest:
            return ChangeBatch(full=True, reason=reason or "overflow")  # only drive roots are left
        lifted = {os.path.dirname(path) for path in folders | trees if _depth(path) == deepest}
        folders = {path for path in folders if _depth(path) < deepest} - lifted
        trees = {path for path in trees if _depth(path) < deepest} | lifted
    return ChangeBatch(tuple(sorted(folders)), reason=reason, trees=tuple(sorted(trees)))


def _depth(path: str) -> int:
    return path.rstrip("\\/").count(os.sep)


def merged(first: ChangeBatch, second: ChangeBatch) -> ChangeBatch:
    """Both batches as one, bounded like ``changed``."""
    return changed(set(first.folders) | set(second.folders), full=first.full or second.full,
                   reason=second.reason or first.reason, trees=set(first.trees) | set(second.trees))


Position = tuple[int, int]  # an NTFS change journal and the next record to read from it


def watch(root: Node, on_change: Callable[[ChangeBatch], None], cancel: threading.Event,
          *, ready: Callable[[str], None] | None = None) -> None:
    """``captured_scope`` then ``watch_scope``: a joinable native feed for ``root``."""
    watch_scope(captured_scope(root, cancel), on_change, cancel, ready=ready)


def watch_scope(scope: WatchScope, on_change: Callable[[ChangeBatch], None], cancel: threading.Event,  # noqa: PLR0913
                *, ready: Callable[[str], None] | None = None, since: Position | None = None,
                moved: Callable[[Position], None] | None = None) -> None:
    """Joinable native metadata feed; caller must rescan and separately revalidate later operations.

    Windows uses an existing NTFS USN journal when readable, otherwise one recursive directory
    handle. Linux uses one inotify descriptor and kernel watches for captured ordinary folders.
    No journal creation/deletion, payload reads, Qt watchers or filesystem mutations are involved.
    Overflow/gaps request full rescans; unsupported/failed feeds raise visible OSError/ValueError.
    Setup/rearm and concurrent scans remain observational rather than a consistent live snapshot.
    A journal feed reports its read position to ``moved``; one started ``since`` such a position reads
    on from there, so a feed armed after a refresh misses nothing that happened while it was armed.
    """
    folders = scope.folders
    if not folders or cancel.is_set():
        return
    check_folder(folders[0])
    if sys.platform == "win32":
        from je_file_tree.core.windows_watch import watch_windows  # noqa: PLC0415 - native backend

        watch_windows(folders, on_change, cancel, ready, scope.shared, since=since, moved=moved)
    elif sys.platform.startswith("linux"):
        from je_file_tree.core.linux_watch import watch_linux  # noqa: PLC0415 - native backend

        watch_linux(folders, on_change, cancel, ready, scope.shared)
    elif sys.platform == "darwin":
        from je_file_tree.core.mac_watch import watch_mac  # noqa: PLC0415 - native backend

        watch_mac(folders, on_change, cancel, ready, scope.shared)
    else:
        raise ValueError("Follow changes is available on Windows, Linux and macOS")
