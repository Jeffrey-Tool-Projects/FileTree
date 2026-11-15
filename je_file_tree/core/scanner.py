"""Read a folder tree into ``Node`` objects.

Several worker threads read folders at the same time: listing a folder spends
most of its time waiting on the file system with the interpreter lock
released, so on a disk with many folders the waits overlap. The walk never
follows links (symlinks and Windows junctions are recorded with size 0, so a
link loop cannot make a scan run forever), and it keeps going past folders it
cannot read: those get ``Node.error`` and an entry in ``ScanResult.errors``.

The tree can be shown while it is being read (``on_root`` hands out the root
first): whenever a folder has been listed, its files are added to the totals
of every folder above it, so sizes grow as the scan goes. Children are only
ever appended during the scan; once every folder is read, the totals are
added up again bottom-up and each folder's children sorted largest first.
"""

from __future__ import annotations

import errno
import os
import stat
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import cast

from je_file_tree.core import mft_scan, native_scan
from je_file_tree.core.allocation import Allocation, OrdinaryAllocation, allocation_for, ordinary_allocation
from je_file_tree.core.cpu_load import WorkerGovernor
from je_file_tree.core.exclusions import Excluded, exclusion_test
from je_file_tree.core.node import Node
from je_file_tree.core.hard_links import HardLinkAccounting, account_hard_links
from je_file_tree.core.owner_id import file_owner
from je_file_tree.core.mounts import MOUNT_BOUNDARY, MountChangedError, MountSurvey, boundary_path, mount_points
from je_file_tree.core.pacing import give_way
from je_file_tree.core.priority import background_priority
from je_file_tree.core.snapshot import link_identity, pack_snapshot, path_metadata, stat_snapshot, unpack_snapshot

# Windows reparse tags of links that must not be followed. A junction (and a
# volume mounted into a folder) is a mount point; ``is_symlink()`` is False for
# it, and ``is_dir(follow_symlinks=False)`` is True, so only the tag tells.
_IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003
_IO_REPARSE_TAG_SYMLINK = 0xA000000C
_LINK_REPARSE_TAGS = frozenset({_IO_REPARSE_TAG_MOUNT_POINT, _IO_REPARSE_TAG_SYMLINK})
_FILE_ATTRIBUTE_HIDDEN = 0x2

# Measured on an SSD (warm cache): 1 thread 1.27 s, 2 0.88 s, 4 0.67 s, 8 0.72 s for
# 62k files; past four the threads mostly wait for the interpreter lock.
DEFAULT_WORKERS = min(4, os.cpu_count() or 1)


_PAUSE_STEP = 0.05  # s between two looks at ``pause`` while a table walk is paused

# The common reasons are worded here instead of taken from the OS, whose text
# is in the system's language (a Chinese Windows answers 存取被拒。 in an
# English window); the GUI translates these, exports keep them as they are.
ACCESS_DENIED = "access denied"
NOT_FOUND = "not found"
PATH_TOO_LONG = "path too long"
_REASON_BY_ERRNO = {errno.EACCES: ACCESS_DENIED, errno.EPERM: ACCESS_DENIED, errno.ENOENT: NOT_FOUND,
                    errno.ENAMETOOLONG: PATH_TOO_LONG}
_WINDOWS_PATH_TOO_LONG = 206  # ERROR_FILENAME_EXCED_RANGE

# ``Node.error`` of a folder the scan never got to because it was stopped.
NOT_SCANNED = "not scanned: the scan was stopped first"
EXCLUDED = "excluded: skipped by the exclusions"
HIDDEN_OMITTED = "excluded: hidden entries omitted"
PARTIAL_FOLDER = "incomplete: some entries could not be read"


class ScanCancelledError(Exception):
    """Raised by ``scan`` when its ``cancel`` event is set.

    ``partial`` is what was read before the stop, added up and sorted like a
    finished scan; folders never read have ``error == NOT_SCANNED`` (when the
    stop came before anything was read, that is the root itself).
    """

    def __init__(self, partial: ScanResult | None = None) -> None:
        super().__init__("scan cancelled")
        self.partial = partial


