"""A whole-drive scan may be served from the NTFS file table, and only when every condition holds."""

import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_gui import window as window  # noqa: PLC0414 - explicit fixture re-export
from je_file_tree.core import mft_scan, native_scan, scanner
from je_file_tree.core.scanner import ScanOptions, scan
from je_file_tree.core.snapshot import pack_snapshot, path_metadata
from je_file_tree.gui import main_window as main

ROOT = "Q:\\"
ROOT_REFERENCE = 5 | (5 << 48)


def _snapshot(reference: int) -> bytes:
    return (77).to_bytes(8, "little") + reference.to_bytes(16, "little") + bytes(52)


class _Table:
    """A made-up module: one drive whose root holds a folder and a file."""

    QUERY_BY_HANDLE_SHORT = 3

    def __init__(self, *, damaged: int = 0, root: bytes = b"root", refuse: bool = False) -> None:
        self.damaged, self.root, self.refuse, self.opened, self.asked = damaged, root, refuse, [], []

    def mft_open(self, drive):
        self.opened.append(drive)
        if self.refuse:
            raise PermissionError(5, "Access is denied")
        return "table"

    def mft_info(self, table):
        assert table == "table"
        return (77, 100, 3, self.damaged)

    def mft_snapshot(self, _table, reference, _file_times, _change_time, _short):
        assert reference == ROOT_REFERENCE
        return self.root

    def mft_rows(self, _table, reference, file_times, change_time, short):
        self.asked.append((reference, file_times, change_time, short))
        if reference == ROOT_REFERENCE:
            return [("inner", native_scan.KIND_FOLDER, 0, 1.0, _snapshot(40 | (2 << 48)), 0x10),
                    ("file.bin", native_scan.KIND_FILE, 9, 2.0, _snapshot(41 | (1 << 48)), 0x20)]
        return [("deep.txt", native_scan.KIND_FILE, 3, 3.0, _snapshot(42 | (1 << 48)), 0x20)]


@pytest.fixture
def made_up_drive(monkeypatch):
    """Pretend to be Windows with a calibrated module; ``os.lstat`` of the root answers b"root"."""
    table = _Table()
    monkeypatch.setattr(mft_scan, "sys", SimpleNamespace(platform="win32"))
    monkeypatch.setattr(native_scan, "chosen", lambda: (table, False, False))
    monkeypatch.setattr(mft_scan.os, "lstat", lambda _path: SimpleNamespace(st_ino=ROOT_REFERENCE | (9 << 64)))
    monkeypatch.setattr(mft_scan, "path_metadata", lambda info: info)
    monkeypatch.setattr(mft_scan, "pack_snapshot", lambda _info, *, file_times=False: b"root")
    monkeypatch.delenv(mft_scan.DISABLE_VARIABLE, raising=False)
    return table


@pytest.mark.parametrize(("path", "drive"), [("C:\\", "C:"), ("d:/", "d:"), ("C:\\Users", None), ("C:", None),
                                             ("\\\\server\\share\\", None), ("1:\\", None), ("/", None), ("", None)])
def test_only_the_root_of_a_lettered_drive_is_a_whole_drive(path, drive):
    assert mft_scan.drive_of(path) == drive


def test_rows_are_served_by_reference_and_each_folder_once(made_up_drive):
    read = mft_scan.table_reader(ROOT)
    assert read is not None and made_up_drive.opened == ["Q:"]
    rows = read(ROOT, True)
    assert [row[0] for row in rows] == ["inner", "file.bin"]
    assert [row[0] for row in read(os.path.join(ROOT, "inner"), False)] == ["deep.txt"]
    assert made_up_drive.asked == [(ROOT_REFERENCE, True, False, False), (40 | (2 << 48), False, False, False)]
    for path in (ROOT, os.path.join(ROOT, "inner"), os.path.join(ROOT, "file.bin"), "Q:\\elsewhere"):
        with pytest.raises(FileNotFoundError):
            read(path, False)


@pytest.mark.parametrize("change", ["folder", "switched off", "not calibrated", "old module", "refused", "damaged",
                                    "root differs", "other system"])
