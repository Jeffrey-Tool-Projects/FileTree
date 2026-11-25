"""Defects a review of the core found on 2026-11-26; each test failed before its fix."""

import ctypes
import json
import os
import plistlib
import stat
import sys
import threading
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from conftest import make_tree
from je_file_tree.core import (
    bin_empty,
    disks,
    duplicate_link_ops,
    duplicate_links,
    duplicates,
    forecast,
    recurring,
    trash_restore,
)
from je_file_tree.core import operation_journal as journal_module
from je_file_tree.core.cleanup import EMPTY_FOLDERS, find_cleanup
from je_file_tree.core.cleanup_policy import CleanupPolicy, RuleSetting
from je_file_tree.core.compare import load_saved
from je_file_tree.core.coverage import coverage_of
from je_file_tree.core.duplicate_decisions import check_group
from je_file_tree.core.duplicates import DuplicateSearchCancelledError, find_duplicates
from je_file_tree.core.export import export_json
from je_file_tree.core.folder_budgets import BudgetRule, BudgetTicket, observe_budgets
from je_file_tree.core.mounts import parse_mountinfo
from je_file_tree.core.multi_scan import scan_roots
from je_file_tree.core.node import Node
from je_file_tree.core.operation_journal import OperationJournal, OperationOutcome, OperationRecord, export_journal
from je_file_tree.core.scanner import ScanOptions, scan
from je_file_tree.core.search import Query, search
from je_file_tree.core.snapshot import Snapshot, renamed
from je_file_tree.core.trash_restore import TrashOrigin

ON_WINDOWS = sys.platform == "win32"
LONE = "lone\ud800x"


def _attributes(path, value):
    assert ctypes.windll.kernel32.SetFileAttributesW(str(path), value)


def _folder_link(link, target):
    if ON_WINDOWS:
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(target, link, target_is_directory=True)


# --- the archive attribute of renamed files ---------------------------------------------------------------


def test_only_the_change_time_and_the_archive_bit_may_differ_after_a_rename():
    before = Snapshot(1, 2, 3, 4, 5, stat.S_IFREG, 0x80, 1)
    after = Snapshot(1, 2, 3, 4, 99, stat.S_IFREG, 0x20, 1)
    assert renamed(before, after) and renamed(after, before)
    assert not renamed(before, Snapshot(1, 2, 3, 4, 99, stat.S_IFREG, 0x21, 1))  # read-only now
    assert not renamed(before, Snapshot(1, 2, 3, 5, 99, stat.S_IFREG, 0x20, 1))
    assert not renamed(before, Snapshot(1, 9, 3, 4, 99, stat.S_IFREG, 0x20, 1))


@pytest.mark.skipif(not ON_WINDOWS, reason="the archive attribute")
@pytest.mark.parametrize("keeper, copy", [(0x20, 0x80), (0x80, 0x20), (0x80, 0x80)])
def test_copies_without_the_archive_bit_are_linked(tmp_path, keeper, copy):
    folder = tmp_path.resolve() / "scan"
    folder.mkdir()
    for name, attributes in (("a.bin", keeper), ("b.bin", copy)):
        (folder / name).write_bytes(b"the same content")
        _attributes(folder / name, attributes)
    root = scan(folder).root
    group = find_duplicates(root, min_size=1).groups[0]
    group = replace(group, kept=next(node for node in group.files if node.name == "a.bin"))
    result = duplicate_link_ops.execute_links(duplicate_links.prepare_links(root, [group]))
    assert [(outcome.linked, outcome.error) for outcome in result.outcomes] == [(True, "")]
    assert sorted(os.listdir(folder)) == ["a.bin", "b.bin"] and os.stat(folder / "b.bin").st_nlink == 2


