"""Whether an entry can go: one plain answer per entry, from evidence the scan already holds.

The answer combines three things FileTree knows without touching the disk again: the places Windows
manages itself (``system_files``), the places whose removal breaks the system or programs
(``protected``) and the clean-up suggestions of the scan on screen (``cleanup``). It is advice only:
it selects nothing, approves nothing and never replaces the review and the confirmations of
``MainWindow.move_to_trash``. The most careful answer wins — a managed or protected place stays
*keep* even when a clean-up rule matches it.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from je_file_tree.core.cleanup import CleanupGroup
from je_file_tree.core.node import Node
from je_file_tree.core.protected import Protection, protection_of
from je_file_tree.core.system_files import system_file

LOW, REVIEW, PERSONAL, PROTECTED, MANAGED, PENDING = "low", "review", "personal", "protected", "managed", "pending"
KINDS = (LOW, REVIEW, PERSONAL, PROTECTED, MANAGED, PENDING)  # the order a list sorts them in
_CACHE_LIMIT = 4096  # answers kept; a list shows at most 1,000 rows, so repaints and sorts never recompute


@dataclass(frozen=True, slots=True)
class Advice:
    """One answer: its ``kind`` and what decided it (a clean-up group or a protected place)."""

    kind: str
    group: CleanupGroup | None = None
    protection: Protection | None = None

    @property
    def rank(self) -> int:
        """Where this answer sorts: what can go first, what must stay last."""
        return KINDS.index(self.kind)


class Adviser:
    """Answers for the entries of one scan.

    ``groups`` are the clean-up suggestions of that scan, or None while they are still being looked
    for: an entry no place protects is then *pending* rather than called the user's own.
    """

    def __init__(self, places: Iterable[Protection], groups: Sequence[CleanupGroup] | None = None, *,
                 platform: str = sys.platform, environ: Mapping[str, str] | None = None) -> None:
        self._places = tuple(places)
        self._platform, self._environ = platform, environ
        self._ready = groups is not None
        self._claimed: dict[Node, CleanupGroup] = {
            node: group for group in groups or () for node in group.nodes}
        self._cache: dict[Node, Advice] = {}

    @property
    def ready(self) -> bool:
        """Whether the clean-up suggestions are known, so no answer is *pending*."""
        return self._ready

    def advice(self, node: Node) -> Advice:
        """The answer for ``node``; reads recorded paths and parents only, never the disk."""
        found = self._cache.get(node)
        if found is None:
            if len(self._cache) >= _CACHE_LIMIT:
                self._cache.clear()
            found = self._cache[node] = self._decide(node)
        return found

    def _decide(self, node: Node) -> Advice:
        path = node.path
        if path is not None:
            if system_file(path, platform=self._platform, environ=self._environ) is not None:
                return Advice(MANAGED)
            protection = protection_of(path, self._places, self._platform)
            if protection is not None:
                return Advice(PROTECTED, protection=protection)
        group = self._group_of(node)
        if group is not None:
            return Advice(LOW if group.details.risk == "low" else REVIEW, group=group)
        return Advice(PERSONAL if self._ready else PENDING)

    def _group_of(self, node: Node) -> CleanupGroup | None:
        """The suggestion that names ``node`` or a folder above it (a matching folder is suggested whole)."""
        current: Node | None = node
        while current is not None and self._claimed:
            group = self._claimed.get(current)
            if group is not None:
                return group
            current = current.parent
        return None