@dataclass(frozen=True, slots=True)
class ScanOptions:
    """What a scan includes and how many folders it reads at once.

    ``count_hard_links`` adds counted totals from recorded identities without changing named bytes.
    ``adaptive`` makes ``workers`` an upper limit: fewer folders are read at once while other
    programs are using the processors (see ``core/cpu_load.py``).
    """

    include_hidden: bool = True
    workers: int = DEFAULT_WORKERS
    exclude: tuple[str, ...] = ()  # folder name patterns and folder paths to skip (see core/exclusions.py)
    gentle: bool = False
    file_times: bool = False
    windows_owners: bool = False
    exact_windows_allocation: bool = False
    count_hard_links: bool = False
    # How a scan is paced, not what it includes: presets, templates and restart hand-offs do not carry
    # it, so it takes no part in comparing two sets of choices.
    adaptive: bool = field(default=False, compare=False)
    # Read a whole NTFS drive from its master file table where that is possible (``core/mft_scan.py``);
    # like ``adaptive`` it is this machine's own choice and takes no part in comparisons.
    mft: bool = field(default=False, compare=False)


@dataclass(frozen=True, slots=True)
class ScanProgress:
    """A snapshot of a running scan, for progress displays."""

    files: int
    folders: int
    size: int
    current: str


@dataclass(slots=True)
class ScanResult:
    """A finished tree, coverage and duration."""

    root: Node
    errors: list[tuple[str, str]] = field(default_factory=list)
    elapsed: float = 0.0
    warnings: list[str] = field(default_factory=list)
    hard_links: HardLinkAccounting | None = None


ProgressCallback = Callable[[ScanProgress], None]
RootCallback = Callable[[Node], None]


@dataclass(slots=True)
class _FolderRead:
    """What reading one folder found."""

    subfolders: list[tuple[Node, str]] = field(default_factory=list)
    files: int = 0
    size: int = 0
    allocated: int = 0
    errors: list[tuple[str, str]] = field(default_factory=list)


def scan(path: str | os.PathLike[str], *, options: ScanOptions | None = None,  # noqa: PLR0913
         progress: ProgressCallback | None = None, cancel: threading.Event | None = None,
         progress_interval: float = 0.1, on_root: RootCallback | None = None,
         pause: threading.Event | None = None) -> ScanResult:
    """Scan the folder at ``path`` and return its tree.

    ``on_root`` is called once with the (still empty) root before any folder is
    read, for showing the tree while it grows. ``progress`` is called about
    every ``progress_interval`` seconds (and once at the end). Both run on the
    calling thread. Setting ``cancel`` stops the scan within one interval.
    While ``pause`` is set, workers take no new folders; in-flight folder reads finish.
    Clearing it resumes within 0.1 seconds. Cancellation works while paused.
    Windows native directory entries use ordinary no-follow path stat even with a cached file ID,
    so full snapshot attributes do not depend on the enumeration API. Audited adapters retain their
    already verified metadata; other platforms keep cached stat with missing-identity fallback.

    :raises NotADirectoryError: when ``path`` is not an existing folder
    :raises ScanCancelledError: when ``cancel`` is set; ``partial`` holds what was read
    :raises OSError: when Linux mount boundaries are unknown or change during scanning
    """
    root_path = os.path.abspath(os.fspath(path))
    if not os.path.isdir(root_path):
        raise NotADirectoryError(root_path)
    options = options or ScanOptions()
    started = time.monotonic()
    root = Node(name=root_path, is_dir=True, children=[], error=NOT_SCANNED)
    root.snapshot = stat_snapshot(root_path)
    if unpack_snapshot(root.snapshot).is_link:
        raise NotADirectoryError("scan roots must not be links or junctions")
    if on_root is not None:
        on_root(root)
    crawler = _Crawler(root, root_path, options, cancel, pause)
    try:
        crawler.run(progress, cancel, progress_interval)
    except ScanCancelledError:
        for folder, _ in crawler.unread():
            folder.error = NOT_SCANNED
        _add_up(crawler.folders)
        accounting = account_hard_links(root) if options.count_hard_links else None
        raise ScanCancelledError(ScanResult(root, crawler.errors, time.monotonic() - started,
                                            sorted(set(crawler.warnings)), accounting)) from None
    _add_up(crawler.folders)
    accounting = account_hard_links(root, cancel=cancel) if options.count_hard_links else None
    if cancel is not None and cancel.is_set():
        raise ScanCancelledError(ScanResult(root, crawler.errors, time.monotonic() - started,
                                            sorted(set(crawler.warnings)), accounting))
    if progress is not None:
        progress(crawler.snapshot())
    crawler.verify_mounts()
    return ScanResult(root=root, errors=crawler.errors, elapsed=time.monotonic() - started,
                      warnings=sorted(set(crawler.warnings)), hard_links=accounting)


