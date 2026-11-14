"""Permanently delete exactly the entries a user approved, each one checked against its scan record.

FileTree never chooses what to delete. ``MainWindow.delete_permanently`` asks the user and passes
the approved entries here; this module removes those entries and, for an approved folder, what
the scan recorded inside it, and nothing else:

* Every removal goes through ``remove_entry``, the one call that removes anything. The test suite
  wraps it and refuses any path outside pytest's temporary directory.
* Right before each removal the entry is compared with its no-follow scan snapshot (link state,
  kind, file identity and, for files and links, size, times, attributes and link count), and its
  parent folders are resolved to exactly the folders the scan recorded, so no link above it can
  redirect the removal. A changed, missing or replaced entry is refused and reported.
* A folder is walked from its scan record only: bottom-up, without recursion, never by listing
  the disk, a pattern or a name alone. Entries that appeared after the scan are reported and
  left in place, and so is their folder: the only folder removal is that of an empty folder.
* Links (symlinks, junctions) are removed as the link itself and never followed or entered.
  Windows volume mount folders, POSIX mount points and anything on another volume are refused.
* Windows read-only entries are refused and reported; FileTree never clears their attributes.

Residual risk: another program can still act between the last check and the removal. On Windows
the entry itself (never a link target) is opened and that open object's identity is compared
before exactly that object is marked for deletion, so a swapped-in replacement is refused. POSIX
anchors the parent folder by descriptor and compares both identities, but a replacement swapped
in between ``fstatat`` and ``unlinkat`` cannot be excluded: POSIX has no conditional unlink.
"""

from __future__ import annotations

import ctypes
import os
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from je_file_tree.core.node import Node, outermost
from je_file_tree.core.operations import check_place
from je_file_tree.core.pacing import give_way
from je_file_tree.core.protected import Protection, protection_of
from je_file_tree.core.snapshot import Snapshot, stat_snapshot, unpack_snapshot
from je_file_tree.core.system_files import system_file

if os.name == "nt":
    import msvcrt

DELETED, PARTIAL, SKIPPED, FAILED = "deleted", "partial", "skipped", "failed"
PENDING = "pending"  # failure detail: the system accepted the removal but the entry is still there
_READ_ONLY = 0x1  # FILE_ATTRIBUTE_READONLY
_DELETE_ACCESS, _READ_ATTRIBUTES, _SHARE_ALL, _OPEN_EXISTING = 0x00010000, 0x0080, 0x7, 3
_OPEN_ENTRY_ITSELF = 0x00200000 | 0x02000000  # FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTICS
_DISPOSITION, _DISPOSITION_EX = 4, 21  # FileDispositionInfo, FileDispositionInfoEx
_DELETE_POSIX = 0x1 | 0x2  # FILE_DISPOSITION_FLAG_DELETE | FILE_DISPOSITION_FLAG_POSIX_SEMANTICS
_EX_UNSUPPORTED = frozenset({1, 50, 87})  # invalid function, not supported, invalid parameter
_PROGRESS_SECONDS = 0.1

Finished = Callable[[Node, str, str], None]


class EntryChangedError(Exception):
    """The entry at a path is no longer the one the scan recorded; nothing was removed."""


@dataclass(slots=True)
class DeleteResult:
    """Removed approved entries, kept folders, refusals (path, reason key) and failures (path, detail)."""

    removed: list[Node] = field(default_factory=list)
    kept: list[Node] = field(default_factory=list)
    refused: list[tuple[str, str]] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)
    parents: list[Node] = field(default_factory=list)
    removed_entries: int = 0
    removed_bytes: int = 0


def remove_entry(path: str, expected: bytes, parent: bytes, *, directory: bool) -> None:
    """The only call that removes anything: one file or link, or one empty folder, still ``expected``.

    ``expected`` and ``parent`` are the scan snapshots of the entry and of its folder. A link is
    removed as the link itself. A folder that is not empty is refused by the system. Raises
    ``EntryChangedError`` when the entry or (POSIX) its folder is no longer the recorded one, and
    ``OSError`` when the system refuses.
    """
    if os.name == "nt":
        _remove_windows(path, expected)
    else:
        _remove_posix(path, expected, parent, directory=directory)


