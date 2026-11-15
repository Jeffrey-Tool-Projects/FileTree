"""Compare known file allocation with OS capacity, without filling unknown buckets with zero."""

from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass, field

from je_file_tree.core import native_tree
from je_file_tree.core.coverage import Coverage, coverage_of
from je_file_tree.core.node import Node
from je_file_tree.core.mounts import MOUNT_BOUNDARY
from je_file_tree.core.pacing import give_way
from je_file_tree.core.snapshot import NO_FILE_NUMBER, link_identity, stat_snapshot, unpack_snapshot


@dataclass(frozen=True, slots=True)
class CapacityLedger:
    """An estimated ledger, not a filesystem audit or a promise of recoverable space.

    Recycle Bin allocation seen is included in unique allocation. Unaccounted is only computed for a
    complete whole-volume scan with known identities and compatible OS totals. Metadata, omitted data
    and other mounted volumes have no measured byte total. Values refer to different instants; live
    filesystem changes, shared extents, snapshots and Windows cluster estimates affect the remainder.
    """

    total: int | None
    used: int | None
    free: int | None
    unavailable_free: int | None
    named_allocated: int
    unique_allocated: int | None
    hard_link_overcount: int | None
    recycle_bin_seen: int | None
    recycle_bin_complete: bool
    mounted_folders: int
    foreign_allocated_seen: int | None
    coverage: Coverage
    status: str
    unaccounted: int | None
    measured_at: float
    metadata_bytes: int | None = None
    omitted_bytes: int | None = None
    other_volumes_bytes: int | None = None


def capacity_ledger(root: Node, *, partial: bool = False) -> CapacityLedger:
    """Survey on a worker; report why a folder, interrupted or unreadable scan cannot reconcile a volume."""
    coverage = coverage_of(root)
    root_info = unpack_snapshot(root.snapshot) if root.snapshot is not None else None
    device = root_info.device if root_info is not None else None
    counts = _survey(root, device)
    total, used, free, unavailable = _usage(root.path)
    status = _status(root, coverage, counts.unknown or root_info is None, partial)
    if total is None and root.path is not None:
        status = "capacity_unavailable"
    elif status == "estimated" and used is not None and counts.unique > used:
        status = "allocation_exceeds_used"
    remainder = used - counts.unique if status == "estimated" and used is not None else None
    known = not counts.unknown and (root_info is not None or root.path is None)
    return CapacityLedger(total, used, free, unavailable, counts.named, counts.unique if known else None,
                          counts.named - counts.unique if known else None, counts.bin_seen if known else None,
                          counts.bin_found and counts.bin_complete, counts.mounts, counts.foreign if known else None,
                          coverage, status, remainder, time.time())


def _survey(root: Node, device: int | None) -> _Counts:
    """Walk the tree once: per folder here, per file in ``_Counts.add`` or in the native module.

    Measured 2026-11-15 on 1.1 million files / 325,000 folders: the ledger took 3.3 s with the files
    counted in Python and 1.7 s natively, with the same numbers (``docs/updates`` U-20261115-10).
    """
    counts = _Counts()
    started, add, finish = (native_tree.function(name) for name in ("capacity_new", "capacity_add", "capacity_finish"))
    totals = started() if started is not None and add is not None and finish is not None else None
    stack = [(root, _is_trash(root.path))]
    while stack:
        node, in_bin = stack.pop()
        give_way()
        # Only the three fields needed are decoded, and no path is joined per folder. Measured
        # 2026-11-15 on 686,000 files / 126,000 folders: 3.6 s before, 1.0 s now.
        own, number = link_identity(node.snapshot)[:2] if node.snapshot is not None else (None, NO_FILE_NUMBER)
        has_path = node.parent is not None or bool(node.name)  # ``node.path is not None``
        counts.unknown |= has_path and number == NO_FILE_NUMBER
        if in_bin:
            counts.bin_found = True
            counts.bin_complete &= node.error is None and not node.is_link
        above = node.parent.snapshot if node.parent else None
        if node.error == MOUNT_BOUNDARY or (own is not None and above is not None
                                           and own != link_identity(above)[0]):
            counts.mounts += 1
        if node.is_link:
            continue
        if totals is not None:  # the module counts the files and hands the folders back
            stack.extend((child, in_bin or _trash_node(child))
                         for child in add(totals, node.children, device, in_bin))  # type: ignore[misc]
            continue
        for child in node.children:
            if child.is_dir:
                stack.append((child, in_bin or _trash_node(child)))
            elif not child.is_link:
                counts.add(child, device, in_bin)
    if totals is None:
        counts.finish()
    else:
        counts.named, counts.unique, counts.bin_seen, counts.foreign, unknown = finish(totals)  # type: ignore[misc]
        counts.unknown |= unknown
    return counts


