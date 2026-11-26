"""A whole-drive scan may be served from the NTFS file table, and only when every condition holds."""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_gui import window as window  # noqa: PLC0414 - explicit fixture re-export
from je_file_tree.core import mft_scan, native_scan
from je_file_tree.core.scanner import NOT_SCANNED, ScanCancelledError, ScanOptions, scan
from je_file_tree.core.snapshot import pack_snapshot, path_metadata
from je_file_tree.gui import window_scans
from je_file_tree.gui.window_settings import MFT_SCAN_KEY, read_flag

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
            raise PermissionError(13, "Permission denied")
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
    monkeypatch.setattr(mft_scan, "_administrator", lambda: True)
    monkeypatch.setattr(mft_scan, "is_small", lambda _path: False)
    monkeypatch.delenv(mft_scan.DISABLE_VARIABLE, raising=False)
    return table


@pytest.mark.parametrize(("path", "drive"), [("C:\\", "C:"), ("d:/", "d:"), ("C:\\Users\\someone", "C:"), ("C:", None),
                                             ("C:relative", None), ("\\\\server\\share\\", None), ("1:\\", None),
                                             ("/", None), ("/home/someone", None), ("", None), ("資:\\", None)])
def test_only_a_path_on_a_lettered_drive_names_a_table(path, drive):
    assert mft_scan.drive_of(path) == drive


def test_a_folder_below_the_root_is_served_from_its_own_record(made_up_drive):
    table = mft_scan.open_table("Q:\\some\\folder")  # the made-up module answers for whatever os.lstat names
    assert table is not None and made_up_drive.opened == ["Q:"] and table.root == ROOT_REFERENCE


def test_rows_are_served_by_reference(made_up_drive):
    table = mft_scan.open_table(ROOT)
    assert table is not None and made_up_drive.opened == ["Q:"] and table.root == ROOT_REFERENCE
    rows = table.rows(table.root, True)
    assert [row[0] for row in rows] == ["inner", "file.bin"]
    inner = mft_scan.reference_of(rows[0][4])
    assert inner == 40 | (2 << 48) and [row[0] for row in table.rows(inner, False)] == ["deep.txt"]
    assert made_up_drive.asked == [(ROOT_REFERENCE, True, False, False), (inner, False, False, False)]


@pytest.mark.parametrize("change", ["network", "switched off", "not calibrated", "old module", "refused", "damaged",
                                    "root differs", "other system", "not administrator", "small folder"])
def test_the_table_is_not_used_unless_everything_holds(made_up_drive, monkeypatch, change):
    path = ROOT
    if change == "network":
        path = "\\\\server\\share\\folder"
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
    elif change == "not administrator":
        monkeypatch.setattr(mft_scan, "_administrator", lambda: False)
    elif change == "small folder":
        path = "Q:\\small"
        monkeypatch.setattr(mft_scan, "is_small", lambda asked: asked == path)
    else:
        monkeypatch.setattr(mft_scan, "sys", SimpleNamespace(platform="linux"))
    assert mft_scan.open_table(path) is None
    assert not made_up_drive.asked
    assert not made_up_drive.opened or change in ("refused", "damaged", "root differs")


def test_a_drive_root_is_never_probed_and_a_large_folder_is_read_from_the_table(made_up_drive, monkeypatch):
    probed = []
    monkeypatch.setattr(mft_scan, "is_small", lambda path: probed.append(path) or False)
    assert mft_scan.open_table(ROOT) is not None and not probed
    assert mft_scan.open_table("Q:\\large") is not None and probed == ["Q:\\large"]