@pytest.mark.skipif(not ON_WINDOWS, reason="the archive attribute")
def test_a_failed_link_gives_the_copy_its_name_back(tmp_path, monkeypatch):
    folder = tmp_path.resolve() / "scan"
    folder.mkdir()
    for name in ("a.bin", "b.bin"):
        (folder / name).write_bytes(b"the same content")
    root = scan(folder).root
    group = find_duplicates(root, min_size=1).groups[0]
    group = replace(group, kept=next(node for node in group.files if node.name == "a.bin"))
    plan = duplicate_links.prepare_links(root, [group])
    native = duplicate_link_ops.rename_no_replace

    def rename(source, target, old, new):
        native(source, target, old, new)
        if target.endswith(".bak"):
            _attributes(target, 0x22)  # something else changed it meanwhile

    monkeypatch.setattr(duplicate_link_ops, "rename_no_replace", rename)
    outcome = duplicate_link_ops.execute_links(plan).outcomes[0]
    assert not outcome.linked and outcome.error and not outcome.retained
    assert sorted(os.listdir(folder)) == ["a.bin", "b.bin"]


# --- removal and its journal ------------------------------------------------------------------------------


def test_a_cancelled_undo_capture_is_an_error_the_worker_expects(monkeypatch, tmp_path):
    def cancelled(*_args):
        raise bin_empty.BinSurveyCancelledError

    class Anchor:
        def __enter__(self):
            return 3

        def __exit__(self, *_args):
            return False

    payload = tmp_path / "Trash" / "files" / "x"
    origin = TrashOrigin(str(tmp_path / "x"), b"", ())
    monkeypatch.setattr(trash_restore.bin_empty, "_volume", lambda _root: tmp_path)
    monkeypatch.setattr(trash_restore.bin_empty, "_candidates", lambda _root: [payload.parent.parent])
    monkeypatch.setattr(trash_restore, "directory_stamps", lambda _path: (1, 2))
    monkeypatch.setattr(trash_restore, "anchored_directory", lambda _chain: Anchor())
    monkeypatch.setattr(trash_restore, "descriptor_mount", lambda _fd: 1)
    monkeypatch.setattr(trash_restore, "_scope", lambda *_args: None)
    monkeypatch.setattr(trash_restore, "_receipt", lambda *_args: (None, origin.path))
    monkeypatch.setattr(trash_restore, "_inventory", cancelled)
    with pytest.raises(InterruptedError):
        trash_restore.prepare_restore(origin, str(payload), str(tmp_path))


def _record(path):
    node = Node(str(path), False, size=1)
    return OperationRecord.approved("batch", node, "manual")


def test_names_that_are_not_text_are_recorded_and_exported(tmp_path):
    journal = OperationJournal(tmp_path / "journal")
    record = _record(tmp_path / LONE)
    journal.append([record, record.finished(OperationOutcome("moved", destination="/bin/" + LONE))])
    read = journal.recent()
    assert read.invalid == 0 and [row.source for row in read.records] == [record.source]
    assert read.records[0].outcome.destination == "/bin/" + LONE
    assert export_journal(read.records, tmp_path / "actions.csv") == 1


def test_reading_the_journal_never_fails_a_write(tmp_path, monkeypatch):
    journal = OperationJournal(tmp_path / "journal")
    journal.append([_record(tmp_path / "first")])
    segment = next((tmp_path / "journal").glob("actions-*.jsonl"))
    reading = threading.Event()

    def hold():
        with segment.open("rb"):
            reading.set()
            time.sleep(.4)

    thread = threading.Thread(target=hold)
    thread.start()
    reading.wait(5)
    journal.append([_record(tmp_path / "second")])  # Windows refuses to replace the segment while it is read
    thread.join()
    assert len(journal.recent().records) == 2
    monkeypatch.setattr(journal_module, "_LOCK_SECONDS", 0)

    def refuse(*_args):
        raise PermissionError("held")

    monkeypatch.setattr(journal_module.os, "replace", refuse)
    with pytest.raises(PermissionError):
        journal.append([_record(tmp_path / "third")])