def test_the_table_is_not_used_unless_everything_holds(made_up_drive, monkeypatch, change):
    path = ROOT
    if change == "folder":
        path = "Q:\\folder"
    elif change == "switched off":
        monkeypatch.setenv(mft_scan.DISABLE_VARIABLE, "0")
    elif change == "not calibrated":
        monkeypatch.setattr(native_scan, "chosen", lambda: None)
    elif change == "old module":
        monkeypatch.setattr(native_scan, "chosen", lambda: (SimpleNamespace(), False, False))
    elif change == "refused":
        made_up_drive.refuse = True
    elif change == "damaged":
        made_up_drive.damaged = 1
    elif change == "root differs":
        made_up_drive.root = b"another folder"
    else:
        monkeypatch.setattr(mft_scan, "sys", SimpleNamespace(platform="linux"))
    assert mft_scan.table_reader(path) is None
    assert not made_up_drive.asked
    assert not made_up_drive.opened or change in ("refused", "damaged", "root differs")


@pytest.mark.skipif(sys.platform != "win32", reason="the scanner takes native rows on Windows only")
def test_a_scan_asks_for_the_table_only_when_told_and_then_reads_with_one_thread(tmp_path, monkeypatch):
    (tmp_path / "inner").mkdir()
    (tmp_path / "inner" / "deep.txt").write_bytes(b"abc")
    (tmp_path / "file.bin").write_bytes(b"123456789")
    asked, threads = [], []

    def rows_of(path, _file_times):  # what a table would answer, taken from the folder itself
        rows = []
        with os.scandir(path) as entries:
            for entry in entries:
                info = path_metadata(os.lstat(entry.path), entry.stat(follow_symlinks=False).st_file_attributes)
                kind = native_scan.KIND_FOLDER if entry.is_dir() else native_scan.KIND_FILE
                rows.append((entry.name, kind, info.st_size, info.st_mtime, pack_snapshot(info),
                             info.st_file_attributes))
        return rows

    def table_reader(root):
        asked.append(root)
        return rows_of

    run = scanner._Crawler.run

    def watched(self, *arguments):
        threads.append(self._threads)
        return run(self, *arguments)

    monkeypatch.setattr(mft_scan, "table_reader", table_reader)
    monkeypatch.setattr(scanner._Crawler, "run", watched)
    plain = scan(tmp_path, options=ScanOptions(workers=3))
    assert not asked and threads == [3]
    served = scan(tmp_path, options=ScanOptions(workers=3, mft=True, adaptive=True))
    assert asked == [str(tmp_path)] and threads == [3, 1]

    def flat(result):
        return sorted((node.path, node.is_dir, node.size, node.allocated, node.modified, node.snapshot, node.error)
                      for node in result.root.iter_nodes())

    assert flat(served) == flat(plain) and served.errors == plain.errors
    monkeypatch.setattr(mft_scan, "table_reader", lambda _root: None)
    assert flat(scan(tmp_path, options=ScanOptions(mft=True))) == flat(plain)  # no table: folders are listed
    for needs_queries in ({"windows_owners": True}, {"exact_windows_allocation": True}):
        asked.clear()
        monkeypatch.setattr(mft_scan, "table_reader", table_reader)
        scan(tmp_path, options=ScanOptions(mft=True, **needs_queries))
        assert not asked


def test_window_reads_the_table_by_default_and_remembers_the_choice(window):
    action = window._actions["mft_scan"]
    assert action.isCheckable() and action.isChecked() and window._scan_options().mft
    assert action in window._menus["menu_options"].actions()
    action.trigger()
    assert not window._scan_options().mft and not main.read_flag(window.settings, main.MFT_SCAN_KEY, True)
    action.trigger()
    assert window._scan_options().mft and main.read_flag(window.settings, main.MFT_SCAN_KEY, False)


# ---- the real table of the drive holding pytest's temporary folder: read-only, made-up entries ----

def _real_module():
    if sys.platform != "win32":
        pytest.skip("the file table is an NTFS structure, read on Windows only")
    try:
        from je_file_tree import _native  # noqa: PLC0415 - optional module
    except ImportError:
        pytest.skip("je_file_tree._native is not built here (python setup.py build_ext --inplace)")
    if not hasattr(_native, "mft_open"):
        pytest.skip("this build of je_file_tree._native cannot read the file table")
    return _native