@pytest.mark.skipif(sys.platform != "win32", reason="the probe reads Windows file attributes")
def test_a_folder_is_small_only_when_all_of_it_is_listed_within_the_limits(tmp_path, monkeypatch):
    for number in range(6):
        (tmp_path / f"folder{number}").mkdir()
        (tmp_path / f"folder{number}" / "file").write_bytes(b"1")
    assert mft_scan.is_small(str(tmp_path))  # 12 entries
    monkeypatch.setattr(mft_scan, "SMALL_ENTRIES", 12)
    assert not mft_scan.is_small(str(tmp_path))
    monkeypatch.setattr(mft_scan, "SMALL_ENTRIES", 13)
    assert mft_scan.is_small(str(tmp_path))
    monkeypatch.setattr(mft_scan, "PROBE_SECONDS", -1.0)
    assert not mft_scan.is_small(str(tmp_path))  # out of time after the first folder
    assert not mft_scan.is_small(str(tmp_path / "missing"))  # the table decides about a root that cannot be listed


@pytest.mark.skipif(sys.platform != "win32", reason="junctions are a Windows link")
def test_the_probe_does_not_enter_a_junction(tmp_path, monkeypatch):
    outside, scanned = tmp_path / "outside", tmp_path / "scanned"
    (outside / "many").mkdir(parents=True)
    for number in range(5):
        (outside / "many" / f"file{number}").write_bytes(b"1")
    scanned.mkdir()
    made = subprocess.run(["cmd", "/c", "mklink", "/J", str(scanned / "link"), str(outside)],  # noqa: S603, S607
                          capture_output=True, check=False)
    if made.returncode != 0:
        pytest.skip("cannot create a junction here")
    try:
        monkeypatch.setattr(mft_scan, "SMALL_ENTRIES", 3)
        assert mft_scan.is_small(str(scanned)) and not mft_scan.is_small(str(outside))
    finally:
        os.rmdir(scanned / "link")  # removes the junction itself, never its target
    assert (outside / "many" / "file0").exists()


windows_only = pytest.mark.skipif(sys.platform != "win32", reason="the scanner takes table rows on Windows only")


class _FolderTable:
    """What a file table would answer for a made-up folder, taken from the folder itself."""

    def __init__(self, root: Path, *, ask_python: tuple[str, ...] = ()) -> None:
        self.paths = {mft_scan.folder_reference(str(root)): str(root)}
        self.root = mft_scan.folder_reference(str(root))
        self.ask_python, self.asked, self.refused = ask_python, [], set()

    def rows(self, reference: int, file_times: bool):
        folder = self.paths[reference]
        self.asked.append(folder)
        if folder in self.refused:
            raise PermissionError(13, "Permission denied")
        rows = []
        with os.scandir(folder) as entries:
            for entry in entries:
                listed = entry.stat(follow_symlinks=False).st_file_attributes
                info = path_metadata(os.lstat(entry.path), listed)
                folder_row = entry.is_dir(follow_symlinks=False) and not listed & 0x400
                if folder_row:  # a table knows every folder of its volume, whatever it says about the entry
                    self.paths[info.st_ino & ((1 << 64) - 1)] = entry.path
                if listed & 0x400 or entry.name in self.ask_python:
                    rows.append((entry.name, native_scan.KIND_ASK_PYTHON, 0, 0.0, None, 0))
                    continue
                rows.append((entry.name, native_scan.KIND_FOLDER if folder_row else native_scan.KIND_FILE,
                             info.st_size, info.st_mtime, pack_snapshot(info, file_times=file_times),
                             info.st_file_attributes))
        return rows


@pytest.fixture
def made_up_tree(tmp_path) -> Path:
    root = tmp_path / "scan"
    (root / "plain" / "deep" / "deeper").mkdir(parents=True)
    (root / "empty").mkdir()
    (root / "檔案 資料夾").mkdir()
    (root / ".dotfolder").mkdir()
    for name, size in {"plain/a.txt": 10, "plain/zero.bin": 0, "plain/deep/big.bin": 70_000,
                       "plain/deep/deeper/x.log": 4096, "檔案 資料夾/名稱 with space.txt": 33, ".dotfile": 1,
                       ".dotfolder/inside.txt": 5, "plain/hidden.txt": 7, "top.bin": 123}.items():
        (root / name).write_bytes(b"x" * size)
    if sys.platform == "win32":
        subprocess.run(["attrib", "+h", str(root / "plain" / "hidden.txt")], check=True)  # noqa: S603, S607
    os.link(root / "plain" / "a.txt", root / "plain" / "a-hard-link.txt")
    return root