class _Crawler:
    """Worker threads sharing one stack of folders still to read."""

    def __init__(self, root: Node, root_path: str, options: ScanOptions,
                 cancel: threading.Event | None = None, pause: threading.Event | None = None) -> None:
        self._options = options
        self._mounts = MountSurvey(root_path, cast(bytes, root.snapshot), mount_points())
        self._allocation = (allocation_for(root_path, exact_windows=True) if options.exact_windows_allocation
                            else allocation_for(root_path))
        self._excluded = exclusion_test(options.exclude)
        self._native = _native_reader(options, self._allocation, self._mounts, root_path)
        self._table = _table_for(options, self._allocation, self._mounts, root_path)
        self._cancel = cancel
        self._pause = pause
        self._pending: list[tuple[Node, str]] = [(root, root_path)]
        self._busy = 0
        self._threads = max(1, options.workers)
        self._governor = WorkerGovernor(options.workers) if options.adaptive and self._table is None else None
        self._limit = self._threads if self._governor is None else self._governor.limit
        self._stopped = False
        self._failure: BaseException | None = None
        self._condition = threading.Condition()
        self._done = threading.Event()
        self._current = root_path
        self.folders: list[Node] = [root]  # every folder after its parent
        self.errors: list[tuple[str, str]] = []
        self.warnings: list[str] = []
        self.files = 0
        self.size = 0

    @property
    def options(self) -> ScanOptions:
        """What this scan includes."""
        return self._options

    @property
    def allocation(self) -> Allocation:
        """The rule for the space a file takes."""
        return self._allocation

    @property
    def excluded(self) -> Excluded | None:
        """The exclusion test, or None without exclusions."""
        return self._excluded

    def took(self, folder: Node, path: str, read: _FolderRead) -> None:
        """Count what reading ``folder`` found, like ``_finish`` without a queue to feed."""
        with self._condition:
            self.folders.extend(node for node, _ in read.subfolders)
            self.files += read.files
            self.size += read.size
            self.errors.extend(read.errors)
            self._current = path
            _add_to_ancestors(folder, read)

    def verify_mounts(self) -> None:
        """Recheck scope after workers and final aggregation, before publishing a complete scan."""
        self._mounts.verify(mount_points())

    def unread(self) -> list[tuple[Node, str]]:
        """The folders still waiting to be read (after ``run`` has returned or raised)."""
        with self._condition:
            return list(self._pending)

    def snapshot(self) -> ScanProgress:
        """The counts so far."""
        with self._condition:
            return ScanProgress(self.files, len(self.folders) - 1, self.size, self._current)

    def run(self, progress: ProgressCallback | None, cancel: threading.Event | None,
            interval: float) -> None:
        """Read every folder, reporting progress and watching ``cancel`` from this thread.

        The workers watch ``cancel`` too and take no new folder once it is set,
        so a stop is immediate instead of up to one ``interval`` late; the
        folders already being read finish.
        """
        if cancel is not None and cancel.is_set():
            raise ScanCancelledError
        if self._table is not None:
            self._walk_table(progress, cancel, interval)
            return
        threads = [threading.Thread(target=self._work, name=f"file-tree-scan-{number}", daemon=True)
                   for number in range(self._threads)]
        started: list[threading.Thread] = []
        try:
            for thread in threads:
                thread.start()
                started.append(thread)
            while not self._done.wait(interval):
                if cancel is not None and cancel.is_set():
                    break
                if self._governor is not None:
                    self._allow(self._governor.update())
                if progress is not None:
                    progress(self.snapshot())
        except BaseException as error:  # noqa: BLE001 - stop and join owned threads, then re-raise the first failure
            self._fail(error)
        finally:
            self._stop()
            for thread in started:
                thread.join()
        if self._failure is not None:
            raise self._failure
        if cancel is not None and cancel.is_set():
            raise ScanCancelledError

    def _walk_table(self, progress: ProgressCallback | None, cancel: threading.Event | None,
                    interval: float) -> None:
        """Build the tree from the file table on this thread: nothing is waited for, so threads would only
        take turns at the interpreter lock."""
        walk = _TableWalk(self, self._table)
        try:
            with background_priority(self._options.gentle) as warnings:
                walk.run(progress, cancel, self._pause, interval)
        finally:
            self._pending = walk.unread()
        self.warnings.extend(warnings)
        if cancel is not None and cancel.is_set():
            raise ScanCancelledError

    def _allow(self, limit: int) -> None:
        """Let at most ``limit`` threads read folders from now on; reads under way finish."""
        with self._condition:
            if limit != self._limit:
                self._limit = max(1, limit)
                self._condition.notify_all()

    def _stop(self) -> None:
        with self._condition:
            self._stopped = True
            self._condition.notify_all()
        self._done.set()

    def _work(self) -> None:
        try:
            with background_priority(self._options.gentle) as warnings:
                self._read_all()
            with self._condition:
                self.warnings.extend(warnings)
        except BaseException as error:  # noqa: BLE001 - re-raised on the calling thread after joining
            self._fail(error)

    def _fail(self, error: BaseException) -> None:
        with self._condition:
            if self._failure is None:
                self._failure = error
            self._stop()

    def _read_all(self) -> None:
        while (task := self._take()) is not None:
            try:
                give_way()
                # The native reader is an extra argument only when it is in use: the six-argument call
                # is what tests and callers of the Python reader replace.
                extra = () if self._native is None else (self._native,)
                read = _read_folder(task[0], task[1], self._options, self._allocation, self._excluded, self._mounts,
                                    *extra)
                self._finish(task[0], task[1], read)
            except BaseException as error:  # noqa: BLE001 - handed to the calling thread, which re-raises it
                self._fail(error)
                return
            finally:
                with self._condition:
                    self._busy -= 1
                    self._condition.notify_all()

    def _take(self) -> tuple[Node, str] | None:
        """The next folder to read, or None once there is nothing left anywhere."""
        with self._condition:
            while not self._stopped and not (self._cancel is not None and self._cancel.is_set()):
                if not self._pending and not self._busy:
                    break
                if ((self._pause is None or not self._pause.is_set()) and self._pending
                        and self._busy < self._limit):
                    break
                self._condition.wait(0.1)
            cancelled = self._cancel is not None and self._cancel.is_set()
            if self._stopped or cancelled or not self._pending:
                self._condition.notify_all()
                self._done.set()
                return None
            self._busy += 1
            return self._pending.pop()

    def _finish(self, folder: Node, path: str, read: _FolderRead) -> None:
        with self._condition:
            self._pending.extend(read.subfolders)
            self.folders.extend(node for node, _ in read.subfolders)
            self.files += read.files
            self.size += read.size
            self.errors.extend(read.errors)
            self._current = path
            _add_to_ancestors(folder, read)