def delete_entries(root: Node, nodes: Sequence[Node], *, places: Sequence[Protection] = (),
                   approved: dict[Node, Protection | None] | None = None,
                   cancel: threading.Event | None = None, progress: Callable[[int], None] | None = None,
                   finished: Finished | None = None) -> DeleteResult:
    """Permanently delete exactly the approved ``nodes`` of the scan ``root``; run it on a worker thread.

    ``approved`` holds the protection each entry had when the user approved it; a different one
    now refuses the entry. ``cancel`` is checked between entries. ``progress`` receives the number
    of removed entries now and then, ``finished`` each approved entry with its status (one of
    ``DELETED``, ``PARTIAL``, ``SKIPPED``, ``FAILED``) and reason key.
    """
    result = DeleteResult()
    run = _Run(result, cancel, progress)
    approvals = approved or {}
    for node in outermost(nodes):
        if node.parent is not None and node.parent not in result.parents:
            result.parents.append(node.parent)
        if run.cancelled():
            result.refused.append((node.path or node.name, "cancelled"))
            status = SKIPPED, "cancelled"
        else:
            status = run.approved(node, root, places, approvals.get(node))
        if finished is not None:
            finished(node, *status)
    if progress is not None:
        progress(result.removed_entries)
    return result


@dataclass(frozen=True, slots=True)
class _Scope:
    top: Node
    root: Node
    places: Sequence[Protection]
    approval: Protection | None
    base: str  # the resolved folder that holds ``top``
    device: int


class _Run:
    """One batch: the result so far and the folders kept because something inside them stayed."""

    def __init__(self, result: DeleteResult, cancel: threading.Event | None,
                 progress: Callable[[int], None] | None) -> None:
        self.result, self.cancel, self.progress = result, cancel, progress
        self.blocked: set[Node] = set()
        self.reported = 0.0

    def cancelled(self) -> bool:
        """Whether the user asked to stop."""
        return self.cancel is not None and self.cancel.is_set()

    def approved(self, node: Node, root: Node, places: Sequence[Protection],
                 approval: Protection | None) -> tuple[str, str]:
        """Delete one approved entry (a folder with its recorded contents); its status and reason."""
        before = self.result.removed_entries, len(self.result.refused), len(self.result.failed)
        scope = _scope(node, root, places, approval)
        if isinstance(scope, str):
            self.result.refused.append((node.path or node.name, scope))
            return SKIPPED, scope
        if node.is_dir and not node.is_link:
            self._walk(scope)
        else:
            self._remove(node, scope, folder=False)
        return self._status(node, before)

    def _status(self, node: Node, before: tuple[int, int, int]) -> tuple[str, str]:
        result = self.result
        if result.removed and result.removed[-1] is node:
            return DELETED, ""
        if node in self.blocked:  # a folder left in place because something inside it stayed
            result.refused.append((node.path, "cancelled" if self.cancelled() else "not_empty"))
        if node.is_dir and not node.is_link:
            result.kept.append(node)
        rows = result.refused[before[1]:]
        detail = rows[-1][1] if node in self.blocked else rows[0][1] if rows else "failed"
        if result.removed_entries > before[0]:
            return PARTIAL, detail
        return (FAILED, "") if not rows and len(result.failed) > before[2] else (SKIPPED, detail)

    def _walk(self, scope: _Scope) -> None:
        """Children before their folder, from the scan record only; a stack instead of recursion."""
        stack: list[tuple[Node, bool]] = [(scope.top, False)]
        while stack:
            node, entered = stack.pop()
            if self.cancelled():
                self.blocked.add(scope.top)
                return
            if not node.is_dir or node.is_link:
                self._remove(node, scope, folder=False)
            elif entered:
                self._leave(node, scope)
            else:
                reason = _check(node, scope, folder=True)
                if reason is not None:
                    self._refuse(node, reason, scope)
                    continue
                give_way()
                stack.append((node, True))
                stack.extend((child, False) for child in node.children)

    def _leave(self, folder: Node, scope: _Scope) -> None:
        """Remove a folder whose recorded contents are gone, unless something stayed or arrived."""
        if folder in self.blocked:
            self._block_parent(folder, scope)
            return
        try:
            with os.scandir(folder.path) as entries:
                arrivals = sorted(entry.name for entry in entries)
        except OSError:
            self._refuse(folder, "unreadable", scope)
            return
        if arrivals:  # every recorded entry was removed, so whatever is left came later
            self.result.refused.extend((os.path.join(folder.path, name), "arrived") for name in arrivals)
            self.blocked.add(folder)
            self._block_parent(folder, scope)
            return
        self._remove(folder, scope, folder=True)

    def _remove(self, node: Node, scope: _Scope, *, folder: bool) -> None:
        reason = _check(node, scope, folder=folder)
        if reason is None and node is scope.top:  # a folder walk takes time: recheck its place too
            reason = check_place(node, scope.root, places=scope.places, approved=scope.approval)
        if reason is not None:
            self._refuse(node, reason, scope)
            return
        try:
            remove_entry(node.path, node.snapshot, node.parent.snapshot, directory=folder)
        except EntryChangedError:
            self._refuse(node, "identity", scope)
            return
        except OSError as error:
            self._fail(node, str(error) or type(error).__name__, scope)
            return
        if not _gone(node):
            self._fail(node, PENDING, scope)
            return
        self.result.removed_entries += 1
        if not node.is_dir and not node.is_link:
            self.result.removed_bytes += node.size
        if node is scope.top:
            self.result.removed.append(node)
        self._report_progress()

    def _refuse(self, node: Node, reason: str, scope: _Scope) -> None:
        self.result.refused.append((node.path, reason))
        self._block_parent(node, scope)

    def _fail(self, node: Node, detail: str, scope: _Scope) -> None:
        self.result.failed.append((node.path, detail))
        self._block_parent(node, scope)

    def _block_parent(self, node: Node, scope: _Scope) -> None:
        if node is not scope.top and node.parent is not None:
            self.blocked.add(node.parent)

    def _report_progress(self) -> None:
        now = time.monotonic()
        if self.progress is not None and now - self.reported >= _PROGRESS_SECONDS:
            self.reported = now
            self.progress(self.result.removed_entries)