def _flat(result) -> list[tuple]:
    return sorted((node.path, node.is_dir, node.is_link, node.size, node.allocated, node.file_count, node.dir_count,
                   node.modified, node.error, node.snapshot, [child.name for child in node.children])
                  for node in result.root.iter_nodes())


def _use(monkeypatch, table) -> list[str]:
    opened: list[str] = []
    monkeypatch.setattr(mft_scan, "open_table", lambda root: opened.append(root) or table)
    return opened


@windows_only
@pytest.mark.parametrize("choices", [{}, {"file_times": True}, {"include_hidden": False}, {"exclude": ("deep",)},
                                     {"workers": 3, "adaptive": True}, {"count_hard_links": True}, {"gentle": True}])
def test_a_tree_built_from_the_table_equals_a_listed_one(made_up_tree, monkeypatch, choices):
    listed = scan(made_up_tree, options=ScanOptions(**choices))
    table = _FolderTable(made_up_tree)
    opened = _use(monkeypatch, table)
    built = scan(made_up_tree, options=ScanOptions(mft=True, **choices))
    assert opened == [str(made_up_tree)] and len(table.asked) == len(set(table.asked)) > 1
    assert _flat(built) == _flat(listed)
    assert sorted(built.errors) == sorted(listed.errors) and built.warnings == listed.warnings
    assert (built.root.size, built.root.allocated, built.root.file_count, built.root.dir_count) == (
        listed.root.size, listed.root.allocated, listed.root.file_count, listed.root.dir_count)


@windows_only
def test_entries_left_to_python_are_asked_and_a_plain_folder_among_them_is_still_read(made_up_tree, monkeypatch):
    outside = made_up_tree.parent / "outside"
    outside.mkdir()
    (outside / "never-counted.bin").write_bytes(b"o" * 50)
    made = subprocess.run(["cmd", "/c", "mklink", "/J", str(made_up_tree / "junction"), str(outside)],  # noqa: S603, S607
                          capture_output=True, check=False)
    try:
        listed = scan(made_up_tree)
        table = _FolderTable(made_up_tree, ask_python=("top.bin", "empty", "plain"))
        _use(monkeypatch, table)
        built = scan(made_up_tree, options=ScanOptions(mft=True))
        assert _flat(built) == _flat(listed) and built.errors == listed.errors
        assert str(made_up_tree / "plain" / "deep") in table.asked and str(outside) not in table.asked
        if made.returncode == 0:
            junction = next(node for node in built.root.children if node.name == "junction")
            assert junction.is_link and junction.is_dir and not junction.children and junction.size == 0
    finally:
        if made.returncode == 0:
            os.rmdir(made_up_tree / "junction")  # removes the junction itself, never its target
    assert (outside / "never-counted.bin").exists()


@windows_only
def test_a_folder_the_table_cannot_answer_for_is_reported_and_the_rest_is_read(made_up_tree, monkeypatch):
    table = _FolderTable(made_up_tree)
    table.refused.add(str(made_up_tree / "plain" / "deep"))
    _use(monkeypatch, table)
    built = scan(made_up_tree, options=ScanOptions(mft=True))
    deep = next(node for node in built.root.iter_nodes() if node.name == "deep")
    assert deep.error == "access denied" and not deep.children
    assert built.errors == [(str(made_up_tree / "plain" / "deep"), "access denied")]
    assert built.root.file_count == 8 and built.root.size == 10 + 10 + 0 + 33 + 1 + 5 + 7 + 123