def _add_to_ancestors(folder: Node, read: _FolderRead) -> None:
    """Count what reading ``folder`` found into it and every folder above it (running totals)."""
    subfolders = len(read.subfolders)
    node: Node | None = folder
    while node is not None:
        node.size += read.size
        node.allocated += read.allocated
        node.file_count += read.files
        node.dir_count += subfolders
        node = node.parent


def _read_folder(folder: Node, path: str, options: ScanOptions, allocation: Allocation,  # noqa: PLR0913
                 excluded: Excluded | None = None,
                 boundaries: frozenset[str] | MountSurvey = frozenset(),
                 native: _NativeRead | None = None) -> _FolderRead:
    """Add ``folder``'s entries as its children and report what was found."""
    read = _FolderRead()
    try:
        if native is not None:
            _read_native(folder, path, native, _Reading(options, allocation, excluded, boundaries, read))
        else:
            listing_context = (boundaries.listing(path, folder.snapshot) if isinstance(boundaries, MountSurvey)
                               else _path_listing(path))
            with listing_context as entries:
                listing = list(entries)
                _record_entries(folder, listing, options, allocation, excluded, boundaries, read)
    except MountChangedError:
        raise
    except OSError as error:
        folder.error = _describe(error)
        read.errors.append((path, folder.error))
        return read
    if read.errors:
        folder.error = HIDDEN_OMITTED if all(reason == HIDDEN_OMITTED for _, reason in read.errors) else PARTIAL_FOLDER
    else:
        folder.error = None
    return read