def test_an_old_segment_in_use_does_not_fail_the_append(tmp_path, monkeypatch):
    journal = OperationJournal(tmp_path / "journal", days=1)
    journal.append([_record(tmp_path / "first")])
    segment = next((tmp_path / "journal").glob("actions-*.jsonl"))
    old = segment.with_name("actions-20200101" + segment.name[16:])
    segment.rename(old)
    os.utime(old, (1, 1))

    def refuse(*_args, **_options):
        raise PermissionError("held")

    monkeypatch.setattr(type(old), "unlink", refuse)
    journal.append([_record(tmp_path / "second")])
    assert old.exists() and len(journal.recent().records) == 2


def test_folder_names_that_are_not_text_are_exported_and_read_back(tmp_path):
    root = Node(str(tmp_path), True, children=[])
    root.children.append(Node(LONE, True, parent=root, children=[], size=5))
    target = tmp_path / "scan.json"
    export_json(root, target)
    assert json.loads(target.read_text(encoding="utf-8"))["root"]["children"][0]["name"] == LONE
    assert load_saved(target)


# --- clean-up, duplicates, search ---------------------------------------------------------------------------


def test_an_empty_folder_a_rule_names_is_proposed_once(tmp_path):
    root = tmp_path / "scan"
    make_tree(root.parent, {"scan": {"AppData": {"Local": {"CrashDumps": {}, "kept": b"x"}}}})
    policy = CleanupPolicy((RuleSetting("crash_dumps", True, 0), RuleSetting(EMPTY_FOLDERS, True, 0)))
    for folder in sorted(root.rglob("*"), reverse=True):
        os.utime(folder, (time.time() - 60,) * 2)
    scanned = scan(root).root
    paths = [node.path for group in find_cleanup(scanned, policy=policy) for node in group.nodes]
    assert len(paths) == len(set(paths))
    assert recurring.capture(scanned, policy, time.time()).candidate_count == len(paths)


def test_captured_file_times_do_not_make_every_copy_look_changed(tmp_path):
    for name in ("a", "b"):
        (tmp_path / name).write_bytes(b"same content here")
    root = scan(tmp_path, options=ScanOptions(file_times=True)).root
    group = find_duplicates(root, min_size=1).groups[0]
    group = replace(group, kept=group.files[0])
    assert check_group(group, root, places=()) is None


def test_the_duplicate_search_gives_way_and_stops_while_it_collects(tmp_path, monkeypatch):
    for name in ("a", "b", "c"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "file").write_bytes(b"x" * 10)
    root = scan(tmp_path).root
    steps = []
    monkeypatch.setattr(duplicates, "give_way", lambda: steps.append(1))
    assert len(duplicates._by_size(root, 1, None)[10]) == 3 and len(steps) == 4
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(DuplicateSearchCancelledError):
        duplicates._by_size(root, 1, cancel)


def test_a_search_of_several_folders_does_not_judge_them_by_their_paths(tmp_path):
    for name in ("temp1", "temp2"):
        make_tree(tmp_path, {name: {"film.mkv": b"x" * 5, "temp": {"other.mkv": b"x"}}})
    root = scan_roots([tmp_path / "temp1", tmp_path / "temp2"]).root
    found = search(root, Query(text="*.mkv", exclude="temp"))
    assert sorted(node.name for node in found.matches) == ["film.mkv", "film.mkv"]
    assert [node.name for node in search(root, "temp").matches] == ["temp", "temp"]


# --- several roots ------------------------------------------------------------------------------------------


def test_a_root_behind_a_link_is_scanned_too(tmp_path):
    make_tree(tmp_path, {"a": {"x": b"1"}, "elsewhere": {"sub": {"file": b"x" * 1000}}})
    _folder_link(tmp_path / "a" / "j", tmp_path / "elsewhere")
    result = scan_roots([tmp_path / "a", tmp_path / "a" / "j" / "sub"])
    assert len(result.root.children) == 2 and result.root.size == 1001


