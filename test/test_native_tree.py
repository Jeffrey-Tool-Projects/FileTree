"""The native passes over a finished tree give exactly what the Python code they stand in for gives."""

import dataclasses
import random
import struct
import threading

import pytest

from je_file_tree.core import analysis, capacity, export, native_tree
from je_file_tree.core.analysis import AnalysisCancelledError, summarise
from je_file_tree.core.capacity import capacity_ledger
from je_file_tree.core.history import ScanHistory
from je_file_tree.core.node import Node
from je_file_tree.core.scanner import scan

PASSES = ("json_folders", "local_time_text", "capacity_new", "capacity_add", "capacity_finish", "summary_new",
          "summary_step", "summary_finish")


@pytest.fixture
def native(monkeypatch):
    """Skip unless this build of the module has every pass; the passes are switched on for the test."""
    monkeypatch.delenv(native_tree.DISABLE_VARIABLE, raising=False)
    missing = [name for name in PASSES if native_tree.function(name) is None]
    if missing:
        pytest.skip("je_file_tree._native is not built here or lacks: " + ", ".join(missing))


def _in_python(monkeypatch, work):
    monkeypatch.setenv(native_tree.DISABLE_VARIABLE, "0")
    try:
        return work()
    finally:
        monkeypatch.delenv(native_tree.DISABLE_VARIABLE)


def _snapshot(device: int, number: int, links: int, *, times: bool = False) -> bytes:
    packed = struct.pack("<Q16sq16s16sIII", device, number.to_bytes(16, "little"), 0, bytes(16), bytes(16), 0o100000,
                         0x20, links)
    return packed + struct.pack("<dd", 1.0, 2.0) if times else packed