def _made_up(root: Path) -> None:
    (root / "plain" / "deep").mkdir(parents=True)
    (root / "empty").mkdir()
    (root / "檔案 資料夾").mkdir()
    files = {"plain/a.txt": b"a" * 10, "plain/zero.bin": b"", "plain/deep/big.bin": b"b" * 70_000,
             "檔案 資料夾/名稱 with space.txt": b"u" * 33, "plain/a name longer than eight characters.data": b"n" * 5}
    for name, content in files.items():
        with open(root / name, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    os.link(root / "plain" / "a.txt", root / "plain" / "a-hard-link.txt")
    subprocess.run(["attrib", "+h", str(root / "plain" / "zero.bin")], check=True)  # noqa: S603, S607 - fixed tool


def _table_rows(native, table, folder: Path, choices: tuple[bool, bool]) -> dict[str, dict] | None:
    """The rows of ``folder`` and everything beneath, by path relative to it; None when not in the table."""
    reference = os.lstat(folder.anchor).st_ino & ((1 << 64) - 1)
    for part in folder.parts[1:]:
        found = {row[0]: row for row in native.mft_rows(table, reference, False, *choices)}
        if part not in found or found[part][1] != native_scan.KIND_FOLDER:
            return None
        reference = int.from_bytes(found[part][4][8:16], "little")
    rows, pending = {}, [("", reference)]
    while pending:
        prefix, reference = pending.pop()
        for row in native.mft_rows(table, reference, False, *choices):
            rows[prefix + row[0]] = row
            if row[1] == native_scan.KIND_FOLDER:
                pending.append((prefix + row[0] + "/", int.from_bytes(row[4][8:16], "little")))
    return rows


def _expected_rows(folder: Path) -> dict[str, tuple]:
    rows = {}
    for path in sorted(folder.rglob("*")):
        listed = next(entry for entry in os.scandir(path.parent) if entry.name == path.name)
        info = path_metadata(os.lstat(path), listed.stat(follow_symlinks=False).st_file_attributes)
        kind = native_scan.KIND_FOLDER if path.is_dir() else native_scan.KIND_FILE
        rows[path.relative_to(folder).as_posix()] = (path.name, kind, info.st_size, info.st_mtime,
                                                     pack_snapshot(info), info.st_file_attributes)
    return rows


def test_the_real_table_describes_made_up_entries_exactly_as_lstat_does(tmp_path, monkeypatch):
    native = _real_module()
    monkeypatch.undo()  # this module's conftest switches the native reader off; the table needs its calibration
    native_scan.reset()
    chosen = native_scan.chosen()
    if chosen is None:
        pytest.skip("the native reader does not agree with os.lstat here")
    root = tmp_path.resolve() / "table"
    root.mkdir()
    _made_up(root)
    expected = _expected_rows(root)
    drive = root.drive
    found, deadline = None, time.monotonic() + 60
    while True:  # the table on disk follows the running system a few seconds behind
        try:
            table = native.mft_open(drive)
        except OSError as error:
            pytest.skip(f"cannot read the file table of {drive} here: {error}")
        assert native.mft_info(table)[3] == 0
        found = _table_rows(native, table, root, chosen[1:])
        if found == expected or time.monotonic() > deadline:
            break
        time.sleep(2)
    assert found == expected
    assert unpack_links(found["plain/a.txt"]) == unpack_links(found["plain/a-hard-link.txt"]) == 2
    file_reference = int.from_bytes(found["plain/a.txt"][4][8:16], "little")
    with pytest.raises(OSError):
        native.mft_rows(table, file_reference, False, *chosen[1:])  # a file is not a folder
    with pytest.raises(OSError):
        native.mft_rows(table, (1 << 47) | (1 << 48), False, *chosen[1:])  # no such record
    with pytest.raises(ValueError):
        native.mft_open("nonsense")
    with pytest.raises((TypeError, ValueError)):
        native.mft_rows(object(), 5, False, False, False)
    native_scan.reset()


def unpack_links(row: tuple) -> int:
    """The link count recorded in a row's snapshot."""
    return int.from_bytes(row[4][72:76], "little")
