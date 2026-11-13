"""The Free up space plan: ranked, bounded, counted once, never proposing what must stay (no Qt, no disk)."""

from __future__ import annotations

import pytest

from test_protected import WINDOWS_ENV
from je_file_tree.core.advice import LOW, PERSONAL, REVIEW, Adviser
from je_file_tree.core.cleanup import DETAILS, CleanupGroup
from je_file_tree.core.duplicates import DuplicateGroup
from je_file_tree.core.node import Node
from je_file_tree.core.protected import protected_places
from je_file_tree.core.reclaim import (CLEANUP, DUPLICATES, LARGE_FILES, LOOK_FACTOR, ReclaimSources, build_plan,
                                       free_share_target)

GB = 1024 ** 3


def _node(name: str, parent: Node | None = None, *, size: int = 0, is_dir: bool = False) -> Node:
    """A recorded entry; only a root keeps its whole path as its name. Folders add their files' sizes."""
    node = Node(name, is_dir, size=size, allocated=size, parent=parent, children=[] if is_dir else ())
    if parent is not None:
        parent.children.append(node)
        above: Node | None = parent
        while above is not None:
            above.size += size
            above.allocated += size
            above = above.parent
    return node


def _folder(name: str, parent: Node) -> Node:
    return _node(name, parent, is_dir=True)


def _group(key: str, nodes: list[Node]) -> CleanupGroup:
    return CleanupGroup(key, nodes, sum(node.size for node in nodes), DETAILS[key])


def _sources(root: Node, groups: list[CleanupGroup] | None = None, **kwargs) -> ReclaimSources:
    adviser = Adviser(protected_places("win32", WINDOWS_ENV), [] if groups is None else groups,
                      platform="win32", environ=WINDOWS_ENV)
    return ReclaimSources(root, adviser, tuple(groups or ()), **kwargs)


@pytest.fixture
def drive() -> dict[str, Node]:
    """A small C: drive with caches, dumps, duplicates, personal files and places that must stay."""
    root = _node("C:\\", is_dir=True)
    users = _folder("Users", root)
    me = _folder("me", users)
    local = _folder("Local", _folder("AppData", me))
    cache = _folder("Cache", _folder("Default", _folder("User Data", _folder("Chrome", _folder("Google", local)))))
    _node("data_1", cache, size=3 * GB)
    pip = _folder("Cache", _folder("pip", local))
    _node("wheel", pip, size=GB)
    work = _folder("work", me)
    dump = _node("crash.dmp", work, size=2 * GB)
    videos = _folder("Videos", me)
    movie = _node("holiday.mp4", videos, size=8 * GB)
    copy_a = _node("set.iso", videos, size=4 * GB)
    copy_b = _node("set.iso", work, size=4 * GB)
    program = _node("tool.exe", _folder("Tool", _folder("Program Files", root)), size=9 * GB)
    pagefile = _node("pagefile.sys", root, size=16 * GB)
    return {"root": root, "cache": cache, "pip": pip, "dump": dump, "movie": movie, "copy_a": copy_a,
            "copy_b": copy_b, "program": program, "pagefile": pagefile, "work": work}


def _full(drive: dict[str, Node], *, kept: Node | None = None) -> ReclaimSources:
    groups = [_group("browser_cache", [drive["cache"]]), _group("package_caches", [drive["pip"]]),
              _group("crash_dumps", [drive["dump"]])]
    duplicates = (DuplicateGroup(4 * GB, [drive["copy_a"], drive["copy_b"]], kept=kept),)
    largest = tuple(sorted((node for node in drive["root"].iter_files()), key=lambda node: -node.size))
    return _sources(drive["root"], groups, duplicates=duplicates, largest=largest)


def test_lower_risk_comes_first_then_review_then_your_call(drive) -> None:
    plan = build_plan(5 * GB, _full(drive, kept=drive["copy_a"]))
    assert [(step.category, step.key, step.risk) for step in plan.steps] == [
        (CLEANUP, "browser_cache", LOW), (CLEANUP, "package_caches", LOW),
        (DUPLICATES, DUPLICATES, REVIEW), (CLEANUP, "crash_dumps", REVIEW)]
    assert [step.total for step in plan.steps] == [3 * GB, 4 * GB, 8 * GB, 10 * GB]
    assert plan.reached and plan.shortfall == 0 and plan.total == 10 * GB
    assert [plan.needed(step) for step in plan.steps] == [True, True, True, False]
    assert plan.options is not None and plan.options.category == LARGE_FILES and plan.options.risk == PERSONAL
    assert [entry.node for entry in plan.options.entries] == [drive["movie"]]
    assert plan.options.total == 18 * GB, "the options continue the running total, apart from the steps"