@contextmanager
def _path_listing(path: str) -> Iterator[Iterator[os.DirEntry[str]]]:
    with os.scandir(path) as entries:
        yield entries


def _record_entries(folder: Node, listing: list[os.DirEntry[str]], options: ScanOptions, allocation: Allocation,
                    excluded: Excluded | None, boundaries: frozenset[str] | MountSurvey, read: _FolderRead) -> None:
    children = cast(list[Node], folder.children)  # folders are always created with a list
    for entry in listing:
        child = _entry_node(entry, options, read, allocation, excluded)
        if child is not None:
            _adopt(folder, child, entry.path, boundaries, read)
            children.append(child)


def _adopt(folder: Node, child: Node, path: str, boundaries: frozenset[str] | MountSurvey,
           read: _FolderRead) -> None:
    """Give ``child`` its place under ``folder``: mount boundaries are listed and never entered."""
    # Asked once per folder found: without mount points there is nothing to normalise a path for.
    # Measured 2026-11-15 for 126,000 folders, with ``_other_volume`` reading only the device: these
    # two checks took 0.74 s before and 0.17 s now.
    points = boundaries.points if isinstance(boundaries, MountSurvey) else boundaries
    if points and child.is_dir and not child.is_link and boundary_path(path) in points:
        child.is_link = True
        child.error = MOUNT_BOUNDARY
        read.errors.append((path, MOUNT_BOUNDARY))
    elif _other_volume(folder, child):
        child.is_link = True  # a mount boundary is listed, never traversed
        child.error = None
    child.parent = folder
    if child.is_dir and not child.is_link and child.error == NOT_SCANNED:
        read.subfolders.append((child, path))


@dataclass(frozen=True, slots=True)
class _NativeRead:
    """The calibrated native reader and the allocation rule for files without unusual attributes."""

    read: native_scan.Reader
    ordinary: OrdinaryAllocation


@dataclass(frozen=True, slots=True)
class _Reading:
    """What reading one folder needs besides the folder itself."""

    options: ScanOptions
    allocation: Allocation
    excluded: Excluded | None
    boundaries: frozenset[str] | MountSurvey
    read: _FolderRead


class _NamedEntry:
    """A listed name for the ``os.lstat`` code: the entries the native reader leaves to Python."""

    __slots__ = ("name", "path", "_listed")

    def __init__(self, name: str, path: str, listed_attributes: int) -> None:
        self.name, self.path, self._listed = name, path, listed_attributes

    def stat(self, *, follow_symlinks: bool = True) -> os.stat_result:
        """The entry's metadata, of the entry itself unless ``follow_symlinks``."""
        return os.stat(self.path) if follow_symlinks else path_metadata(os.lstat(self.path), self._listed)

    def is_dir(self, *, follow_symlinks: bool = True) -> bool:
        """Whether it is a folder (or, following links, leads to one)."""
        return stat.S_ISDIR(self.stat(follow_symlinks=follow_symlinks).st_mode)


def _native_reader(options: ScanOptions, allocation: Allocation,
                   boundaries: MountSurvey, root_path: str) -> _NativeRead | None:
    """The native reader when this scan's choices leave every entry to the ordinary rules.

    It was checked against ``os.lstat`` on this interpreter's own files; the scan's first folder is
    compared too, because another volume or file system may identify its files differently.
    """
    if options.windows_owners or options.exact_windows_allocation or not boundaries.plain_listing:
        return None  # per-file owner and exact allocation queries need the full Python path
    ordinary = ordinary_allocation(allocation)
    read = native_scan.reader() if ordinary is not None else None
    if read is None or ordinary is None or not native_scan.agrees_on(root_path):
        return None
    return _NativeRead(read, ordinary)


