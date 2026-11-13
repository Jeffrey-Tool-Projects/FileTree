"""A "free up space" plan: which entries the scan already found could give back a wanted amount, safest first.

The plan is built from what is already in memory: the clean-up suggestions (``cleanup``), duplicate
groups whose kept copy the user chose (``duplicates``) and the largest files with their removal advice
(``advice``). It reads recorded nodes only, never the disk, and is deterministic: the same inputs give
the same plan. It proposes and nothing else: it selects, approves and removes nothing, and whatever the
user picks from it still goes through ``MainWindow.move_to_trash`` with every question that asks.

Rules the plan keeps:

- protected and OS-managed entries (``Adviser`` answers *keep* / *OS-managed*) are never proposed;
- an entry is counted once: one inside a folder already in the plan is left out, and a folder holding
  entries already in the plan counts only the rest (``PlanEntry.counted``);
- a duplicate is proposed only when its group's kept copy was chosen by the user, still is in the tree
  and lies inside nothing the plan proposes; that kept copy is never proposed itself;
- the user's own large files (advice *your call*) are a separate list of options, never a step;
- every step lists at most ``max_entries`` entries and the options at most ``max_options``, and looks at
  no more than ``LOOK_FACTOR`` times as many candidates; the work is sorting the candidate lists and one
  walk up the parents (plus one advice answer) per candidate looked at, never a walk of the tree. Measured
  2026-11-14 on 50,000 duplicate extras that all had to be refused (inside Program Files) and 1,000 largest
  files: looking at every candidate took 3.4 s, with the look-up bound 0.24 s, so the dialog builds the plan
  on the GUI thread.

Sizes are the space on disk (``Node.allocated``) when the scan measured it, otherwise the file sizes. They
are estimates: hard links, compression, cloud files and the Recycle Bin all change what is really freed.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from je_file_tree.core.advice import LOW, MANAGED, PERSONAL, PROTECTED, REVIEW, Adviser
from je_file_tree.core.cleanup import CleanupGroup
from je_file_tree.core.duplicates import DuplicateGroup
from je_file_tree.core.node import Node, outermost

CLEANUP, DUPLICATES, LARGE_FILES = "cleanup", "duplicates", "large_files"
DEFAULT_MAX_ENTRIES = 200
DEFAULT_MAX_OPTIONS = 100
LOOK_FACTOR = 10  # candidates looked at per entry a step may list (see the module docstring)
_NEVER = (PROTECTED, MANAGED)


@dataclass(frozen=True, slots=True)
class ReclaimSources:
    """What a plan is built from: the scan on screen and the suggestions already found for it.

    ``adviser`` must answer for the same ``groups`` (``Adviser.ready`` once they are known). ``total`` and
    ``free`` are the drive's capacity, when known, for a "until the drive has X % free" target.
    """

    root: Node
    adviser: Adviser
    groups: Sequence[CleanupGroup] = ()
    duplicates: Sequence[DuplicateGroup] = ()
    largest: Sequence[Node] = ()
    total: int | None = None
    free: int | None = None

    @property
    def ready(self) -> bool:
        """Whether the clean-up suggestions are known, so the plan is complete."""
        return self.adviser.ready


@dataclass(frozen=True, slots=True)
class PlanEntry:
    """One proposed entry: its own estimated ``size`` and the part of it the plan has not counted yet."""

    node: Node
    size: int
    counted: int


@dataclass(frozen=True, slots=True)
class PlanStep:
    """One proposed kind of entry, with its ``risk`` (an advice kind: low, review or personal).

    ``size`` is what the step adds to the plan, ``total`` the plan's running total after it and ``more``
    the candidates left out by the bound (not looked at, so not counted).
    """

    category: str
    key: str
    risk: str
    entries: tuple[PlanEntry, ...]
    size: int
    total: int
    more: int = 0


@dataclass(frozen=True, slots=True)
class ReclaimPlan:
    """The ranked ``steps`` towards ``target`` bytes, and the user's own large files as ``options``."""

    target: int
    steps: tuple[PlanStep, ...]
    options: PlanStep | None
    measured: bool
    undecided_duplicates: int = 0

    @property
    def total(self) -> int:
        """What all steps together could give back (the options left out)."""
        return self.steps[-1].total if self.steps else 0

    @property
    def reached(self) -> bool:
        """Whether the steps alone reach the target."""
        return self.total >= self.target

    @property
    def shortfall(self) -> int:
        """How much the steps fall short of the target (0 once it is reached)."""
        return max(0, self.target - self.total)

    def needed(self, step: PlanStep) -> bool:
        """Whether ``step`` is still needed to reach the target when the steps are taken in order."""
        return step.total - step.size < self.target

    def size_of(self, nodes: Iterable[Node]) -> int:
        """The estimate for a selection: each entry once, an entry inside a chosen folder with that folder."""
        return sum(_size(node, self.measured) for node in outermost(nodes))


def free_share_target(percent: float, total: int, free: int) -> int:
    """The bytes to give back so that ``percent`` of a ``total``-byte drive with ``free`` bytes free is free."""
    wanted = math.ceil(total * max(0.0, min(percent, 100.0)) / 100)
    return max(0, wanted - free)