@pytest.mark.parametrize("options", [ScanOptions(exclude=("sub",)), ScanOptions(include_hidden=False)])
def test_a_root_the_outer_scan_skips_is_scanned_too(tmp_path, options):
    name = "sub" if options.exclude else ".sub"
    make_tree(tmp_path, {"b": {name: {"file": b"x" * 1000}}})
    assert scan_roots([tmp_path / "b", tmp_path / "b" / name], options=options).root.size == 1000
    assert len(scan_roots([tmp_path / "b", tmp_path / "b" / name]).root.children) == 1


def test_two_budgets_of_one_folder_are_both_measured(tmp_path):
    (tmp_path / "file").write_bytes(b"x" * 10)
    root = scan(tmp_path).root
    rules = tuple(BudgetRule(f"rule-{number}", 1, "name", str(tmp_path), 100 + number) for number in range(2))
    batch = observe_budgets(root, coverage_of(root), BudgetTicket(1, rules), time.time())
    assert sorted((row.identity, row.bytes) for row in batch.observations) == [("rule-0", 10), ("rule-1", 10)]


# --- damaged or unusual outside data --------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["\u6211\u7684\u3000\u786c\u789f", "a\u00a0b", "a\u0085b", "a\u2028b", "a\x0cb"])
def test_mount_names_keep_unicode_whitespace(name):
    line = f"36 35 98:0 / /media/u/{name} rw,noatime master:1 - ext3 /dev/root rw\n"
    assert f"/media/u/{name}" in {point.replace("\\", "/") for point in parse_mountinfo(line)}


def test_a_damaged_property_list_is_a_value_error():
    whole = plistlib.dumps({"a": 1})
    for data in (whole[:-20], whole.replace(b"<integer>1</integer>", b"<date>never</date>"), b"<?xml"):
        with pytest.raises(ValueError):
            disks._plist(data)


@pytest.mark.parametrize("when", [10 ** 400, float("inf"), float("nan"), -1, True, "1"])
def test_impossible_forecast_times_are_no_samples(when):
    assert forecast._sample([when, 1, 2]) is None


def test_a_decoder_that_fails_in_its_own_way_skips_the_picture(tmp_path, monkeypatch):
    from je_file_tree import photo_reader

    for name in ("a.avif", "b.png"):
        (tmp_path / name).write_bytes(b"x" * 100)
    errors = iter((RuntimeError("Missing or empty image item"), SyntaxError("not a TIFF file")))

    def fail(*_args, **_options):
        raise next(errors)

    monkeypatch.setattr(photo_reader.Image, "open", fail)
    result = photo_reader.find_similar_photos(scan(tmp_path).root, min_size=1)
    assert result.skipped == 2 and not result.groups


def test_a_malformed_trash_receipt_is_an_os_error(monkeypatch, tmp_path):
    receipt = Path(tmp_path / "x.trashinfo")
    receipt.write_text("no section\n", encoding="utf-8")
    info = os.lstat(receipt)
    monkeypatch.setattr(bin_empty.os, "getuid", lambda: info.st_uid, raising=False)
    for flag in ("O_NOFOLLOW", "O_NONBLOCK"):
        monkeypatch.setattr(bin_empty.os, flag, 0, raising=False)
    real_open, real_stat = os.open, os.stat
    monkeypatch.setattr(bin_empty, "os", SimpleNamespace(**{name: getattr(os, name) for name in dir(os)
                                                            if not name.startswith("__")}))
    monkeypatch.setattr(bin_empty.os, "stat", lambda *_args, **_options: real_stat(receipt))
    monkeypatch.setattr(bin_empty.os, "open", lambda *_args, **_options: real_open(receipt, os.O_RDONLY))
    monkeypatch.setattr(bin_empty, "pack_snapshot", lambda _info: b"")
    with pytest.raises(OSError, match="Unrecognized"):
        bin_empty._receipt(3, "x.trashinfo")
