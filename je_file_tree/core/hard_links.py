"""Separate once-per-observed-hard-link accounting from actual named file lengths/allocation."""

from __future__ import annotations

import os
import stat
import threading
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from je_file_tree.core.node import Node
from je_file_tree.core.pacing import give_way
from je_file_tree.core.snapshot import Snapshot, unpack_snapshot

_ZERO = (0, 0)


@dataclass(frozen=True, slots=True)
class HardLinkAccounting:
    """Observed alias reductions; missing/inconsistent identities never imply duplicate data."""

    aliases: int
    logical_overcount: int
    allocation_overcount: int
    unknown: int


@dataclass(frozen=True, slots=True)
class HardLinkPlan:
    """Counted totals worked out without changing the tree: only the entries whose value changes."""

    accounting: HardLinkAccounting
    changes: tuple[tuple[Node, tuple[int, int] | None], ...]

    def apply(self) -> None:
        """Set the planned counted totals; cheap, so the GUI thread may do it (no tree walk)."""
        for node, value in self.changes:
            node.accounting = value


def account_hard_links(root: Node, *, cancel: threading.Event | None = None) -> HardLinkAccounting | None:
    """Assign deterministic once-per-identity totals using recorded stat only; no payload/OS query.

    The lexically first observed path contributes bytes, other proven names contribute zero only to
    accounting. Node.size/allocated/file_count/snapshots remain unchanged. Unknown or inconsistent
    hard-link groups retain named totals. Groups outside the observed tree are never assumed present;
    shared extents and directory metadata remain unknown. Reapply after changing this captured tree.
    Canceled surveys leave existing accounting untouched. Run whole-tree work on a worker thread.
    """
    plan = plan_hard_links(root, cancel=cancel)
    if plan is None:
        return None
    plan.apply()
    return plan.accounting


def plan_hard_links(root: Node, *, cancel: threading.Event | None = None,
                    without: Iterable[Node] = ()) -> HardLinkPlan | None:
    """The counted totals ``account_hard_links`` would set, as if the disjoint ``without`` entries were gone.

    Reads the tree only, so a worker can plan while the window shows it; ``HardLinkPlan.apply`` then
    sets the few values that change. After a delete the window detaches ``without`` (named totals) and
    applies the plan (counted totals) instead of scanning the root again: a name left alone of its
    group is counted in full again. None when canceled.
    """
    removed = {id(node) for node in without}
    survey = _survey(root, cancel, removed)
    if survey is None:
        return None
    folders, files, groups, unknown = survey
    found = _duplicates(groups, cancel)
    if found is None:
        return None
    duplicate_ids, logical, allocated, inconsistent = found
    changes: list[tuple[Node, tuple[int, int] | None]] = []
    planned: dict[int, tuple[int, int] | None] = {}
    for node in files:
        wanted = _ZERO if id(node) in duplicate_ids else None
        if node.accounting != wanted:
            changes.append((node, wanted))
            planned[id(node)] = wanted
    gone = _removed_totals(root, without)
    for folder in reversed(folders):
        wanted_total = _folder_total(folder, root, removed, planned, gone)
        if folder.accounting != wanted_total:
            changes.append((folder, wanted_total))
            planned[id(folder)] = wanted_total
    accounting = HardLinkAccounting(len(duplicate_ids), logical, allocated, unknown + inconsistent)
    return HardLinkPlan(accounting, tuple(changes))


def _duplicates(groups: dict[tuple[int, int], list[tuple[Node, Snapshot]]], cancel: threading.Event | None
                ) -> tuple[set[int], int, int, int] | None:
    """The names counted as zero (all but the lexically first of a consistent group), their bytes and
    allocation, and how many names belong to inconsistent groups; None when canceled."""
    duplicate_ids: set[int] = set()
    logical = allocated = inconsistent = 0
    for group in groups.values():
        if cancel is not None and cancel.is_set():
            return None
        signatures = {(info.size, info.modified_ns, info.changed_ns, info.attributes,
                       node.size, node.allocated) for node, info in group}
        if len(signatures) != 1:
            inconsistent += len(group)
            continue
        ordered = sorted((node for node, _info in group), key=lambda node: (os.path.normcase(node.path), node.path))
        for node in ordered[1:]:
            duplicate_ids.add(id(node))
            logical += node.size
            allocated += node.allocated
    if cancel is not None and cancel.is_set():
        return None
    return duplicate_ids, logical, allocated, inconsistent


def _folder_total(folder: Node, root: Node, removed: set[int], planned: dict[int, tuple[int, int] | None],
                  gone: dict[int, tuple[int, int]]) -> tuple[int, int] | None:
    """A folder's planned counted totals, or None where they equal its named totals (the root always has them)."""
    size = allocation = 0
    for child in folder.children:
        if id(child) in removed:
            continue
        value = planned.get(id(child), child.accounting)
        if value is None:
            minus = gone.get(id(child), _ZERO)
            value = (child.size - minus[0], child.allocated - minus[1])
        size += value[0]
        allocation += value[1]
    minus = gone.get(id(folder), _ZERO)
    changed = (size, allocation) != (folder.size - minus[0], folder.allocated - minus[1])
    return (size, allocation) if folder is root or changed else None


def _removed_totals(root: Node, without: Iterable[Node]) -> dict[int, tuple[int, int]]:
    """Named bytes each folder above the ``without`` entries loses when they are detached."""
    gone: dict[int, tuple[int, int]] = {}
    for node in without:
        above = node.parent
        while above is not None:
            size, allocation = gone.get(id(above), _ZERO)
            gone[id(above)] = (size + node.size, allocation + node.allocated)
            if above is root:
                break
            above = above.parent
    return gone


def _survey(root: Node, cancel: threading.Event | None, removed: set[int]) -> tuple[
        list[Node], list[Node], dict[tuple[int, int], list[tuple[Node, Snapshot]]], int] | None:
    """Folders (parents first), files and recorded link groups, leaving out the ``removed`` subtrees."""
    folders: list[Node] = []
    files: list[Node] = []
    groups: dict[tuple[int, int], list[tuple[Node, Snapshot]]] = defaultdict(list)
    unknown = 0
    stack = [root]
    while stack:
        node = stack.pop()
        if id(node) in removed:
            continue
        stack.extend(reversed(node.children))
        if cancel is not None and cancel.is_set():
            return None
        if node.is_dir:
            folders.append(node)
            give_way()
        elif not node.is_link:
            files.append(node)
            if node.snapshot is None or node.error:
                unknown += 1
                continue
            info = unpack_snapshot(node.snapshot)
            if not stat.S_ISREG(info.mode):
                continue
            if not info.inode or not info.links:
                unknown += 1
            elif info.links > 1:
                groups[info.identity].append((node, info))
    return folders, files, groups, unknown