def _usage(path: str | None) -> tuple[int | None, int | None, int | None, int | None]:
    if path is None:
        return None, None, None, None
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return None, None, None, None
    return usage.total, usage.used, usage.free, max(0, usage.total - usage.used - usage.free)


def _status(root: Node, coverage: Coverage, unknown: bool, partial: bool) -> str:
    if root.path is None:
        return "multiple_roots"
    try:
        whole_volume = os.path.ismount(root.path)
        current = stat_snapshot(root.path)
    except OSError:
        return "capacity_unavailable"
    if root.snapshot is not None and unpack_snapshot(current).identity != unpack_snapshot(root.snapshot).identity:
        return "root_changed"
    if not whole_volume:
        return "folder_only"
    if partial or not coverage.complete:
        return "incomplete"
    return "identity_unknown" if unknown else "estimated"


def _is_trash(path: str | None) -> bool:
    """Recognise platform Trash namespaces, not an arbitrary folder called Trash."""
    if path is None:
        return False
    normal = path.replace("\\", "/").rstrip("/")
    name = normal.rsplit("/", 1)[-1]
    if os.name == "nt":
        return name.casefold() == "$recycle.bin" and os.path.ismount(os.path.dirname(path))
    home = os.path.expanduser("~").replace("\\", "/").rstrip("/")
    data = os.environ.get("XDG_DATA_HOME", home + "/.local/share")
    if not os.path.isabs(data):
        data = home + "/.local/share"
    data = os.path.normpath(data).replace("\\", "/").rstrip("/")
    if normal in (home + "/.Trash", data + "/Trash"):
        return True
    return (name in (".Trash", ".Trashes") or name.startswith(".Trash-") and name[7:].isdigit()) and (
        os.path.ismount(os.path.dirname(path)))


def _trash_node(node: Node) -> bool:
    name = node.name.casefold()
    return node.is_dir and (name in ("$recycle.bin", ".trash", ".trashes", "trash") or name.startswith(".trash-")) and (
        _is_trash(node.path))


@dataclass(slots=True)
class _Counts:
    named: int = 0
    unique: int = 0
    bin_seen: int = 0
    foreign: int = 0
    mounts: int = 0
    unknown: bool = False
    bin_found: bool = False
    bin_complete: bool = True
    links: dict[tuple[int, int], list[int]] = field(default_factory=dict)

    def add(self, node: Node, device: int | None, in_bin: bool) -> None:
        if node.snapshot is None:
            self.named += node.allocated
            self.unknown = True
            self.count(node.allocated, in_bin, False)
            return
        own, number, links = link_identity(node.snapshot)
        foreign = device is not None and own != device
        if not foreign:
            self.named += node.allocated
        known = number != NO_FILE_NUMBER
        self.unknown |= not known or not links or node.error is not None
        if known and links > 1:
            group = self.links.setdefault((own, number), [node.allocated, int(in_bin), int(foreign)])
            group[0] = max(group[0], node.allocated)
            group[1] |= int(in_bin)
        else:
            self.count(node.allocated, in_bin, foreign)

    def count(self, allocated: int, in_bin: bool, foreign: bool) -> None:
        if foreign:
            self.foreign += allocated
        else:
            self.unique += allocated
            if in_bin:
                self.bin_seen += allocated

    def finish(self) -> None:
        for allocated, in_bin, foreign in self.links.values():
            self.count(allocated, bool(in_bin), bool(foreign))
