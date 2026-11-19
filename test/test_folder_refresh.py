"""Reading one changed folder's own entries again keeps its subfolders and corrects every total above it."""

import os
import shutil

from je_file_tree.core.refresh import kept_subfolders, refill, refreshed_errors
from je_file_tree.core.scanner import KEPT, ScanOptions, scan


def _tree(tmp_path):
    root = tmp_path / "來源"
    (root / "a" / "deep").mkdir(parents=True)
    (root / "b").mkdir()
    (root / "a" / "deep" / "one").write_bytes(b"1" * 10)
    (root / "b" / "two").write_bytes(b"2" * 20)
    (root / "top").write_bytes(b"t" * 5)
    return root, scan(root).root


def _child(folder, name):
    return next(child for child in folder.children if child.name == name)


def test_a_listing_reads_only_the_folder_and_keeps_its_subfolders_in_place(tmp_path):
    source, root = _tree(tmp_path)
    a, deep = _child(root, "a"), _child(_child(root, "a"), "deep")
    (source / "a" / "deep" / "one").write_bytes(b"1" * 99)  # below a kept subfolder: not read now
    (source / "top").write_bytes(b"t" * 7)
    (source / "c").mkdir()
    (source / "c" / "three").write_bytes(b"3" * 30)
    keep = kept_subfolders(root)
    assert {name for name, _device, _number in keep} == {"a", "b"}

    fresh = scan(source, options=ScanOptions(keep=keep))
    assert _child(fresh.root, "a").error == KEPT and not _child(fresh.root, "a").children
    old_top = _child(root, "top")
    assert refill(root, fresh.root) == frozenset({"a", "b"})

    assert _child(root, "a") is a and a.parent is root and _child(a, "deep") is deep and deep.size == 10
    assert _child(root, "c").size == 30 and _child(_child(root, "c"), "three").parent is _child(root, "c")
    assert _child(root, "top").size == 7 and old_top.parent is None
    assert root.size == 10 + 20 + 7 + 30 and root.file_count == 4 and root.dir_count == 4
    assert [child.name for child in root.children] == ["c", "b", "a", "top"]


def test_refilling_a_subfolder_corrects_the_folders_above_it(tmp_path):
    source, root = _tree(tmp_path)
    b = _child(root, "b")
    (source / "b" / "more").write_bytes(b"m" * 40)
    (source / "b" / "two").unlink()
    assert refill(b, scan(source / "b", options=ScanOptions(keep=kept_subfolders(b))).root) == frozenset()
    assert b.size == 40 and [child.name for child in b.children] == ["more"]
    assert root.size == 10 + 40 + 5 and root.file_count == 3 and _child(root, "b") is b


def test_a_subfolder_replaced_since_the_scan_is_read_again(tmp_path):
    source, root = _tree(tmp_path)
    keep = kept_subfolders(root)
    old_b = _child(root, "b")
    shutil.rmtree(source / "b")
    (source / "b").mkdir()
    (source / "b" / "new").write_bytes(b"n" * 3)
    fresh = scan(source, options=ScanOptions(keep=keep))
    if _child(fresh.root, "b").error == KEPT:  # the system gave the new folder the old one's file number
        return
    assert refill(root, fresh.root) == frozenset({"a"})
    assert _child(root, "b") is not old_b and _child(root, "b").size == 3 and old_b.parent is None


def test_nothing_changes_when_a_kept_subfolder_left_the_tree_meanwhile(tmp_path):
    source, root = _tree(tmp_path)
    fresh = scan(source, options=ScanOptions(keep=kept_subfolders(root)))
    _child(root, "a").detach()
    before = list(root.children), root.size
    assert refill(root, fresh.root) is None
    assert (list(root.children), root.size) == before


def test_errors_inside_kept_subfolders_stay_and_the_rest_are_replaced(tmp_path):
    folder = str(tmp_path / "f")
    errors = [(folder, "partial"), (os.path.join(folder, "kept", "x"), "denied"),
              (os.path.join(folder, "gone"), "denied"), (str(tmp_path / "other"), "denied")]
    fresh = [(os.path.join(folder, "new"), "denied")]
    assert refreshed_errors(errors, folder, frozenset({"kept"}), fresh) == [
        (os.path.join(folder, "kept", "x"), "denied"), (str(tmp_path / "other"), "denied"), *fresh]