@dataclass(frozen=True, slots=True)
class _TableRead:
    """A file table and the allocation rule for files without unusual attributes."""

    table: mft_scan.Table
    ordinary: OrdinaryAllocation


def _table_for(options: ScanOptions, allocation: Allocation, boundaries: MountSurvey,
               root_path: str) -> _TableRead | None:
    """The file table to build this scan from, or None to list folders (``core/mft_scan.py``).

    Asked for under the conditions of the native reader, and only without mount points to mark.
    """
    ordinary = ordinary_allocation(allocation)
    if (not options.mft or options.windows_owners or options.exact_windows_allocation or ordinary is None
            or not boundaries.plain_listing or boundaries.points):
        return None
    table = mft_scan.open_table(root_path)
    return None if table is None else _TableRead(table, ordinary)


class _TableWalk:
    """Build a scan's tree from a file table, on the calling thread.

    The crawler's workers, lock and queue exist to overlap waits on the file system; rows that are
    already in memory need none of that. What a folder's rows become is what ``_read_native`` makes of
    them: the same nodes, errors, hidden and excluded entries, and running totals while the tree is
    shown. Measurements are in ``docs/updates`` U-20261115-09.
    """

    def __init__(self, crawler: _Crawler, source: _TableRead) -> None:
        self._crawler, self._table, self._ordinary = crawler, source.table, source.ordinary
        root, root_path = crawler.unread()[0]
        self._stack: list[tuple[Node, str, int]] = [(root, root_path, source.table.root)]

    def unread(self) -> list[tuple[Node, str]]:
        """The folders not read yet."""
        return [(folder, path) for folder, path, _reference in self._stack]

    def run(self, progress: ProgressCallback | None, cancel: threading.Event | None,
            pause: threading.Event | None, interval: float) -> None:
        """Read every folder of the stack; stop at once when ``cancel`` is set, wait while ``pause`` is."""
        stack, crawler = self._stack, self._crawler
        report = time.monotonic() + interval
        while stack and not (cancel is not None and cancel.is_set()):
            if pause is not None and pause.is_set():
                time.sleep(_PAUSE_STEP)
                continue
            give_way()
            self._read(*stack.pop())
            if progress is not None and time.monotonic() >= report:
                progress(crawler.snapshot())
                report = time.monotonic() + interval

    def _read(self, folder: Node, path: str, reference: int) -> None:
        crawler, read = self._crawler, _FolderRead()
        try:
            rows = self._table.rows(reference, crawler.options.file_times)
        except OSError as error:
            folder.error = _describe(error)
            crawler.errors.append((path, folder.error))
            return
        found = self._rows(folder, path if path.endswith(os.sep) else path + os.sep, rows, read)
        if read.errors:
            hidden = all(reason == HIDDEN_OMITTED for _, reason in read.errors)
            folder.error = HIDDEN_OMITTED if hidden else PARTIAL_FOLDER
        else:
            folder.error = None
        self._stack.extend(found)
        crawler.took(folder, path, read)

    def _rows(self, folder: Node, prefix: str, rows: list[native_scan.Row],
              read: _FolderRead) -> list[tuple[Node, str, int]]:
        """Add the rows of ``folder`` as its children; the folders among them that are to be read."""
        excluded, skip_hidden = self._crawler.excluded, not self._crawler.options.include_hidden
        unusual, cluster, shared = self._ordinary.unusual, self._ordinary.cluster, self._ordinary.shared
        shared_count, a_file, a_folder = len(shared), native_scan.KIND_FILE, native_scan.KIND_FOLDER
        append = cast(list[Node], folder.children).append
        found: list[tuple[Node, str, int]] = []
        files = size = allocated = 0
        # This loop runs once per entry of the volume; names are bound outside it for that reason.
        for name, kind, length, modified, snapshot, attributes in rows:
            plain = (kind == a_file and not attributes & unusual) or kind == a_folder
            if not plain:
                self._asked(folder, _NamedEntry(name, prefix + name, attributes), read, found)
            elif skip_hidden and (attributes & _FILE_ATTRIBUTE_HIDDEN or name.startswith(".")):
                read.errors.append((prefix + name, HIDDEN_OMITTED))
            elif kind == a_file:
                clusters = -(-length // cluster)
                space = shared[clusters] if clusters < shared_count else clusters * cluster
                files += 1
                size += length
                allocated += space
                append(Node(name, False, length, 1, 0, modified, False, None, space, (), folder, snapshot))
            else:
                skipped = excluded is not None and excluded(name, prefix + name)
                child = Node(name, True, 0, 0, 0, modified, False, EXCLUDED if skipped else NOT_SCANNED, 0, [],
                             folder, snapshot)
                append(child)
                if not skipped:
                    found.append((child, prefix + name, int.from_bytes(snapshot[8:16], "little")))
        read.files += files
        read.size += size
        read.allocated += allocated
        read.subfolders = [(child, child_path) for child, child_path, _reference in found]
        return found

    def _asked(self, folder: Node, entry: _NamedEntry, read: _FolderRead,
               found: list[tuple[Node, str, int]]) -> None:
        """An entry the table leaves to ``os.lstat``: a link, a cloud or packed file, an unusual record."""
        crawler = self._crawler
        child = _entry_node(cast("os.DirEntry[str]", entry), crawler.options, read, crawler.allocation,
                            crawler.excluded)
        if child is None:
            return
        child.parent = folder
        cast(list[Node], folder.children).append(child)
        if child.is_dir and not child.is_link and child.error == NOT_SCANNED:
            try:  # the system now calls it a plain folder: read it from the table by what it is now
                found.append((child, entry.path, mft_scan.folder_reference(entry.path)))
            except OSError as error:
                child.error = _describe(error)
                read.errors.append((entry.path, child.error))


def _read_native(folder: Node, path: str, native: _NativeRead, reading: _Reading) -> None:
    """``_record_entries`` from one native listing: the same nodes, without an ``os.lstat`` per entry.

    Measured 2026-11-14 on 80,000 small files (warm cache, 8 logical processors, median of three):
    Python reader 2.70 / 2.09 / 2.70 / 3.05 s with 1 / 2 / 4 / 8 threads, native 1.97 / 1.16 / 0.93 / 0.81 s.
    Plain files and folders come packed from the native module, whose snapshot bytes equal
    ``pack_snapshot(os.lstat(path))`` (checked by ``native_scan`` before use). Links, files with
    sparse/compressed/cloud attributes and anything the module could not read go through
    ``_entry_node`` exactly as before.
    """
    options, read = reading.options, reading.read
    rounded, unusual = native.ordinary.rounded, native.ordinary.unusual
    hidden = 0 if options.include_hidden else _FILE_ATTRIBUTE_HIDDEN
    children = cast(list[Node], folder.children)  # folders are always created with a list
    files = size = allocated = 0
    for name, kind, length, modified, snapshot, attributes in native.read(path, options.file_times):
        if kind == native_scan.KIND_FILE and not attributes & unusual:
            if not options.include_hidden and (attributes & hidden or name.startswith(".")):
                read.errors.append((os.path.join(path, name), HIDDEN_OMITTED))
                continue
            space = rounded(length)
            files += 1
            size += length
            allocated += space
            children.append(Node(name, False, length, 1, 0, modified, False, None, space, (), folder, snapshot))
            continue
        child_path = os.path.join(path, name)
        if kind == native_scan.KIND_FOLDER:
            if not options.include_hidden and (attributes & hidden or name.startswith(".")):
                read.errors.append((child_path, HIDDEN_OMITTED))
                continue
            skipped = reading.excluded is not None and reading.excluded(name, child_path)
            child: Node | None = Node(name, True, modified=modified, error=EXCLUDED if skipped else NOT_SCANNED,
                                      children=[], snapshot=snapshot)
        else:
            child = _entry_node(cast("os.DirEntry[str]", _NamedEntry(name, child_path, attributes)), options, read,
                                reading.allocation, reading.excluded)
        if child is not None:
            _adopt(folder, child, child_path, reading.boundaries, read)
            children.append(child)
    read.files += files
    read.size += size
    read.allocated += allocated


def _other_volume(folder: Node, child: Node) -> bool:
    """Different-device directory mounts must not bring another volume into this scan."""
    return bool(child.is_dir and folder.snapshot is not None and child.snapshot is not None
                and link_identity(folder.snapshot)[0] != link_identity(child.snapshot)[0])


def _entry_node(entry: os.DirEntry[str], options: ScanOptions, read: _FolderRead,
                allocation: Allocation, excluded: Excluded | None = None) -> Node | None:
    """The node for one directory entry, or None when it is skipped or unreadable."""
    try:
        info = entry.stat(follow_symlinks=False)
        if not info.st_ino or (os.name == "nt" and isinstance(entry, os.DirEntry)):
            # Windows cached enumeration can omit native attributes even with a valid file ID.
            # Audited adapters already supply checked no-follow metadata; retain that exact result.
            info = path_metadata(os.lstat(entry.path), getattr(info, "st_file_attributes", 0))
    except FileNotFoundError:
        return None  # removed while we were scanning
    except OSError as error:
        read.errors.append((entry.path, _describe(error)))
        return None
    if not options.include_hidden and _is_hidden(entry.name, info):
        read.errors.append((entry.path, HIDDEN_OMITTED))
        return None
    snapshot = pack_snapshot(info, file_times=True) if options.file_times else pack_snapshot(info)
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_reparse_tag", 0) in _LINK_REPARSE_TAGS:
        return Node(name=entry.name, is_dir=_points_to_folder(entry), modified=info.st_mtime,
                    is_link=True, snapshot=snapshot)
    if stat.S_ISDIR(info.st_mode):
        node = _folder_node(entry, info.st_mtime, excluded)
        node.snapshot = snapshot
        return node
    allocated = allocation(entry, info)
    read.files += 1
    read.size += info.st_size
    read.allocated += allocated
    return Node(name=entry.name, is_dir=False, size=info.st_size, allocated=allocated, file_count=1,
                modified=info.st_mtime, snapshot=snapshot,
                owner=file_owner(entry.path, info, windows=options.windows_owners))


def _folder_node(entry: os.DirEntry[str], modified: float, excluded: Excluded | None) -> Node:
    """A folder to read, or, when the exclusions match it, one that is listed but never read."""
    skipped = excluded is not None and excluded(entry.name, entry.path)
    return Node(name=entry.name, is_dir=True, modified=modified,
                error=EXCLUDED if skipped else NOT_SCANNED, children=[])


def _is_hidden(name: str, info: os.stat_result) -> bool:
    return name.startswith(".") or bool(getattr(info, "st_file_attributes", 0) & _FILE_ATTRIBUTE_HIDDEN)


def _points_to_folder(entry: os.DirEntry[str]) -> bool:
    """Whether a link's target is a folder (False when the target is missing or unreadable)."""
    try:
        return entry.is_dir(follow_symlinks=True)
    except OSError:
        return False


def _describe(error: OSError) -> str:
    """One of the worded reasons above, or the system's own text for anything else."""
    if getattr(error, "winerror", None) == _WINDOWS_PATH_TOO_LONG:
        return PATH_TOO_LONG
    return _REASON_BY_ERRNO.get(error.errno) or error.strerror or type(error).__name__


def _size_first(node: Node) -> tuple[int, str]:
    return -node.size, node.name.lower()


def _add_up(folders: list[Node]) -> None:
    """Fill in folder totals, deepest folders first, and sort each folder's children largest first.

    ``folders`` must list every folder after its parent.
    """
    for folder in reversed(folders):
        give_way()
        size = allocated = files = subfolders = 0
        newest = folder.modified
        children = folder.children
        for child in children:
            size += child.size
            allocated += child.allocated
            files += child.file_count
            if child.is_dir and not child.is_link and child.error != EXCLUDED:
                subfolders += 1 + child.dir_count
            newest = max(newest, child.modified)
        folder.size = size
        folder.allocated = allocated
        folder.file_count = files
        folder.dir_count = subfolders
        folder.modified = newest
        if isinstance(children, list) and len(children) > 1:
            children.sort(key=_size_first)