def _scope(node: Node, root: Node, places: Sequence[Protection], approval: Protection | None) -> _Scope | str:
    """Where an approved entry stands now, or why it is refused before anything is removed."""
    reason = check_place(node, root, places=places, approved=approval)
    if reason is not None:
        return reason
    if node.snapshot is None or node.parent is None or node.parent.snapshot is None:
        return "unverified"
    device = unpack_snapshot(node.snapshot).device
    if node.is_dir and not node.is_link and device != unpack_snapshot(node.parent.snapshot).device:
        return "mount_point"
    try:
        base = os.path.realpath(os.path.dirname(node.path), strict=True)
    except (OSError, ValueError):
        return "missing"
    return _Scope(node, root, places, approval, base, device)


def _check(node: Node, scope: _Scope, *, folder: bool) -> str | None:
    """Why ``node`` must not be removed now, or None; folders compare identity and kind only.

    A folder's own times and size change as its contents go; its contents are checked one by one.
    """
    if system_file(node.path) is not None:
        return "system_managed"
    found = protection_of(node.path, scope.places)
    if node is not scope.top and found is not None and found != scope.approval:
        return "protected"  # a protected place inside the approved folder that the user was not asked about
    if folder and node.error is not None:
        return "incomplete"  # the scan could not read all of it, so its record is not complete
    if node.snapshot is None or node.parent is None or node.parent.snapshot is None:
        return "unverified"
    current = _observe(node.path)
    if isinstance(current, str):
        return current
    return _difference(unpack_snapshot(node.snapshot), current, node, folder) or _placement(node, current, scope)


def _observe(path: str) -> Snapshot | str:
    try:
        return unpack_snapshot(stat_snapshot(path))
    except FileNotFoundError:
        return "missing"
    except OSError:
        return "unreadable"


def _difference(before: Snapshot, current: Snapshot, node: Node, folder: bool) -> str | None:
    if current.is_link != before.is_link or current.is_link != node.is_link:
        return "link"
    if current.mode != before.mode:
        return "kind"
    if not before.inode or not current.inode:
        return "unverified"
    if current.identity != before.identity:
        return "identity"
    if not folder and (current.size, current.modified_ns, current.changed_ns, current.attributes, current.links) != (
            before.size, before.modified_ns, before.changed_ns, before.attributes, before.links):
        return "changed"
    return None


def _placement(node: Node, current: Snapshot, scope: _Scope) -> str | None:
    if current.device != scope.device:
        return "other_volume"
    if os.name == "nt" and current.attributes & _READ_ONLY:
        return "read_only"
    if node.is_link and _volume_mount(node.path):
        return "mount_point"
    return _contained(node, scope)


