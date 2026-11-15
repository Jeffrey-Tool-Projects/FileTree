"""Only a directory listing may say "recall on open"; a path query's copy of that bit is not believed.

Found on a real system volume (2026-11-14): ``os.lstat`` of Python 3.12 and newer reports attribute
0x40000 for ordinary files nobody has opened yet, and the scan counted them as taking no space.
"""

from __future__ import annotations

import os
import sys
from types import SimpleNamespace

import pytest

from je_file_tree.core import native_scan, scanner
from je_file_tree.core.snapshot import RECALL_ON_OPEN, pack_snapshot, path_metadata, stat_snapshot, unpack_snapshot

_ARCHIVE = 0x20
_windows = pytest.mark.skipif(sys.platform != "win32", reason="Windows file attributes")


def _with_attributes(info: os.stat_result, attributes: int) -> SimpleNamespace:
    copy = SimpleNamespace(**{name: getattr(info, name) for name in dir(info) if name.startswith("st_")})
    copy.st_file_attributes = attributes
    return copy


def _claiming_recall(monkeypatch: pytest.MonkeyPatch, suffix: str) -> None:
    """Make ``os.lstat`` report the bit for paths ending in ``suffix``, as a query by name does."""
    real = os.lstat

    def lstat(path, *args, **kwargs):
        info = real(path, *args, **kwargs)
        if os.fspath(path).endswith(suffix):
            return _with_attributes(info, getattr(info, "st_file_attributes", 0) | RECALL_ON_OPEN)
        return info

    monkeypatch.setattr(os, "lstat", lstat)


def test_a_path_query_alone_cannot_set_the_bit_and_a_listing_can(tmp_path) -> None:
    info = os.lstat(tmp_path)
    assert path_metadata(info) is info  # nothing to change: no copy
    claimed = _with_attributes(info, _ARCHIVE | RECALL_ON_OPEN)
    assert path_metadata(claimed).st_file_attributes == _ARCHIVE
    assert path_metadata(claimed, RECALL_ON_OPEN).st_file_attributes == _ARCHIVE | RECALL_ON_OPEN
    plain = _with_attributes(info, _ARCHIVE)
    confirmed = path_metadata(plain, 0xFFFFFFFF)  # only this one bit is taken from the listing
    assert confirmed.st_file_attributes == _ARCHIVE | RECALL_ON_OPEN
    assert confirmed.st_size == info.st_size and confirmed.st_mtime_ns == info.st_mtime_ns
    assert pack_snapshot(path_metadata(claimed)) == pack_snapshot(plain)
    # A file with no attribute of its own is "normal" to its listing and to a query by handle.
    assert path_metadata(_with_attributes(info, RECALL_ON_OPEN)).st_file_attributes == 0x80


def test_the_file_tables_index_flags_are_never_recorded(tmp_path) -> None:
    info = os.lstat(tmp_path)
    folder = 0x10  # what a listing and a later query report for a new empty folder
    for flags in (0x10000000, 0x20000000, 0x30000000):
        reported = _with_attributes(info, folder | flags)
        assert path_metadata(reported).st_file_attributes == folder
        assert pack_snapshot(path_metadata(reported)) == pack_snapshot(_with_attributes(info, folder))


@_windows
def test_an_empty_folder_scanned_just_after_it_was_made_is_not_changed(tmp_path, monkeypatch) -> None:
    from je_file_tree.core import operations

    (tmp_path / "empty").mkdir()
    real = os.lstat

    def lstat(path, *args, **kwargs):  # what a query by name reports until something lists the folder
        info = real(path, *args, **kwargs)
        if os.fspath(path).endswith("empty") and scanning:
            return _with_attributes(info, info.st_file_attributes | 0x10000000)
        return info

    scanning = True
    monkeypatch.setattr(os, "lstat", lstat)
    monkeypatch.setenv(native_scan.DISABLE_VARIABLE, "0")  # the Python reader, which asks os.lstat
    root = scanner.scan(tmp_path).root
    scanning = False
    assert not unpack_snapshot(root.children[0].snapshot).attributes & 0x10000000
    assert operations.validate_tree(root) is None  # observed only; nothing is moved here


@_windows  # elsewhere a file has no attributes for the bit to join
def test_a_snapshot_of_one_path_never_carries_the_bit(tmp_path, monkeypatch) -> None:
    target = tmp_path / "file.bin"
    target.write_bytes(b"data")
    before = stat_snapshot(str(target))
    _claiming_recall(monkeypatch, "file.bin")
    assert stat_snapshot(str(target)) == before  # a later check must not call this file changed


@_windows
def test_the_python_reader_counts_the_space_of_a_file_whose_path_query_claims_recall(tmp_path, monkeypatch) -> None:
    (tmp_path / "plain.bin").write_bytes(b"x" * 5000)
    _claiming_recall(monkeypatch, "plain.bin")
    node = scanner.scan(tmp_path).root.children[0]
    assert node.size == 5000 and node.allocated >= 5000
    assert not unpack_snapshot(node.snapshot).attributes & RECALL_ON_OPEN


@_windows
def test_the_native_rows_keep_only_the_bit_of_the_listing(tmp_path, monkeypatch) -> None:
    for name in ("listed.bin", "plain.bin"):
        (tmp_path / name).write_bytes(b"x" * 5000)
    rows = [
        # The module reports the listing's bit; such a file goes to the Python code as unusual.
        ("listed.bin", native_scan.KIND_FILE, 5000, 0.0, b"", _ARCHIVE | RECALL_ON_OPEN),
        # An entry the module could not describe carries nothing but the listing's bit: none here.
        ("plain.bin", native_scan.KIND_ASK_PYTHON, 0, 0.0, b"", 0),
    ]
    monkeypatch.setattr(native_scan, "reader", lambda: lambda _path, _times: rows)
    monkeypatch.setattr(native_scan, "agrees_on", lambda _path: True)
    _claiming_recall(monkeypatch, "plain.bin")
    nodes = {node.name: node for node in scanner.scan(tmp_path).root.children}
    assert nodes["listed.bin"].allocated == 0  # really elsewhere: the listing said so
    assert unpack_snapshot(nodes["listed.bin"].snapshot).attributes & RECALL_ON_OPEN
    assert nodes["plain.bin"].allocated >= 5000
    assert not unpack_snapshot(nodes["plain.bin"].snapshot).attributes & RECALL_ON_OPEN


@_windows
def test_the_check_before_a_permanent_delete_does_not_call_such_a_file_changed(tmp_path, monkeypatch) -> None:
    from je_file_tree.core import permanent_delete

    target = tmp_path / "file.bin"
    target.write_bytes(b"data")
    recorded = unpack_snapshot(stat_snapshot(str(target)))
    _claiming_recall(monkeypatch, "file.bin")
    assert permanent_delete._observe(str(target)) == recorded  # observed only; nothing is deleted here


def test_no_core_module_records_the_attributes_of_a_bare_path_query() -> None:
    # ``path_metadata`` / ``stat_snapshot`` are the places that know which attribute not to believe.
    import re
    from pathlib import Path

    core = Path(__file__).resolve().parents[1] / "je_file_tree" / "core"
    direct = re.compile(r"pack_snapshot\((os\.lstat|[a-z_.]+\.lstat)\(")
    found = [f"{path.name}:{number}" for path in sorted(core.glob("*.py"))
             for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
             if direct.search(line) and "``" not in line and path.name not in ("finder_bin.py", "bin_empty.py")]
    assert found == []  # the two exempt modules read macOS and freedesktop bins, which have no such attribute
