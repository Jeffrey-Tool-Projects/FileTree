"""The read-only console reports besides ``scan``: search, duplicates, clean-up candidates and folder budgets.

Each prints one JSON document about a finished scan. Nothing here moves, deletes or changes anything, and no
option makes it do so; clean-up candidates are listed with their risk, not acted on.
"""

from __future__ import annotations

import argparse
import os
import stat
import threading
import time
from collections.abc import Callable
from decimal import Decimal, InvalidOperation
from pathlib import Path

from je_file_tree.core.analysis import CATEGORIES
from je_file_tree.core.cleanup import find_cleanup
from je_file_tree.core.cleanup_policy import CleanupPolicy, load_policy
from je_file_tree.core.coverage import Coverage
from je_file_tree.core.duplicates import DuplicateSearchCancelledError, find_duplicates
from je_file_tree.core.folder_budgets import BudgetRule, BudgetTicket, observe_budgets
from je_file_tree.core.node import Node
from je_file_tree.core.search import KINDS, Query, accepts, search

OVER_BUDGET = 4
MAX_BYTES = (1 << 63) - 1
_POLICY_LIMIT = 256_000
_DAY = 86400.0
_UNITS = {"": 1, "b": 1, "k": 1 << 10, "m": 1 << 20, "g": 1 << 30, "t": 1 << 40}
_PATHS_PER_GROUP = 100

Report = Callable[[argparse.Namespace, Node, Coverage, threading.Event], tuple[dict, int | None]]


def size_argument(text: str) -> int:
    """``500``, ``10K``, ``1.5G``: whole bytes, binary units."""
    number, unit = text.strip().lower().removesuffix("ib"), ""
    if number[-1:].isalpha():
        number, unit = number[:-1], number[-1]
    try:
        value = Decimal(number) * _UNITS[unit]
        whole = int(value)
        if not value.is_finite() or value != whole or not 0 <= whole <= MAX_BYTES:
            raise ValueError(text)
    except (InvalidOperation, KeyError, ValueError, OverflowError) as error:
        raise argparse.ArgumentTypeError(f"not a size: {text!r}") from error
    return whole


def days_argument(text: str) -> float:
    """A positive number of days, in seconds."""
    try:
        days = float(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"not a number of days: {text!r}") from error
    if not 0 < days <= 36500:  # noqa: PLR2004 - a hundred years
        raise argparse.ArgumentTypeError(f"not a number of days: {text!r}")
    return days * _DAY


def budget_argument(text: str) -> tuple[str, int]:
    """``PATH=SIZE``."""
    path, separator, size = text.rpartition("=")
    if not separator or not path:
        raise argparse.ArgumentTypeError(f"expected PATH=SIZE: {text!r}")
    return os.path.abspath(path), size_argument(size)


def depth_argument(text: str) -> int:
    """A depth of at least one."""
    if not text.isascii() or not text.isdigit() or int(text) < 1:
        raise argparse.ArgumentTypeError(f"not a depth: {text!r}")
    return int(text)


def add_search(parser: argparse.ArgumentParser) -> None:
    """The conditions of the Search tab."""
    parser.add_argument("--name", default="", metavar="TEXT", help="text or patterns, such as '*.iso;*.zip'")
    parser.add_argument("--regex", action="store_true", help="read --name as a regular expression")
    parser.add_argument("--exclude-names", default="", metavar="TEXT", help="leave matching entries out")
    parser.add_argument("--owner", default="", metavar="TEXT", help="part of the owner's name (records owners)")
    parser.add_argument("--min-size", type=size_argument, metavar="SIZE")
    parser.add_argument("--max-size", type=size_argument, metavar="SIZE")
    parser.add_argument("--changed-within", type=days_argument, metavar="DAYS")
    parser.add_argument("--unchanged-for", type=days_argument, metavar="DAYS")
    parser.add_argument("--type", choices=CATEGORIES)
    parser.add_argument("--kind", choices=KINDS, default=KINDS[0])
    parser.add_argument("--min-depth", type=depth_argument, metavar="N")
    parser.add_argument("--max-depth", type=depth_argument, metavar="N")


def search_query(args: argparse.Namespace) -> Query:
    """What ``search`` looks for; raises ValueError when it names no condition or an unusable one."""
    query = Query(text=args.name, min_size=args.min_size, max_size=args.max_size,
                  changed_within=args.changed_within, unchanged_for=args.unchanged_for, category=args.type,
                  kind=args.kind, regex=args.regex, exclude=args.exclude_names, owner=args.owner,
                  min_depth=args.min_depth, max_depth=args.max_depth)
    if accepts(query, time.time()) is None:
        raise ValueError("search needs at least one condition")
    return query


def report_search(args: argparse.Namespace, root: Node, _coverage: Coverage,
                  cancel: threading.Event) -> tuple[dict, int | None]:
    """The largest matches, and the count and size of all of them."""
    result = search(root, search_query(args), args.limit, cancel)
    if result is None:
        return {}, None
    return {"kind": "search", "count": result.count, "bytes": result.size, "listed": len(result.matches),
            "matches": [_entry(node) for node in result.matches]}, 0


