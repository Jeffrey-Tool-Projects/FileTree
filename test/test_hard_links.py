"""Once-per-identity accounting preserves named file sizes, observations and deterministic ownership."""

import os
import threading

import pytest

from je_file_tree.core.hard_links import account_hard_links, plan_hard_links
from je_file_tree.core.node import detach_many
from je_file_tree.core.scanner import ScanOptions, scan
from je_file_tree.core.snapshot import pack_snapshot


def _fixture(tmp_path):
    (tmp_path / "z").mkdir()
    (tmp_path / "a").mkdir()
    first, second = tmp_path / "z" / "first.log", tmp_path / "a" / "second.log"
    first.write_bytes(b"owned" * 1024)
    os.link(first, second)
    return first, second


def test_recorded_hard_links_keep_actual_lengths_and_count_in_lexical_folder(tmp_path):
    _fixture(tmp_path)
    result = scan(tmp_path, options=ScanOptions(count_hard_links=True))
    nodes = sorted(result.root.iter_files(), key=lambda node: node.path)
    size, allocation = nodes[0].size, nodes[0].allocated
    assert [node.size for node in nodes] == [5120, 5120]
    assert [node.accounted_size for node in nodes] == [5120, 0]
    assert [node.accounted_allocated for node in nodes] == [allocation, 0]
    assert result.root.size == 2 * size and result.root.accounted_size == size
    assert result.root.allocated == 2 * allocation and result.root.accounted_allocated == allocation
    assert result.root.file_count == 2 and result.hard_links.aliases == 1
    assert result.hard_links.logical_overcount == size and result.hard_links.unknown == 0
    assert next(node for node in result.root.children if node.name == "z").accounted_size == 0
    assert scan(tmp_path).hard_links is None
    assert all(node.accounting is None for node in scan(tmp_path).root.iter_nodes())


def test_survey_uses_no_new_os_queries_and_cancel_keeps_existing_accounting(tmp_path, monkeypatch):
    _fixture(tmp_path)
    root = scan(tmp_path).root
    originals = {node: (node.size, node.allocated, node.snapshot) for node in root.iter_nodes()}
    monkeypatch.setattr(os, "lstat", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("new stat")))
    first = account_hard_links(root)
    assert first.aliases == 1
    assert originals == {node: (node.size, node.allocated, node.snapshot) for node in root.iter_nodes()}
    values = {node: node.accounting for node in root.iter_nodes()}
    event = threading.Event()
    event.set()
    assert account_hard_links(root, cancel=event) is None
    assert values == {node: node.accounting for node in root.iter_nodes()}
    assert account_hard_links(root) == first


def test_inconsistent_and_unknown_records_are_not_deduplicated(tmp_path):
    _fixture(tmp_path)
    root = scan(tmp_path).root
    files = list(root.iter_files())
    files[0].allocated += 4096
    outcome = account_hard_links(root)
    assert outcome.aliases == 0 and outcome.unknown == 2
    assert root.accounted_size == root.size
    files[1].snapshot = None
    assert account_hard_links(root).unknown == 1


def test_reaccount_after_detach_transfers_contribution_to_remaining_name(tmp_path):
    _fixture(tmp_path)
    root = scan(tmp_path, options=ScanOptions(count_hard_links=True)).root
    kept = next(node for node in root.iter_files() if node.accounted_size > 0)
    kept.detach()
    assert account_hard_links(root).aliases == 0
    remaining = list(root.iter_files())
    assert len(remaining) == 1 and remaining[0].accounted_size == 5120
    assert root.accounted_size == root.size == 5120


def test_identity_in_another_device_is_never_merged(tmp_path):
    _fixture(tmp_path)
    root = scan(tmp_path).root
    node = next(root.iter_files())
    info = os.lstat(node.path)
    from types import SimpleNamespace
    fake = SimpleNamespace(**{key: getattr(info, key) for key in
                             ("st_mode", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")})
    fake.st_dev = info.st_dev + 1
    fake.st_file_attributes = getattr(info, "st_file_attributes", 0)
    node.snapshot = pack_snapshot(fake)
    assert account_hard_links(root).aliases == 0


def _counted(tmp_path):
    (tmp_path / "z" / "deep").mkdir(parents=True)
    (tmp_path / "a").mkdir()
    (tmp_path / "solo.bin").write_bytes(b"s" * 300)
    first = tmp_path / "z" / "deep" / "first.log"
    first.write_bytes(b"owned" * 1024)
    os.link(first, tmp_path / "a" / "second.log")
    os.link(first, tmp_path / "a" / "third.log")
    return scan(tmp_path, options=ScanOptions(count_hard_links=True)).root


def _values(root):
    return {node.path: (node.size, node.allocated, node.accounting) for node in root.iter_nodes()}


@pytest.mark.parametrize("removed", [["a/second.log"], ["z"], ["a/second.log", "a/third.log"], ["a", "solo.bin"]])
def test_a_plan_without_entries_matches_counting_again_after_detaching_them(tmp_path, removed):
    planned_root, counted_root = _counted(tmp_path / "planned"), _counted(tmp_path / "counted")

    def pick(root):
        return [next(node for node in root.iter_nodes() if node.path == os.path.join(root.path, *name.split("/")))
                for name in removed]

    before = _values(planned_root)
    plan = plan_hard_links(planned_root, without=pick(planned_root))
    assert _values(planned_root) == before  # planning reads the tree only
    plan.apply()
    detach_many(pick(planned_root))
    detach_many(pick(counted_root))
    expected = account_hard_links(counted_root)

    def relative(root):
        return {os.path.relpath(path, root.path): value for path, value in _values(root).items()}

    assert plan.accounting == expected and relative(planned_root) == relative(counted_root)
    assert planned_root.accounted_size == counted_root.accounted_size


def test_a_canceled_plan_changes_nothing(tmp_path):
    root = _counted(tmp_path)
    event = threading.Event()
    event.set()
    assert plan_hard_links(root, cancel=event) is None
    assert plan_hard_links(root).changes == ()  # counted already: nothing to change
