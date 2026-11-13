"""The native folder reader records exactly what the Python scanner records, or is not used."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from je_file_tree.core import native_scan, scanner
from je_file_tree.core.node import Node
from je_file_tree.core.scanner import ScanOptions, scan
from je_file_tree.core.snapshot import pack_snapshot

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="the native reader is built on Windows only")


@pytest.fixture
def native():
    """The calibrated reader, or skip where the module was not built or does not agree with os.lstat."""
    native_scan.reset()
    read = native_scan.reader()
    if read is None:
        pytest.skip("je_file_tree._native is not built here (python setup.py build_ext --inplace)")
    yield read
    native_scan.reset()


@pytest.fixture
def made_up(tmp_path: Path) -> Path:
    """A folder with the kinds of entry a scan meets; everything is created here."""
    root = tmp_path / "scan"
    (root / "plain" / "deep" / "deeper").mkdir(parents=True)
    (root / "empty").mkdir()
    (root / "檔案 資料夾").mkdir()
    (root / ".dotfolder").mkdir()
    (root / "plain" / "a.txt").write_bytes(b"a" * 10)
    (root / "plain" / "zero.bin").write_bytes(b"")
    (root / "plain" / "deep" / "big.bin").write_bytes(b"b" * 70_000)
    (root / "plain" / "deep" / "deeper" / "x.log").write_bytes(b"x" * 4096)
    (root / "檔案 資料夾" / "名稱 with space.txt").write_bytes(b"u" * 33)
    (root / ".dotfile").write_bytes(b"d")
    (root / ".dotfolder" / "inside.txt").write_bytes(b"i" * 5)
    read_only = root / "plain" / "read-only.txt"
    read_only.write_bytes(b"r" * 3)
    read_only.chmod(0o444)
    hidden = root / "plain" / "hidden.txt"
    hidden.write_bytes(b"h" * 7)
    subprocess.run(["attrib", "+h", str(hidden)], check=True)  # noqa: S603, S607 - fixed system tool on a fixture
    os.link(root / "plain" / "a.txt", root / "plain" / "a-hard-link.txt")
    os.utime(root / "plain" / "a.txt", ns=(1_600_000_000_123_456_700, 1_500_000_000_987_654_300))
    yield root
    read_only.chmod(0o666)


def _flat(root: Node) -> list[tuple]:
    rows = []
    for node in root.iter_nodes():
        rows.append((node.path, node.is_dir, node.is_link, node.size, node.allocated, node.file_count, node.dir_count,
                     node.modified, node.error, node.snapshot, node.owner,
                     [child.name for child in node.children]))
    return sorted(rows)


def _scan_both(path: Path, monkeypatch: pytest.MonkeyPatch, **choices) -> tuple[scanner.ScanResult, scanner.ScanResult]:
    calls = []
    real = native_scan.reader()

    def counting(folder: str, file_times: bool):
        calls.append(folder)
        return real(folder, file_times)

    monkeypatch.setattr(native_scan, "reader", lambda: counting)
    fast = scan(path, options=ScanOptions(**choices))
    assert calls, "the native reader was not used"
    monkeypatch.setattr(native_scan, "reader", lambda: None)
    slow = scan(path, options=ScanOptions(**choices))
    return fast, slow


@pytest.mark.parametrize("choices", [{}, {"file_times": True}, {"include_hidden": False}, {"workers": 1},
                                     {"exclude": ("deep",)}, {"count_hard_links": True}])
def test_a_native_scan_records_exactly_what_the_python_scan_records(native, made_up, monkeypatch, choices):
    fast, slow = _scan_both(made_up, monkeypatch, **choices)
    assert _flat(fast.root) == _flat(slow.root)
    assert sorted(fast.errors) == sorted(slow.errors)
    assert (fast.root.size, fast.root.file_count, fast.root.dir_count) == (
        slow.root.size, slow.root.file_count, slow.root.dir_count)


def test_native_snapshots_equal_a_fresh_lstat_so_later_checks_accept_them(native, made_up):
    seen = 0
    for folder, _folders, _files in os.walk(made_up):
        for name, kind, size, modified, snapshot, attributes in native(folder, False):
            path = os.path.join(folder, name)
            info = os.lstat(path)
            assert kind in (native_scan.KIND_FILE, native_scan.KIND_FOLDER)
            assert snapshot == pack_snapshot(info)
            assert modified == info.st_mtime and attributes == info.st_file_attributes
            assert kind == native_scan.KIND_FOLDER or size == info.st_size
            seen += 1
        for name, _kind, _size, _modified, snapshot, _attributes in native(folder, True):
            assert snapshot == pack_snapshot(os.lstat(os.path.join(folder, name)), file_times=True)
    assert seen >= 14


def test_both_metadata_queries_give_the_same_rows(native, made_up):
    from je_file_tree import _native

    folder = str(made_up / "plain")
    by_handle = _native.read_folder(folder, True, False, _native.QUERY_BY_HANDLE)
    assert [row[0] for row in by_handle] == sorted(os.listdir(folder), key=[row[0] for row in by_handle].index)
    if _native.by_name_available():
        assert _native.read_folder(folder, True, False, _native.QUERY_BY_NAME) == by_handle
    for name, _kind, _size, _modified, snapshot, _attributes in by_handle:
        assert snapshot == pack_snapshot(os.lstat(os.path.join(folder, name)), file_times=True)


def test_links_are_left_to_python_and_recorded_as_links(native, made_up, monkeypatch):
    target = made_up / "plain" / "deep"
    link = made_up / "junction"
    made = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],  # noqa: S603, S607 - fixture junction
                          capture_output=True, check=False)
    if made.returncode != 0:
        pytest.skip("cannot create a junction here")
    try:
        rows = {row[0]: row for row in native(str(made_up), False)}
        assert rows["junction"][1] == native_scan.KIND_ASK_PYTHON and rows["junction"][4] is None
        fast, slow = _scan_both(made_up, monkeypatch)
        assert _flat(fast.root) == _flat(slow.root)
        junction = next(node for node in fast.root.children if node.name == "junction")
        assert junction.is_link and junction.is_dir and not junction.children and junction.size == 0
    finally:
        os.rmdir(link)  # removes the junction itself, never its target
    assert (target / "big.bin").exists()


def test_a_folder_that_cannot_be_listed_is_reported_like_before(native, made_up, monkeypatch):
    with pytest.raises(OSError) as raised:
        native(str(made_up / "no-such-folder"), False)
    assert raised.value.winerror in (2, 3) and raised.value.filename.endswith("no-such-folder")
    with pytest.raises(OSError):
        native(str(made_up / "plain" / "a.txt"), False)  # a file is not a folder
    assert native(str(made_up / "empty"), False) == []


def test_scans_that_need_per_file_queries_stay_in_python(native, made_up, monkeypatch):
    used = []
    monkeypatch.setattr(native_scan, "reader", lambda: used.append(1) or native)
    scan(made_up, options=ScanOptions(windows_owners=True))
    scan(made_up, options=ScanOptions(exact_windows_allocation=True))
    assert not used
    scan(made_up)
    assert used


def test_the_reader_is_refused_when_switched_off_or_when_it_disagrees(monkeypatch):
    native_scan.reset()
    monkeypatch.setenv(native_scan.DISABLE_VARIABLE, "0")
    assert native_scan.reader() is None
    native_scan.reset()
    monkeypatch.delenv(native_scan.DISABLE_VARIABLE)
    monkeypatch.setattr(native_scan, "pack_snapshot", lambda info, **_: b"different")
    assert native_scan.reader() is None  # snapshots that do not equal os.lstat's turn it off
    native_scan.reset()


def test_embedded_nulls_and_unknown_queries_are_refused(native):
    from je_file_tree import _native

    with pytest.raises(ValueError):
        _native.read_folder("C:\\a\0b", False, False, _native.QUERY_BY_HANDLE)
    with pytest.raises(ValueError):
        _native.read_folder("C:\\", False, False, 99)