def test_protected_managed_and_kept_copies_are_never_proposed(drive) -> None:
    plan = build_plan(100 * GB, _full(drive, kept=drive["copy_a"]))
    proposed = {entry.node for step in (*plan.steps, plan.options) for entry in step.entries}
    assert drive["program"] not in proposed and drive["pagefile"] not in proposed
    assert drive["copy_a"] not in proposed, "the copy the user keeps is not a large-file option either"
    assert drive["copy_b"] in proposed
    assert not plan.reached and plan.shortfall == 90 * GB


def test_a_protected_suggestion_is_left_out(drive) -> None:
    guarded = _folder("Cache", _folder("App", _folder("ProgramData", drive["root"])))
    _node("blob", guarded, size=GB)
    plan = build_plan(GB, _sources(drive["root"], [_group("browser_cache", [guarded, drive["cache"]])]))
    assert [entry.node for entry in plan.steps[0].entries] == [drive["cache"]]


def test_duplicates_without_a_chosen_copy_are_not_proposed(drive) -> None:
    plan = build_plan(GB, _full(drive))
    assert DUPLICATES not in {step.category for step in plan.steps}
    assert plan.undecided_duplicates == 1
    options = {entry.node for entry in plan.options.entries}
    assert {drive["copy_a"], drive["copy_b"]} <= options, "without a choice both copies are only your call"


def test_a_kept_copy_inside_a_suggestion_disables_its_group(drive) -> None:
    inside = _node("copy.bin", drive["cache"], size=GB)
    outside = _node("copy.bin", drive["work"], size=GB)
    groups = [_group("browser_cache", [drive["cache"]])]
    duplicates = (DuplicateGroup(GB, [inside, outside], kept=inside),)
    plan = build_plan(GB, _sources(drive["root"], groups, duplicates=duplicates))
    assert DUPLICATES not in {step.category for step in plan.steps}


def test_nothing_is_counted_twice_even_across_nested_folders(drive) -> None:
    project = _folder("project", drive["work"])
    build = _folder("build", project)
    inner = _folder("__pycache__", build)
    _node("module.pyc", inner, size=GB)
    _node("bundle.bin", build, size=2 * GB)
    copy = _node("asset.bin", build, size=GB)
    original = _node("asset.bin", drive["work"], size=GB)
    big_kept = _node("disk.vhd", drive["work"], size=10 * GB)
    big_extra = _node("disk.vhd", drive["movie"].parent, size=10 * GB)
    groups = [_group("browser_cache", [inner]), _group("build_output", [build, inner])]
    duplicates = (DuplicateGroup(10 * GB, [big_kept, big_extra], kept=big_kept),
                  DuplicateGroup(GB, [original, copy], kept=original))
    plan = build_plan(GB, _sources(drive["root"], groups, duplicates=duplicates))
    entries = [(step.key, entry.node.name, entry.size, entry.counted) for step in plan.steps for entry in step.entries]
    assert entries == [("browser_cache", "__pycache__", GB, GB), (DUPLICATES, "disk.vhd", 10 * GB, 10 * GB),
                       (DUPLICATES, "asset.bin", GB, GB), ("build_output", "build", 4 * GB, 2 * GB)], (
        "a folder counts only what earlier steps did not count; an entry inside a counted one is left out")
    assert plan.total == 14 * GB
    assert plan.size_of([build, inner, copy]) == 4 * GB, "a selection counts the outermost entries once"
    assert plan.size_of([inner, copy]) == 2 * GB


def test_a_folder_holding_a_counted_entry_ranked_first_takes_it_along(drive) -> None:
    build = _folder("build", _folder("project", drive["work"]))
    inner = _folder("__pycache__", build)
    _node("module.pyc", inner, size=GB)
    _node("bundle.bin", build, size=2 * GB)
    copy = _node("asset.bin", build, size=GB)
    original = _node("asset.bin", drive["work"], size=GB)
    groups = [_group("browser_cache", [inner]), _group("build_output", [build])]
    duplicates = (DuplicateGroup(GB, [original, copy], kept=original),)
    plan = build_plan(GB, _sources(drive["root"], groups, duplicates=duplicates))
    entries = [(step.key, entry.node.name, entry.size, entry.counted) for step in plan.steps for entry in step.entries]
    assert entries == [("browser_cache", "__pycache__", GB, GB), ("build_output", "build", 4 * GB, 3 * GB)]
    assert plan.total == 4 * GB == build.size, "the copy inside the folder is not offered again"


