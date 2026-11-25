"""Find entries anywhere in a scanned tree: by name, and by size, age, type and kind."""

from __future__ import annotations

import fnmatch
import heapq
import math
import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from je_file_tree.core.analysis import category_of, extension_of
from je_file_tree.core.name_regex import name_regex
from je_file_tree.core.node import Node
from je_file_tree.core.owner_id import OwnerID, owner_identifier, owner_name
from je_file_tree.core.pacing import give_way

WILDCARDS = frozenset("*?[")
ANY, FILES, FOLDERS = "any", "files", "folders"
KINDS = (ANY, FILES, FOLDERS)


@dataclass(frozen=True, slots=True)
class Query:
    """What to look for; every condition given must hold.

    ``text`` is read by ``name_matcher``. Sizes are in bytes. ``changed_within`` and ``unchanged_for``
    are spans in seconds counted back from the moment of the search, so a saved query stays meaningful.
    ``category`` (a key of ``analysis.CATEGORIES``) matches files of that type only; ``kind`` is one of
    ``KINDS``. ``modified_since`` is an inclusive POSIX timestamp; ``modified_before``
    is exclusive. Unknown or nonfinite modification times fail any active time condition.

    With ``regex``, ``text`` is a regular expression found anywhere in a name (``name_regex``). ``exclude``
    is read like ``text``: a matching entry is left out, a matching folder with everything in it. ``owner``
    is part of a recorded owner's name or identifier. Depths count from the searched folder, whose own
    entries are at depth 1; deeper folders than ``max_depth`` are not looked into.
    """

    text: str = ""
    min_size: int | None = None
    max_size: int | None = None
    changed_within: float | None = None
    unchanged_for: float | None = None
    category: str | None = None
    kind: str = ANY
    modified_since: float | None = None
    modified_before: float | None = None
    regex: bool = False
    exclude: str = ""
    owner: str = ""
    min_depth: int | None = None
    max_depth: int | None = None


@dataclass(frozen=True, slots=True)
class SearchResult:
    """What a search found: the ``limit`` largest matches, and the count and size of all of them.

    ``size`` counts an entry inside a matching folder once (with the folder).
    """

    matches: list[Node]
    count: int
    size: int


def name_matcher(query: str) -> Callable[[str], object] | None:
    """A test for names (truthy when one matches), from what the user typed; None when there is nothing to look for.

    Case never matters. Several patterns are separated by ``;``. A pattern with ``*``, ``?``
    or ``[...]`` must match the whole name (``*.mp4``); plain text matches anywhere in it (``backup``).
    """
    parts = [part.strip() for part in query.split(";") if part.strip()]
    if not parts:
        return None
    expressions = [fnmatch.translate(part) if WILDCARDS & set(part) else rf"(?s:.*{re.escape(part)}.*)\Z"
                   for part in parts]
    pattern = re.compile("|".join(f"(?:{expression})" for expression in expressions), re.IGNORECASE)
    return pattern.match


def search(root: Node, query: Query | str, limit: int = 1000,
           cancel: threading.Event | None = None, *, now: float | None = None) -> SearchResult | None:
    """Every entry beneath ``root`` (files and folders, not ``root`` itself) that ``query`` accepts.

    A plain string is a name query. The matches are listed largest first; a query with no condition
    finds nothing. Returns None when ``cancel`` is set before the search is done (checked once per
    folder). ``now`` (a POSIX time) is what the age conditions count back from.
    """
    query = Query(text=query) if isinstance(query, str) else query
    if query == Query(text=query.text):  # a name alone: test the names directly, the common and fastest case
        matcher = name_matcher(query.text)
        collected = None if matcher is None else _collect(root, matcher, cancel, by_name=True)
    else:
        test = accepts(query, time.time() if now is None else now)
        bounds = _Bounds(name_matcher(query.exclude), query.min_depth, query.max_depth)
        collected = None if test is None else _collect(root, test, cancel, by_name=False, bounds=bounds)
    if collected is None:
        return None if cancel is not None and cancel.is_set() else SearchResult([], 0, 0)
    found, size = collected
    largest = heapq.nlargest(limit, found, key=_size) if limit > 0 else []
    return SearchResult(largest, len(found), size)


@dataclass(frozen=True, slots=True)
class _Bounds:
    """Which part of the tree a search looks at."""

    excluded: Callable[[str], object] | None = None
    min_depth: int | None = None
    max_depth: int | None = None

    def stops(self, depth: int) -> bool:
        """Whether entries below ``depth`` are too deep."""
        return self.max_depth is not None and depth >= self.max_depth

    def deep_enough(self, depth: int) -> bool:
        """Whether entries at ``depth`` count."""
        return self.min_depth is None or depth >= self.min_depth