def _file(parent: Node, name: str, size: int, modified: float = 1_700_000_000.0, **fields) -> Node:
    node = Node(name, False, size, 1, 0, modified, allocated=-(-size // 4096) * 4096, parent=parent,
                snapshot=_snapshot(7, random.getrandbits(60) + 1, 1), **fields)  # noqa: S311 - made-up identities
    parent.children.append(node)
    return node


def _folder(parent: Node | None, name: str, **fields) -> Node:
    node = Node(name, True, children=[], parent=parent, snapshot=_snapshot(7, random.getrandbits(60) + 1, 1), **fields)
    if parent is not None:
        parent.children.append(node)
    return node


def _add_up(folder: Node) -> None:
    for child in folder.children:
        if child.is_dir and not child.is_link:
            _add_up(child)
    folder.size = sum(child.size for child in folder.children)
    folder.allocated = sum(child.allocated for child in folder.children)
    folder.file_count = sum(child.file_count for child in folder.children)
    folder.dir_count = sum(1 + child.dir_count for child in folder.children if child.is_dir and not child.is_link)
    folder.modified = max([folder.modified, *(child.modified for child in folder.children)])


@pytest.fixture
def made_up() -> Node:
    """A tree that never touches a disk, with the names, times and records that need care."""
    random.seed(20261115)
    root = _folder(None, "C:\\made up")
    plain = _folder(root, "plain")
    for index, name in enumerate(["a.TXT", "b.txt", "noextension", ".hidden", "trailing.", "two.dots.Tar.GZ",
                                  "quote\".json", "back\\slash.md", "tab\there.log", "bell\x07.bin", "del\x7f.bin",
                                  "emoji 😀.PNG", "中文 檔案.資料", "lone\ud800surrogate.dat", "İstanbul.İSO"]):
        _file(plain, name, 1000 * (index % 4) + 5, 1_600_000_000.0 + 40_000_000.0 * (index % 5))
    _file(plain, "never changed.bin", 77, 0.0)
    _file(plain, "from the future.bin", 78, 4_000_000_000.5)
    _file(plain, "before 1970.bin", 79, -5.0)
    deep = _folder(_folder(_folder(plain, "one"), "two", error="access denied"), "three \"quoted\"\n")
    _file(deep, "same size 1.x", 4096)
    _file(deep, "same size 2.x", 4096)
    _file(deep, "same size 3.X", 4096)
    _folder(root, "empty")
    _folder(root, "$RECYCLE.BIN")
    link = Node("link", True, is_link=True, parent=root, snapshot=_snapshot(7, 5, 1))
    root.children.append(link)
    file_link = Node("file link", False, is_link=True, parent=plain, snapshot=_snapshot(7, 6, 1))
    plain.children.append(file_link)
    shared = _folder(root, "shared")
    twin = _snapshot(7, 4242, 2)
    for name, allocated in (("first name.dat", 8192), ("second name.dat", 4096)):
        _file(shared, name, 6000).snapshot = twin
        shared.children[-1].allocated = allocated
    _file(shared, "other volume.dat", 100).snapshot = _snapshot(9, 11, 1)
    _file(shared, "no identity.dat", 100).snapshot = _snapshot(7, 0, 1)
    _file(shared, "no link count.dat", 100).snapshot = _snapshot(7, 12, 0, times=True)
    _file(shared, "never recorded.dat", 100).snapshot = None
    _file(shared, "failed.dat", 100, error="access denied")
    _add_up(root)
    return root


def _json(root: Node, joiner: str) -> str:
    return joiner.join(export.folder_json_pieces(root, joiner))


@pytest.mark.parametrize("joiner", ["", "\n"])
def test_folder_json_is_the_same_text(native, made_up, monkeypatch, joiner):
    written = _json(made_up, joiner)
    assert written == _in_python(monkeypatch, lambda: _json(made_up, joiner))
    assert written == joiner.join(export._folder_json(made_up, None))
    assert '"error": "access denied"' in written and "\\u0007" not in written  # files are not in this text
    assert 'three \\"quoted\\"\\n' in written


def test_folder_json_of_a_counted_or_virtual_root_and_of_a_single_folder(native, made_up, monkeypatch):
    made_up.accounting = (123, 456)
    made_up.children[0].accounting = (1, 2)
    assert _json(made_up, "\n") == _in_python(monkeypatch, lambda: _json(made_up, "\n"))
    made_up.name = ""  # the root over several scanned folders
    virtual = _json(made_up, "")
    assert '"virtual": true' in virtual and virtual == _in_python(monkeypatch, lambda: _json(made_up, ""))
    alone = _folder(None, "alone", modified=0.0)
    assert _json(alone, "") == _in_python(monkeypatch, lambda: _json(alone, "")) == "".join(
        export._folder_json(alone, None))


def test_folder_json_comes_in_pieces_so_the_caller_can_stop(native, monkeypatch):
    root = _folder(None, "wide")
    for index in range(native_tree.BATCH * 2 + 10):
        _folder(root, f"folder {index}")
    pieces = list(export.folder_json_pieces(root, "\n"))
    assert len(pieces) >= 4 and "\n".join(pieces) == "\n".join(export._folder_json(root, None))


def test_local_time_text_is_what_python_writes(native, monkeypatch):
    chosen = random.Random(7)  # noqa: S311 - made-up sample times
    values = [chosen.uniform(1, 4_000_000_000) for _ in range(20_000)]
    values += [1_700_000_000.9999996, 1_700_000_000.4999995, 0.5, 1e-9, 0.0, -1.0, float("nan"), float("inf"), 1e30]
    quick = [export._iso_time(value) for value in values]
    assert quick == _in_python(monkeypatch, lambda: [export._iso_time(value) for value in values])
    assert native_tree.function("local_time_text")(float("nan")) is None  # left to Python, which writes ""


def _ledger(root: Node) -> dict:
    ledger = capacity_ledger(root)
    kept = {field.name: getattr(ledger, field.name) for field in dataclasses.fields(ledger)
            if field.name not in ("measured_at", "coverage")}
    return kept | {"coverage_complete": ledger.coverage.complete, "known_folders": ledger.coverage.known_folders}


def test_the_capacity_ledger_has_the_same_numbers(native, made_up, monkeypatch):
    monkeypatch.setattr(capacity, "_usage", lambda _path: (10**9, 10**8, 9 * 10**8, 0))
    monkeypatch.setattr(capacity, "_status", lambda *_arguments: "estimated")
    counted = _ledger(made_up)
    assert counted == _in_python(monkeypatch, lambda: _ledger(made_up))
    assert counted["named_allocated"] > 0 and counted["unique_allocated"] is None  # an identity is unknown
    shared = next(child for child in made_up.children if child.name == "shared")
    shared.children[:] = shared.children[:3]  # the two names of one file and the file of another volume
    for child in list(made_up.children[0].children):
        if child.name == "one":
            made_up.children[0].children.remove(child)  # the folder that could not be read
    known = _ledger(made_up)
    assert known == _in_python(monkeypatch, lambda: _ledger(made_up))
    assert known["hard_link_overcount"] == 4096 and known["foreign_allocated_seen"] == 4096


def test_a_snapshot_of_the_wrong_length_is_refused_either_way(native, made_up, monkeypatch):
    made_up.children[0].children[0].snapshot = b"short"
    with pytest.raises(ValueError, match="snapshot length"):
        capacity_ledger(made_up)
    with pytest.raises(ValueError, match="snapshot length"):
        _in_python(monkeypatch, lambda: capacity_ledger(made_up))


def _summary(root: Node, limit: int, now: float) -> tuple:
    found = summarise(root, limit, now=now)
    return ([id(node) for node in found.largest], found.extensions, found.ages, found.counted_categories,
            found.top_folders)


@pytest.mark.parametrize("limit", [0, 1, 3, 5, 1000])
def test_the_summary_is_the_same(native, made_up, monkeypatch, limit):
    now = 1_800_000_000.0
    gathered = _summary(made_up, limit, now)
    assert gathered == _in_python(monkeypatch, lambda: _summary(made_up, limit, now))
    assert len(gathered[0]) == min(limit, made_up.file_count)
    made_up.accounting = (1, 2)
    for node in made_up.iter_nodes():
        if not node.is_dir and node.name.startswith("same size"):
            node.accounting = (node.size // 2, 0)
    assert _summary(made_up, limit, now) == _in_python(monkeypatch, lambda: _summary(made_up, limit, now))


def test_the_summary_of_one_file_and_of_a_link(native, monkeypatch):
    alone = Node("alone.TXT", False, 5, 1, 0, 1.0)
    assert _summary(alone, 10, 100.0) == _in_python(monkeypatch, lambda: _summary(alone, 10, 100.0))
    assert summarise(alone, 10).extensions[0].extension == ".txt"
    link = Node("link", True, is_link=True, children=[])
    assert _summary(link, 10, 100.0) == _in_python(monkeypatch, lambda: _summary(link, 10, 100.0))


def test_a_cancelled_summary_raises_either_way(native, made_up, monkeypatch):
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(AnalysisCancelledError):
        summarise(made_up, 10, cancel=cancel)
    with pytest.raises(AnalysisCancelledError):
        _in_python(monkeypatch, lambda: summarise(made_up, 10, cancel=cancel))


def test_real_folders_give_the_same_history_ledger_and_summary(native, tmp_path, monkeypatch):
    for index in range(40):
        folder = tmp_path / "scan" / f"folder {index % 7}" / f"deep {index % 3}"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"file {index}.{('TXT', 'bin', 'Log')[index % 3]}").write_bytes(b"x" * (index * 37))
    root = scan(tmp_path / "scan").root

    def saved(store: str) -> str:
        entry = ScanHistory(tmp_path / store).save(root)
        with open(entry.path, encoding="utf-8") as stream:
            stream.readline()  # the header carries the time of saving
            return stream.read()

    assert saved("native") == _in_python(monkeypatch, lambda: saved("python"))
    assert _ledger(root) | {"free": 0, "used": 0, "unavailable_free": 0, "unaccounted": None} == _in_python(
        monkeypatch, lambda: _ledger(root)) | {"free": 0, "used": 0, "unavailable_free": 0, "unaccounted": None}
    assert _summary(root, 12, 2_000_000_000.0) == _in_python(monkeypatch, lambda: _summary(root, 12, 2_000_000_000.0))


def test_the_passes_are_taken_in_python_when_switched_off_or_missing(monkeypatch):
    monkeypatch.setenv(native_tree.DISABLE_VARIABLE, "0")
    assert native_tree.function("json_folders") is None
    monkeypatch.delenv(native_tree.DISABLE_VARIABLE)
    assert native_tree.function("no such pass") is None
    monkeypatch.setattr(native_tree.sys, "platform", "linux")
    assert native_tree.function("json_folders") is None
    assert analysis._native_summary(Node("x", True, children=[]), 1, 0.0, None, None) is None