def test_a_large_file_already_in_a_step_is_not_an_option_again(drive) -> None:
    plan = build_plan(GB, _full(drive, kept=drive["copy_a"]))
    in_steps = {entry.node for step in plan.steps for entry in step.entries}
    assert not in_steps & {entry.node for entry in plan.options.entries}


def test_allocated_size_is_used_where_the_scan_measured_it(drive) -> None:
    drive["dump"].allocated = GB // 2  # a compressed file takes less than its size
    plan = build_plan(GB, _sources(drive["root"], [_group("crash_dumps", [drive["dump"]])]))
    assert plan.measured and plan.steps[0].entries[0].size == GB // 2
    root = _node("D:\\", is_dir=True)
    unmeasured = Node("file.bin", False, size=GB, parent=root)
    root.children.append(unmeasured)
    root.size = GB
    plan = build_plan(GB, _sources(root, largest=(unmeasured,)))
    assert not plan.measured and plan.options.entries[0].size == GB, "no allocation recorded: sizes count"


def test_steps_and_options_are_bounded(drive) -> None:
    folder = _folder("dumps", drive["work"])
    dumps = [_node(f"{index:03}.dmp", folder, size=index + 1) for index in range(50)]
    plan = build_plan(GB, _sources(drive["root"], [_group("crash_dumps", dumps)], largest=tuple(dumps)),
                      max_entries=10, max_options=0)
    step = plan.steps[0]
    assert len(step.entries) == 10 and step.more == 40
    assert [entry.node.name for entry in step.entries][:2] == ["049.dmp", "048.dmp"], "the largest first"
    assert step.size == sum(range(41, 51))
    assert plan.options is None
    program_files = _folder("Big", _folder("Program Files", drive["root"]))
    refused = [_node(f"{index}.dmp", program_files, size=GB) for index in range(LOOK_FACTOR)]
    plan = build_plan(GB, _sources(drive["root"], [_group("crash_dumps", [*refused, dumps[0]])]), max_entries=1)
    assert plan.steps == (), "a step looks at a bounded number of candidates, even when it finds none"
    plan = build_plan(GB, _sources(drive["root"], [_group("crash_dumps", [*refused, dumps[0]])]), max_entries=2)
    assert [entry.node for entry in plan.steps[0].entries] == [dumps[0]]


def test_an_unreachable_target_reports_the_shortfall_and_an_empty_plan_is_empty(drive) -> None:
    plan = build_plan(50 * GB, _sources(drive["root"], [_group("crash_dumps", [drive["dump"]])]))
    assert not plan.reached and plan.shortfall == 48 * GB
    empty = build_plan(GB, _sources(drive["root"]))
    assert empty.steps == () and empty.options is None and empty.total == 0 and not empty.reached
    assert build_plan(0, _sources(drive["root"])).reached


def test_pending_advice_proposes_no_personal_files(drive) -> None:
    waiting = Adviser(protected_places("win32", WINDOWS_ENV), None, platform="win32", environ=WINDOWS_ENV)
    sources = ReclaimSources(drive["root"], waiting, largest=(drive["movie"],))
    assert not sources.ready
    assert build_plan(GB, sources).options is None


def test_the_plan_is_deterministic_and_reads_no_disk(drive, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("os.lstat", lambda *_args, **_kwargs: pytest.fail("the plan queried storage"))
    monkeypatch.setattr("os.stat", lambda *_args, **_kwargs: pytest.fail("the plan queried storage"))
    sources = _full(drive, kept=drive["copy_b"])
    first, second = build_plan(7 * GB, sources), build_plan(7 * GB, sources)
    assert first == second
    detached = _node("gone.dmp", None, size=GB)
    plan = build_plan(GB, _sources(drive["root"], [_group("crash_dumps", [detached, drive["dump"]])]))
    assert [entry.node for entry in plan.steps[0].entries] == [drive["dump"]], "only entries of this scan"


def test_free_share_target() -> None:
    assert free_share_target(20, 100 * GB, 5 * GB) == 15 * GB
    assert free_share_target(10, 100 * GB, 50 * GB) == 0
    assert free_share_target(150, 10, 0) == 10
