"""Problem files come from the recorded tree; links are read but never followed, and doubt stays unknown."""

import os
import struct
import sys
import threading
import time

import pytest

from je_file_tree.core import problem_files as module
from je_file_tree.core.node import Node
from je_file_tree.core.problem_files import (
    BAD_NAME, DEAD_LINK, EMPTY, KINDS, LONG_PATH, bad_name, problem_files, target_exists,
)
from je_file_tree.core.scanner import scan
from je_file_tree.core.shell_link import ShortcutError, local_target


def _node(name, parent, size=1, **fields):
    is_dir, children = fields.pop("is_dir", False), fields.pop("children", ())
    node = Node(name, is_dir, size=size, parent=parent, children=children, **fields)
    parent.children.append(node)
    return node


def shortcut(target: str, *, wide: bool = True, flags: int = 2, local: int = 1) -> bytes:
    """A minimal shortcut recording ``target`` as its local path."""
    header = struct.pack("<I", 0x4C) + bytes.fromhex("0114020000000000c000000000000046") + struct.pack("<I", flags)
    header = header.ljust(0x4C, b"\0")
    if not flags & 2:
        return header
    if wide:
        text = target.encode("utf-16-le") + b"\0\0"
        body = struct.pack("<9I", 0, 0x24, local, 0, 0, 0, 0, 0x24, 0x24 + len(text) - 2) + text
    else:
        text = target.encode("ascii") + b"\0"
        body = struct.pack("<7I", 0, 0x1C, local, 0, 0x1C, 0, 0x1C + len(text) - 1) + text
    return header + struct.pack("<I", len(body)) + body[4:]


@pytest.mark.parametrize("name", ["a:b", "what?", "a*", 'q"', "a<b", "pipe|", "back\\slash", "tab\t", "end.", "end ",
                                  "CON", "nul.txt", "Com1", "lpt9.log", "aux .txt", "COM²"])
def test_names_windows_refuses(name):
    assert bad_name(name)


@pytest.mark.parametrize("name", ["a", "console", "con1", "com10", "lpt", "nul-a.txt", ".hidden", "a.b.c",
                                  "名稱", "x con"])
def test_ordinary_names(name):
    assert not bad_name(name)


def test_kinds_counts_and_limits_without_touching_the_disk(monkeypatch):
    root = Node("C:\\scan", True, children=[])
    _node("empty.txt", root, size=0)
    _node("nul", root, size=0)
    _node("y" * 252, root)
    _node("y" * 250, root)  # C:\scan\ + 250 = 258 characters still fit
    _node("failed", root, size=0, error="access denied")
    _node("folder", root, size=0, is_dir=True, children=[])
    monkeypatch.setattr(os, "lstat", lambda *_args: pytest.fail("the survey of ordinary files reads nothing"))
    found = {row.node.name[:9]: row.kinds for row in problem_files(root, platform="win32").rows}
    assert found == {"empty.txt": (EMPTY,), "nul": (BAD_NAME, EMPTY), "y" * 9: (LONG_PATH,)}
    result = problem_files(root, limit=1, platform="linux")
    assert result.counts == {DEAD_LINK: 0, BAD_NAME: 1, LONG_PATH: 0, EMPTY: 2} and result.count == 3
    assert len(result.rows) == 2  # a row listed for either of its kinds
    with pytest.raises(ValueError):
        problem_files(root, limit=0)


def test_absolute_names_under_a_virtual_root_are_no_file_names():
    root = Node("", True, children=[])
    drive = _node("D:\\", root, is_dir=True, children=[])
    _node("a" * 256, drive)
    _node("b" * 257, drive)
    found = [(row.node.name[0], row.kinds) for row in problem_files(root, platform="win32").rows]
    assert found == [("b", (LONG_PATH,))]


def test_a_cancelled_or_deep_survey():
    root = top = Node("root", True, children=[])
    for level in range(3000):
        top = _node(str(level), top, is_dir=True, children=[])
    _node("end.", top)
    assert problem_files(root).counts[BAD_NAME] == 1
    cancel = threading.Event()
    cancel.set()
    assert problem_files(root, cancel=cancel) is None