def add_duplicates(parser: argparse.ArgumentParser) -> None:
    """What ``duplicates`` compares."""
    parser.add_argument("--min-size", type=size_argument, default=1 << 20, metavar="SIZE")


def report_duplicates(args: argparse.Namespace, root: Node, _coverage: Coverage,
                      cancel: threading.Event) -> tuple[dict, int | None]:
    """Groups of files with the same content; reads only files of the same size."""
    try:
        result = find_duplicates(root, min_size=args.min_size, workers=args.workers, cancel=cancel)
    except DuplicateSearchCancelledError:
        return {}, None
    groups = [{"bytes": group.size, "copies": len(group.files), "extra_bytes": group.extra,
               "paths": [node.path for node in group.files[:_PATHS_PER_GROUP]]}
              for group in result.groups[:args.limit]]
    return {"kind": "duplicates", "groups": len(result.groups), "extra_bytes": result.extra,
            "unreadable_files": result.skipped, "listed": len(groups), "entries": groups}, 0


def add_cleanup(parser: argparse.ArgumentParser) -> None:
    """Which rules ``cleanup`` uses."""
    parser.add_argument("--policy", metavar="FILE", help="a clean-up policy exported or saved as JSON")


def read_policy(path: str | None) -> CleanupPolicy:
    """The policy to list with; the built-in one without a file."""
    if path is None:
        return CleanupPolicy()
    return load_policy(_policy_text(Path(path)))


def _policy_text(path: Path) -> str:
    """Only an ordinary ``.json`` file of bounded size is read; nothing of it is echoed back."""
    if path.suffix.casefold() != ".json":
        raise ValueError("a clean-up policy is a .json file")
    resolved = path.resolve(strict=True)  # FileNotFoundError: an I/O error, as before
    info = resolved.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > _POLICY_LIMIT:
        raise ValueError("a clean-up policy is an ordinary .json file of at most 256 KB")
    with resolved.open(encoding="utf-8") as stream:
        return stream.read(_POLICY_LIMIT + 1)


def report_cleanup(args: argparse.Namespace, root: Node, coverage: Coverage,
                   cancel: threading.Event) -> tuple[dict, int | None]:
    """Candidates by rule, with their risk; a list to look at, never an instruction."""
    groups = find_cleanup(root, policy=read_policy(args.policy), coverage=coverage, cancel=cancel)
    if groups is None:
        return {}, None
    listed = [{"rule": group.key, "risk": group.details.risk, "minimum_days": group.details.minimum_age,
               "count": len(group.nodes), "bytes": group.size,
               "entries": [_entry(node) for node in group.nodes[:args.limit]]} for group in groups]
    return {"kind": "cleanup", "count": sum(len(group.nodes) for group in groups),
            "bytes": sum(group.size for group in groups), "groups": listed}, 0


def add_budget(parser: argparse.ArgumentParser) -> None:
    """The folders and their limits."""
    parser.add_argument("--budget", type=budget_argument, action="append", required=True, metavar="PATH=SIZE",
                        help="a folder in the scan and its limit; repeat for more")


def report_budget(args: argparse.Namespace, root: Node, coverage: Coverage,
                  cancel: threading.Event) -> tuple[dict, int | None]:
    """Each folder's size against its limit; unknown sizes are never called within the limit."""
    rules = tuple(BudgetRule(f"cli-{index}", 1, path, path, limit) for index, (path, limit) in enumerate(args.budget))
    batch = observe_budgets(root, coverage, BudgetTicket(1, rules), time.time(), cancel)
    if batch is None:
        return {}, None
    seen = {observation.identity: observation for observation in batch.observations}
    rows, over, unknown = [], False, False
    for rule in rules:
        observation = seen.get(rule.identity)
        size = observation.bytes if observation is not None else None
        reason = observation.reason if observation is not None else "outside_scan"
        rows.append({"path": rule.path, "limit": rule.limit, "bytes": size, "reason": reason,
                     "over_by": None if size is None else max(0, size - rule.limit)})
        over |= size is not None and size > rule.limit
        unknown |= size is None
    code = OVER_BUDGET if over else 1 if unknown else 0
    return {"kind": "budget", "over": over, "unknown": unknown, "budgets": rows}, code


def _entry(node: Node) -> dict:
    return {"path": node.path, "folder": node.is_dir, "bytes": node.size, "allocated_estimate_bytes": node.allocated,
            "modified": node.modified}


REPORTS: dict[str, tuple[str, Callable[[argparse.ArgumentParser], None], Report]] = {
    "search": ("find entries by name, size, age, type, owner and depth", add_search, report_search),
    "duplicates": ("list files with the same content", add_duplicates, report_duplicates),
    "cleanup": ("list clean-up candidates and their risk", add_cleanup, report_cleanup),
    "budget": ("check folders against size limits", add_budget, report_budget),
}


def check_arguments(args: argparse.Namespace) -> None:
    """Refuse unusable conditions, files and limits before scanning anything."""
    if args.command == "search":
        search_query(args)
    elif args.command == "cleanup":
        read_policy(args.policy)
    elif args.command == "budget":
        for path, limit in args.budget:
            BudgetRule("cli", 1, path, path, limit)
