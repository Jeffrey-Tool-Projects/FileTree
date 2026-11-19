"""Background work gives way to the window: the gate the workers wait at."""

from __future__ import annotations

import inspect
import math
import sys
import threading
import time

import pytest

from je_file_tree.core import cleanup, pacing, scanner
from je_file_tree.core.node import PACE_EVERY, Node, outermost
from je_file_tree.core.pacing import Gate


def _timed_give_way(gate: Gate) -> float:
    """How long ``give_way`` took on another thread."""
    took: list[float] = []

    def work() -> None:
        started = time.perf_counter()
        gate.give_way()
        took.append(time.perf_counter() - started)

    thread = threading.Thread(target=work)
    thread.start()
    thread.join(5)
    return took[0]


def test_an_open_gate_lets_workers_through_at_once() -> None:
    gate = Gate()
    assert gate.is_open
    assert _timed_give_way(gate) < 0.01


def test_a_closed_gate_holds_workers_but_never_longer_than_the_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pacing, "PAUSE_LIMIT", 0.2)
    gate = Gate()
    gate.close()
    took = _timed_give_way(gate)
    assert 0.15 <= took < 1.0, "held while the window is busy, then one more step: nothing hangs on it"


def test_opening_the_gate_lets_a_waiting_worker_go_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pacing, "PAUSE_LIMIT", 5.0)
    gate = Gate()
    gate.close()
    threading.Timer(0.05, gate.open).start()
    assert _timed_give_way(gate) < 1.0


def test_the_thread_that_closed_the_gate_never_waits_at_it(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pacing, "PAUSE_LIMIT", 5.0)
    gate = Gate()
    gate.close()
    started = time.perf_counter()
    gate.give_way()  # the window running core code itself (a synchronous scan, say) must not stall
    assert time.perf_counter() - started < 0.1


def _chain(count: int) -> Node:
    """A root holding ``count`` empty folders, each also holding an empty folder."""
    root = Node("root", True, children=[])
    for number in range(count):
        outer = Node(f"outer-{number}", True, children=[], parent=root)
        outer.children.append(Node("inner", True, children=[], parent=outer))
        root.children.append(outer)
    return root


def test_outermost_paces_both_of_its_passes():
    root = _chain(600)
    nodes = [*root.children, *(child.children[0] for child in root.children)]
    paced = []
    kept = outermost(nodes, pace=lambda: paced.append(1))
    assert kept == root.children, "pacing never changes the answer"
    assert len(paced) == 2 * math.ceil(len(nodes) / PACE_EVERY), "every PACE_EVERY entries, in each pass"
    assert outermost(nodes) == kept


def test_empty_folders_gives_way_in_every_pass(monkeypatch):
    root = _chain(600)
    callers: set[tuple[str, int]] = set()
    monkeypatch.setattr(cleanup, "give_way", lambda: callers.add((sys._getframe(1).f_code.co_name,
                                                                   sys._getframe(1).f_lineno)))
    found = cleanup.empty_folders(root)
    assert len(found) == 600 and {id(node) for node in found} == {id(node) for node in root.children}
    assert ("outermost", _line_of(outermost, "pace()", 1)) in callers
    assert ("outermost", _line_of(outermost, "pace()", 2)) in callers
    lines = {line for name, line in callers if name == "empty_folders"}
    assert len(lines) == 2, "the walk and the emptiness pass: unpaced, they held the window 0.3 s"


def _line_of(function, text: str, occurrence: int) -> int:
    lines, first = inspect.getsourcelines(function)
    found = [first + offset for offset, line in enumerate(lines) if line.strip() == text]
    return found[occurrence - 1]


def _flat(count: int) -> Node:
    """A folder of ``count`` files with repeated sizes and names differing in case: ties must keep the order."""
    folder = Node("flat", True, children=[])
    folder.children.extend(Node(f"{'F' if number % 3 else 'f'}ile-{number % 50}", False, size=number % 7,
                                allocated=number, file_count=1, modified=float(number), parent=folder)
                           for number in range(count))
    return folder


@pytest.mark.parametrize("count", [3, PACE_EVERY, PACE_EVERY + 1, 1000])
def test_a_large_folder_is_added_up_and_sorted_a_page_at_a_time(monkeypatch, count):
    folder = _flat(count)
    expected = sorted(folder.children, key=scanner._size_first)
    paced = []
    monkeypatch.setattr(scanner, "give_way", lambda: paced.append(1))
    scanner._add_up([folder])
    assert [id(child) for child in folder.children] == [id(child) for child in expected], "the same order as before"
    assert folder.size == sum(number % 7 for number in range(count)) and folder.file_count == count
    assert folder.allocated == sum(range(count)) and folder.modified == float(count - 1)
    pages = math.ceil(count / PACE_EVERY)
    # one per folder, one between pages of the totals, one per page of sort keys
    assert len(paced) == (2 * pages if count > PACE_EVERY else 1), "41,610 entries took 42 ms in one go"


def test_matching_a_large_folder_gives_way_between_pages(monkeypatch):
    folder = _flat(1000)
    folder.name = "C:\flat"  # an absolute path: a root the clean-up rules can look into
    paced = []
    monkeypatch.setattr(cleanup, "give_way", lambda: paced.append(1))
    cleanup._visit(folder, (folder.name.casefold(),), cleanup._Matcher(cleanup.RULES, time.time()),
                   {}, cleanup.coverage_of(folder), set(), set())
    assert len(paced) == (1000 - 1) // PACE_EVERY, "one folder's 41,610 files took 100 ms to match"