def _volume_mount(path: str) -> bool:
    """Whether a Windows link is a volume mount folder (removing it would detach a volume there)."""
    if os.name != "nt":
        return False
    try:
        target = os.readlink(path)
    except (OSError, ValueError):
        return True  # an unknown kind of link is never removed
    return "volume{" in target.lower()


def _contained(node: Node, scope: _Scope) -> str | None:
    """Require the entry's folder to resolve, without any link, to the folder the scan recorded."""
    names = [node.name]
    entry = node
    while entry is not scope.top:
        entry = entry.parent
        if entry is None:
            return "outside"
        names.append(entry.name)
    names.reverse()  # the approved entry's name first, ``node``'s own name last
    if not all(_plain(name) for name in names):
        return "outside"
    try:
        actual = os.path.realpath(os.path.dirname(node.path), strict=True)
    except (OSError, ValueError):
        return "missing"
    expected = os.path.join(scope.base, *names[:-1])
    return None if os.path.normcase(actual) == os.path.normcase(expected) else "outside"


def _plain(name: str) -> bool:
    """One ordinary path component: no separator, no ``.`` or ``..``, nothing empty."""
    separators = (os.sep, os.altsep or os.sep, "\0")
    return bool(name) and name not in (".", "..") and not any(mark in name for mark in separators)


def _gone(node: Node) -> bool:
    """Whether the recorded entry is no longer at its path (a newcomer with the same name is not it)."""
    try:
        info = os.lstat(node.path)
    except FileNotFoundError:
        return True
    except OSError:
        return False  # Windows denies access to an entry whose deletion is still pending
    return (info.st_dev, info.st_ino) != unpack_snapshot(node.snapshot).identity


def _remove_posix(path: str, expected: bytes, parent: bytes, *, directory: bool) -> None:
    """Remove a name relative to its folder, opened without following a link; both identities checked."""
    folder = os.open(os.path.dirname(path), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        name = os.path.basename(path)
        anchor = os.fstat(folder)
        current = os.stat(name, dir_fd=folder, follow_symlinks=False)
        if ((anchor.st_dev, anchor.st_ino) != unpack_snapshot(parent).identity
                or (current.st_dev, current.st_ino) != unpack_snapshot(expected).identity):
            raise EntryChangedError(path)
        if directory:
            os.rmdir(name, dir_fd=folder)
        else:
            os.unlink(name, dir_fd=folder)
    finally:
        os.close(folder)


def _kernel32() -> ctypes.WinDLL:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
                                  ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    kernel.CreateFileW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes, kernel.CloseHandle.restype = [ctypes.c_void_p], ctypes.c_int
    kernel.SetFileInformationByHandle.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.c_void_p, ctypes.c_uint32]
    kernel.SetFileInformationByHandle.restype = ctypes.c_int32
    return kernel


def _remove_windows(path: str, expected: bytes) -> None:
    """Open the entry itself, compare the open object's identity, then mark exactly it for deletion."""
    kernel = _kernel32()
    handle = kernel.CreateFileW(path, _DELETE_ACCESS | _READ_ATTRIBUTES, _SHARE_ALL, None, _OPEN_EXISTING,
                                _OPEN_ENTRY_ITSELF, None)
    if handle is None or handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY)
    except OSError:
        kernel.CloseHandle(handle)
        raise
    try:  # the descriptor owns the handle from here on and closes it, which completes the deletion
        info = os.fstat(descriptor)
        if (info.st_dev, info.st_ino) != unpack_snapshot(expected).identity:
            raise EntryChangedError(path)
        _mark_for_deletion(kernel, handle)
    finally:
        os.close(descriptor)


def _mark_for_deletion(kernel: ctypes.WinDLL, handle: int) -> None:
    """POSIX-style disposition where the system has it (the name goes at once), else the classic one."""
    flags = ctypes.c_uint32(_DELETE_POSIX)
    if kernel.SetFileInformationByHandle(handle, _DISPOSITION_EX, ctypes.byref(flags), ctypes.sizeof(flags)):
        return
    error = ctypes.get_last_error()
    if error not in _EX_UNSUPPORTED:
        raise ctypes.WinError(error)
    flag = ctypes.c_ubyte(1)  # FILE_DISPOSITION_INFO holds one BOOLEAN
    if not kernel.SetFileInformationByHandle(handle, _DISPOSITION, ctypes.byref(flag), ctypes.sizeof(flag)):
        raise ctypes.WinError(ctypes.get_last_error())