def build_plan(target: int, sources: ReclaimSources, *, max_entries: int = DEFAULT_MAX_ENTRIES,
               max_options: int = DEFAULT_MAX_OPTIONS) -> ReclaimPlan:
    """Rank what ``sources`` hold into a plan towards ``target`` bytes (see the module docstring).

    Lower-risk clean-up comes first, then duplicates and the clean-up that needs a review, each kind the
    largest first; the user's own large files follow as options.
    """
    root = sources.root
    measured = root.allocated > 0
    usable, undecided = _usable_duplicates(sources)
    keepers = {group.kept for group in usable if group.kept is not None}
    ledger = _Ledger(root, sources.adviser, measured, _guarded(keepers))
    steps: list[PlanStep] = []
    for category, key, risk, nodes in _candidates(sources.groups, usable, keepers, measured):
        step = _step(ledger, category, key, risk, nodes, max(max_entries, 0))
        if step is not None:
            steps.append(step)
    personal = [node for node in sources.largest if not node.is_dir and node not in keepers]
    personal.sort(key=lambda node: -_size(node, measured))
    ledger.only = PERSONAL
    options = _step(ledger, LARGE_FILES, PERSONAL, PERSONAL, personal, max(max_options, 0))
    return ReclaimPlan(max(target, 0), tuple(steps), options, measured, undecided)


def _usable_duplicates(sources: ReclaimSources) -> tuple[list[DuplicateGroup], int]:
    """Groups whose user-chosen kept copy is still in the tree and inside no clean-up suggestion."""
    suggested = {node for group in sources.groups for node in group.nodes}
    usable: list[DuplicateGroup] = []
    undecided = 0
    for group in sources.duplicates:
        kept = group.kept
        if kept is None or kept not in group.files:
            undecided += 1
            continue
        if kept.is_in(sources.root) and not _inside_any(kept, suggested):
            usable.append(group)
    return usable, undecided


def _candidates(groups: Sequence[CleanupGroup], duplicates: Sequence[DuplicateGroup], keepers: set[Node],
                measured: bool) -> list[tuple[str, str, str, list[Node]]]:
    """Every kind of candidate with its entries (largest first), in the order the plan takes them."""
    ranked: list[tuple[int, int, int, tuple[str, str, str, list[Node]]]] = []
    for position, group in enumerate(groups):
        risk = LOW if group.details.risk == "low" else REVIEW
        nodes = sorted(group.nodes, key=lambda node: -_size(node, measured))
        ranked.append((0 if risk == LOW else 1, -sum(_size(node, measured) for node in nodes), position,
                       (CLEANUP, group.key, risk, nodes)))
    extras = [node for group in duplicates for node in group.files if node is not group.kept and node not in keepers]
    if extras:
        extras.sort(key=lambda node: -_size(node, measured))
        ranked.append((1, -sum(_size(node, measured) for node in extras), len(groups),
                       (DUPLICATES, DUPLICATES, REVIEW, extras)))
    ranked.sort(key=lambda item: item[:3])
    return [candidate for *_order, candidate in ranked]


def _step(ledger: _Ledger, category: str, key: str, risk: str, nodes: Sequence[Node],
          limit: int) -> PlanStep | None:
    """Take up to ``limit`` entries of ``nodes`` the plan does not hold yet; None when none is left."""
    entries: list[PlanEntry] = []
    looked = 0
    for node in nodes:
        if len(entries) >= limit or looked >= limit * LOOK_FACTOR:
            break
        looked += 1
        entry = ledger.offer(node)
        if entry is not None:
            entries.append(entry)
    if not entries:
        return None
    size = sum(entry.counted for entry in entries)
    return PlanStep(category, key, risk, tuple(entries), size, ledger.add(size), len(nodes) - looked)


class _Ledger:
    """The space already in the plan: the entries taken, and how much of each folder above them."""

    def __init__(self, root: Node, adviser: Adviser, measured: bool, guarded: set[Node]) -> None:
        self._root, self._adviser, self._measured, self._guarded = root, adviser, measured, guarded
        self._taken: set[Node] = set()
        self._below: dict[Node, int] = {}
        self.total = 0
        self.only: str | None = None

    def add(self, size: int) -> int:
        """Add a finished step's size; returns the running total."""
        self.total += size
        return self.total

    def offer(self, node: Node) -> PlanEntry | None:
        """Take ``node`` into the plan unless it is not eligible or adds nothing; its entry, or None."""
        if node.parent is None or node.is_link or node.error is not None or node in self._guarded:
            return None
        current: Node | None = node
        while current is not None:
            if current in self._taken:
                return None  # inside (or the same as) an entry already counted
            top, current = current, current.parent
        if top is not self._root or not self._allowed(node):
            return None
        size = _size(node, self._measured)
        counted = size - self._below.get(node, 0)
        if counted <= 0:
            return None
        self._taken.add(node)
        above = node.parent
        while above is not None:
            self._below[above] = self._below.get(above, 0) + counted
            above = above.parent
        return PlanEntry(node, size, counted)

    def _allowed(self, node: Node) -> bool:
        kind = self._adviser.advice(node).kind
        return kind == self.only if self.only is not None else kind not in _NEVER


def _guarded(keepers: Iterable[Node]) -> set[Node]:
    """The kept copies and every folder above one: removing any of them would take a kept copy along."""
    guarded: set[Node] = set()
    for kept in keepers:
        current: Node | None = kept
        while current is not None and current not in guarded:
            guarded.add(current)
            current = current.parent
    return guarded


def _inside_any(node: Node, folders: set[Node]) -> bool:
    current: Node | None = node
    while current is not None:
        if current in folders:
            return True
        current = current.parent
    return False


def _size(node: Node, measured: bool) -> int:
    """The estimate for one entry: its space on disk when the scan measured it, else its size."""
    return max(node.allocated if measured else node.size, 0)