def _collect(root: Node, test: Callable[..., object], cancel: threading.Event | None, *,
             by_name: bool, bounds: _Bounds | None = None) -> tuple[list[Node], int] | None:
    """Every entry beneath ``root`` that ``test`` accepts (given its name, or the node), and their size.

    The size counts a match inside a matching folder once, with that folder. It is added up on the
    way down: asking for the outermost matches afterwards walked every match's parents and took
    3.6 s of a 6.9 s profiled search of 1,000,000 files (2026-11-14). None when cancelled.
    """
    found: list[Node] = []
    size = 0
    bounds = bounds or _Bounds()
    excluded = bounds.excluded
    stack = [(root, False, 0)]
    while stack:
        if cancel is not None and cancel.is_set():
            return None
        give_way()
        folder, counted, above = stack.pop()
        depth = above + 1
        if bounds.stops(above):
            continue
        counts = bounds.deep_enough(depth)
        sources = folder.path is None  # a combined scan's own folders: what the search is in, not what it finds
        for child in folder.children:
            if not sources and excluded is not None and excluded(child.name) is not None:
                continue
            matched = counts and not sources and bool(test(child.name if by_name else child))
            if matched:
                found.append(child)
                if not counted:
                    size += child.size
            if child.children:
                stack.append((child, counted or matched, depth))
    return found, size


def accepts(query: Query, now: float) -> Callable[[Node], bool] | None:
    """The test of an entry against every condition of ``query``; None when it has no condition at all."""
    name = _name_test(query)
    kind = _kind_test(query)
    kept = _kept_by_size_and_age(query, now)
    owned = _owner_test(query.owner)
    if (name is None and kind is None and kept is None and owned is None and name_matcher(query.exclude) is None
            and query.min_depth is None and query.max_depth is None):
        return None

    def test(node: Node) -> bool:
        if owned is not None and not owned(node):
            return False
        if name is not None and name(node.name) is None:
            return False
        if kind is not None and not kind(node):
            return False
        return kept is None or kept(node)

    return test


def _name_test(query: Query) -> Callable[[str], object] | None:
    """The test of a name; None when the query names nothing."""
    if query.regex and query.text:
        return name_regex(query.text).search
    return name_matcher(query.text)


def _owner_test(text: str) -> Callable[[Node], bool] | None:
    """One test for a recorded owner; each owner's name is looked up once, entries without one never match."""
    wanted = text.strip().casefold()
    if not wanted:
        return None
    answers: dict[OwnerID, bool] = {}

    def test(node: Node) -> bool:
        owner = node.owner
        if owner is None or node.is_dir:
            return False
        if owner not in answers:
            answers[owner] = (wanted in owner_identifier(owner).casefold()
                              or wanted in owner_name(owner).casefold())
        return answers[owner]

    return test


def _kind_test(query: Query) -> Callable[[Node], bool] | None:
    """One test for the kind and the file type of ``query`` (None when it asks for neither)."""
    category = query.category
    if category is not None:
        if query.kind == FOLDERS:
            return lambda node: False  # a file type with folders only: every condition must hold, none can
        return lambda node: not node.is_dir and category_of(extension_of(node.name)) == category
    if query.kind == FILES:
        return lambda node: not node.is_dir
    if query.kind == FOLDERS:
        return lambda node: node.is_dir and not node.is_link
    return None


def _kept_by_size_and_age(query: Query, now: float) -> Callable[[Node], bool] | None:
    """One test for the size and age conditions of ``query`` (None when it has none)."""
    least = query.min_size if query.min_size is not None else -1
    most = query.max_size if query.max_size is not None else float("inf")
    since = now - query.changed_within if query.changed_within is not None else float("-inf")
    before = now - query.unchanged_for if query.unchanged_for is not None else None
    time_active = any(value is not None for value in (
        query.changed_within, query.unchanged_for, query.modified_since, query.modified_before))
    if query.min_size is None and query.max_size is None and not time_active:
        return None
    since = max(since, query.modified_since if query.modified_since is not None else float("-inf"))
    until = query.modified_before if query.modified_before is not None else float("inf")

    def kept(node: Node) -> bool:
        if not least <= node.size <= most:
            return False
        if not time_active:
            return True
        modified = node.modified
        return (math.isfinite(modified) and modified > 0 and since <= modified < until
                and (before is None or modified <= before))

    return kept



def _size(node: Node) -> int:
    return node.size