@windows_only
def test_stopping_a_table_walk_keeps_what_was_read_and_marks_the_rest(made_up_tree, monkeypatch):
    table, cancel = _FolderTable(made_up_tree), threading.Event()
    rows = table.rows

    def stop_after_two(reference, file_times):
        if len(table.asked) == 2:
            cancel.set()
        return rows(reference, file_times)

    table.rows = stop_after_two
    _use(monkeypatch, table)
    with pytest.raises(ScanCancelledError) as stopped:
        scan(made_up_tree, options=ScanOptions(mft=True), cancel=cancel)
    partial = stopped.value.partial
    assert len(table.asked) == 3 and partial is not None
    unread = [node for node in partial.root.iter_nodes() if node.error == NOT_SCANNED]
    assert unread and all(node.is_dir and not node.children for node in unread)
    assert partial.root.size == sum(node.size for node in partial.root.iter_nodes() if not node.is_dir)
    already = threading.Event()
    already.set()
    with pytest.raises(ScanCancelledError):
        scan(made_up_tree, options=ScanOptions(mft=True), cancel=already)


@windows_only
def test_a_table_walk_waits_while_paused_and_reports_progress(made_up_tree, monkeypatch):
    table, pause, seen = _FolderTable(made_up_tree), threading.Event(), []
    _use(monkeypatch, table)
    pause.set()
    threading.Timer(0.3, pause.clear).start()
    started = time.monotonic()
    built = scan(made_up_tree, options=ScanOptions(mft=True), pause=pause, progress=seen.append,
                 progress_interval=0.0)
    assert time.monotonic() - started >= 0.25
    assert len(seen) >= len(table.asked) and seen[-1].files == built.root.file_count == 10
    assert [progress.files for progress in seen] == sorted(progress.files for progress in seen)


@windows_only
def test_a_scan_asks_for_the_table_only_when_told(made_up_tree, monkeypatch):
    opened = _use(monkeypatch, None)
    listed = scan(made_up_tree, options=ScanOptions(workers=3))
    assert not opened
    assert _flat(scan(made_up_tree, options=ScanOptions(mft=True))) == _flat(listed)  # no table: folders are listed
    assert opened == [str(made_up_tree)]
    for needs_queries in ({"windows_owners": True}, {"exact_windows_allocation": True}):
        opened.clear()
        scan(made_up_tree, options=ScanOptions(mft=True, **needs_queries))
        assert not opened


def test_rescanning_one_folder_of_a_finished_scan_lists_it(window, tmp_path, monkeypatch):
    from je_file_tree.gui.scan_worker import analyse  # noqa: PLC0415

    (tmp_path / "inner").mkdir()
    (tmp_path / "inner" / "file").write_bytes(b"1")
    window.results.show_outcome(analyse(scan(tmp_path)))
    made = []

    class Recording(window_scans.ScanWorker):
        def __init__(self, path, options, *arguments, **named):
            made.append((path, options.mft))
            super().__init__(path, options, *arguments, **named)

    monkeypatch.setattr(window_scans, "ScanWorker", Recording)
    # built and owned, never started
    monkeypatch.setattr(window_scans, "queue_worker", lambda *_arguments, **_options: None)
    inner = window.results.tree_model.root.children[0]
    assert window._scan_options().mft
    window.rescan_folder(inner)
    assert made == [(str(tmp_path / "inner"), False)]
    worker = window._worker
    window._discard_branch(worker)
    worker.deleteLater()


def test_window_reads_the_table_by_default_and_remembers_the_choice(window):
    action = window._actions["mft_scan"]
    assert action.isCheckable() and action.isChecked() and window._scan_options().mft
    assert action in window._menus["menu_options"].actions()
    action.trigger()
    assert not window._scan_options().mft and not read_flag(window.settings, MFT_SCAN_KEY, True)
    action.trigger()
    assert window._scan_options().mft and read_flag(window.settings, MFT_SCAN_KEY, False)


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