def test_links_are_judged_by_their_own_target(tmp_path, monkeypatch):
    root = Node(str(tmp_path), True, children=[])
    for name in ("alive", "dead", "odd"):
        _node(name, root, size=0, is_link=True)
    there = tmp_path / "there"
    there.write_bytes(b"x")
    targets = {"alive": "there", "dead": "missing", "odd": None}

    def readlink(path):
        target = targets[os.path.basename(path)]
        if target is None:
            raise OSError("not a link any more")
        return target
    monkeypatch.setattr(os, "readlink", readlink)
    result = problem_files(root)
    assert [(row.node.name, row.kinds, row.target) for row in result.rows] == [
        ("dead", (DEAD_LINK,), str(tmp_path / "missing"))]
    assert result.unknown_links == 1
    monkeypatch.setattr(module, "MAX_LINKS", 1)
    assert problem_files(root).unknown_links == 2


@pytest.mark.skipif(sys.platform == "win32", reason="creating a symlink needs rights on Windows")
def test_real_symlinks(tmp_path):
    (tmp_path / "file").write_bytes(b"x")
    os.symlink("file", tmp_path / "good")
    os.symlink("nowhere", tmp_path / "bad")
    os.symlink("bad", tmp_path / "to-a-link")  # the link it names exists, whatever that points to
    result = problem_files(scan(tmp_path).root)
    assert [(row.node.name, row.kinds) for row in result.rows if DEAD_LINK in row.kinds] == [("bad", (DEAD_LINK,))]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows shortcuts")
def test_shortcuts_are_read_only_when_small_and_stored_here(tmp_path, monkeypatch):
    target = tmp_path / "target.txt"
    target.write_bytes(b"x")
    (tmp_path / "good.lnk").write_bytes(shortcut(str(target)))
    (tmp_path / "dead.lnk").write_bytes(shortcut(str(tmp_path / "gone.txt")))
    (tmp_path / "server.lnk").write_bytes(shortcut("\\\\server\\share\\x"))
    (tmp_path / "text.lnk").write_bytes(b"not a shortcut")
    root = scan(tmp_path).root
    result = problem_files(root)
    assert [(row.node.name, row.target) for row in result.rows if DEAD_LINK in row.kinds] == [
        ("dead.lnk", str(tmp_path / "gone.txt"))]
    assert result.unknown_links == 2
    for child in root.children:
        child.snapshot = None  # not known to be stored here: never opened
    monkeypatch.setattr(module, "_shortcut_target", lambda _path: pytest.fail("a cloud file would be downloaded"))
    assert problem_files(root).counts[DEAD_LINK] == 0


def test_shortcut_parsing():
    assert local_target(shortcut("C:\\資料\\a.txt")) == "C:\\資料\\a.txt"
    assert local_target(shortcut("C:\\a.txt", wide=False)) == "C:\\a.txt"
    assert local_target(shortcut("", flags=0)) is None  # an app or a web page
    assert local_target(shortcut("C:\\a", local=2)) is None  # a network place


@pytest.mark.parametrize("data", [b"", b"x" * 200, shortcut("C:\\a")[:-4], shortcut("C:\\a")[:90],
                                  shortcut("C:\\a", wide=False).replace(b"C:", b"\xa5:")])
def test_damaged_shortcuts_are_refused(data):
    with pytest.raises(ShortcutError):
        local_target(data)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows drives")
def test_network_relative_and_absent_targets_stay_unknown(tmp_path, monkeypatch):
    assert target_exists("\\\\server\\share\\x") is None and target_exists("relative") is None
    assert target_exists("\\\\?\\Volume{0}\\x") is None
    assert target_exists(str(tmp_path)) is True and target_exists("\\\\?\\" + str(tmp_path)) is True
    assert target_exists(str(tmp_path / "gone")) is False
    monkeypatch.setattr(os.path, "exists", lambda _path: False)
    assert target_exists("Q:\\anything") is None


def test_denied_targets_stay_unknown(tmp_path, monkeypatch):
    def denied(_path):
        raise PermissionError("denied")
    monkeypatch.setattr(os, "lstat", denied)
    assert target_exists(str(tmp_path / "x")) is None


def test_the_survey_is_paced_for_large_trees():
    root = Node("root", True, children=[])
    for index in range(50_000):
        root.children.append(Node(f"file {index}.bin", False, size=1, parent=root))
    started = time.perf_counter()
    assert problem_files(root).count == 0
    assert time.perf_counter() - started < 5
    assert KINDS[0] == DEAD_LINK
