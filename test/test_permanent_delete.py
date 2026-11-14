"""Permanent deletion removes exactly the approved, unchanged entries, and only fixtures made here.

Every fixture is created by its own test under ``tmp_path``; the conftest guard refuses any
removal outside pytest's temporary directory.
"""

from __future__ import annotations

import ast
import contextlib
import os
import stat
import threading
from pathlib import Path

import pytest

from conftest import make_tree
from je_file_tree.core import operations, permanent_delete
from je_file_tree.core.node import Node
from je_file_tree.core.permanent_delete import DELETED, FAILED, PARTIAL, SKIPPED, delete_entries
from je_file_tree.core.protected import PROGRAMS, SETTINGS, Protection
from je_file_tree.core.scanner import scan
from je_file_tree.core.system_files import SystemFile

_PACKAGE = Path(__file__).resolve().parents[1] / "je_file_tree"


def _find(root: Node, *names: str) -> Node:
    node = root
    for name in names:
        node = next(child for child in node.children if child.name == name)
    return node


def _delete(root: Node, nodes: list[Node], **options) -> tuple[permanent_delete.DeleteResult, dict[str, tuple]]:
    statuses: dict[str, tuple] = {}
    options.setdefault("approved", dict.fromkeys(nodes))
    result = delete_entries(root, nodes, finished=lambda node, *status: statuses.__setitem__(node.name, status),
                            **options)
    return result, statuses


def _snapshot(folder: Path) -> dict[str, bytes | None]:
    """Every path below ``folder`` with its content (None for a folder)."""
    found = {}
    for path in sorted(folder.rglob("*")):
        found[path.relative_to(folder).as_posix()] = None if path.is_dir() else path.read_bytes()
    return found


def _dir_link(link: Path, target: Path) -> None:
    """A folder link: a symlink where allowed, else a Windows junction (which needs no rights)."""
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            raise
        import _winapi

        _winapi.CreateJunction(str(target), str(link))


def _file_link(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except OSError as error:
        pytest.skip(f"file symlinks unavailable here: {error}")


@pytest.fixture
def scanned(tmp_path: Path) -> Path:
    root = tmp_path / "scan"
    root.mkdir()
    make_tree(root, {
        "target.txt": b"t" * 10, "target.txt.bak": b"b" * 11, "target": {"inner.txt": b"i"},
        "Target-copy.txt": b"c" * 12, "sibling.txt": b"s" * 13,
        "folder": {"a.txt": b"a" * 20, "sub": {"b.txt": b"b" * 30, "empty": {}}},
        "folder-2": {"a.txt": b"a" * 20},
    })
    return root


def test_only_the_approved_entries_go_and_siblings_parent_and_look_alikes_survive(scanned):
    root = scan(scanned).root
    survivors = {name: value for name, value in _snapshot(scanned).items()
                 if name not in ("target.txt", "folder") and not name.startswith("folder/")}
    assert "target.txt.bak" in survivors and "folder-2/a.txt" in survivors and "target/inner.txt" in survivors

    result, statuses = _delete(root, [_find(root, "target.txt"), _find(root, "folder")])

    assert statuses == {"target.txt": (DELETED, ""), "folder": (DELETED, "")}
    assert not (scanned / "target.txt").exists() and not (scanned / "folder").exists()
    assert _snapshot(scanned) == survivors
    assert scanned.is_dir()
    assert [node.name for node in result.removed] == ["target.txt", "folder"]
    assert result.removed_entries == 6  # target.txt, a.txt, b.txt, empty, sub, folder
    assert result.removed_bytes == 60
    assert result.refused == [] and result.failed == [] and result.kept == []
    assert result.parents == [root]


def test_an_entry_inside_another_approved_one_is_handled_once(scanned):
    root = scan(scanned).root
    folder = _find(root, "folder")
    result, _ = _delete(root, [_find(root, "folder", "sub", "b.txt"), folder])
    assert result.removed == [folder] and result.refused == []


@pytest.mark.parametrize("change", ["size", "modified", "replaced", "missing"])
def test_a_changed_or_missing_entry_is_refused_and_left(scanned, change):
    root = scan(scanned).root
    path = scanned / "sibling.txt"
    if change == "size":
        path.write_bytes(b"s" * 14)
    elif change == "modified":
        info = path.stat()
        os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns + 5_000_000_000))
    elif change == "replaced":  # the new file exists before the old one goes, so it has a new identity
        (scanned / "new.tmp").write_bytes(b"s" * 13)
        os.replace(scanned / "new.tmp", path)
    else:
        path.unlink()  # a fixture this test made

    result, statuses = _delete(root, [_find(root, "sibling.txt")])

    expected = {"size": "changed", "modified": "changed", "replaced": "identity", "missing": "missing"}[change]
    assert statuses == {"sibling.txt": (SKIPPED, expected)}
    assert result.refused == [(str(path), expected)] and not result.removed
    assert path.exists() == (change != "missing")


def test_a_file_replaced_by_a_link_is_refused_and_the_link_and_target_survive(tmp_path):
    folder = tmp_path / "scan"
    folder.mkdir()
    (folder / "victim.txt").write_bytes(b"v")
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"keep me")
    root = scan(folder).root
    (folder / "victim.txt").unlink()  # a fixture this test made
    _file_link(folder / "victim.txt", outside)

    result, statuses = _delete(root, [_find(root, "victim.txt")])

    assert statuses["victim.txt"][1] in ("link", "kind")
    assert os.path.lexists(folder / "victim.txt") and outside.read_bytes() == b"keep me"
    assert not result.removed


def test_a_folder_replaced_by_a_folder_link_is_refused(tmp_path):
    folder = tmp_path / "scan"
    make_tree(tmp_path, {"scan": {"box": {"x.txt": b"x"}}, "elsewhere": {"x.txt": b"precious"}})
    root = scan(folder).root
    (folder / "box" / "x.txt").unlink()
    (folder / "box").rmdir()
    _dir_link(folder / "box", tmp_path / "elsewhere")

    result, _ = _delete(root, [_find(root, "box")])

    assert result.refused and result.refused[0][1] in ("link", "kind", "identity")
    assert (tmp_path / "elsewhere" / "x.txt").read_bytes() == b"precious"
    assert os.path.lexists(folder / "box")


def test_a_parent_replaced_by_a_link_is_never_followed(tmp_path):
    make_tree(tmp_path, {"scan": {"parent": {"child.txt": b"c"}}, "other": {"child.txt": b"c"}})
    folder = tmp_path / "scan"
    root = scan(folder).root
    child = _find(root, "parent", "child.txt")
    os.replace(folder / "parent", tmp_path / "moved-parent")
    _dir_link(folder / "parent", tmp_path / "other")

    result, _ = _delete(root, [child])

    assert result.refused and not result.removed
    assert (tmp_path / "other" / "child.txt").read_bytes() == b"c"
    assert (tmp_path / "moved-parent" / "child.txt").read_bytes() == b"c"


def test_links_inside_an_approved_folder_go_as_links_and_their_targets_stay(tmp_path):
    make_tree(tmp_path, {"scan": {"box": {"own.txt": b"o"}}, "target": {"deep": {"keep.txt": b"keep"}},
                         "target.txt": b"file target"})
    folder = tmp_path / "scan"
    _dir_link(folder / "box" / "folder-link", tmp_path / "target")
    with contextlib.suppress(OSError):  # file symlinks may need rights; the folder link still covers the rule
        (folder / "box" / "file-link").symlink_to(tmp_path / "target.txt")
    root = scan(folder).root
    box = _find(root, "box")
    assert _find(box, "folder-link").is_link

    result, statuses = _delete(root, [box])

    assert statuses == {"box": (DELETED, "")}
    assert not os.path.lexists(folder / "box")
    assert _snapshot(tmp_path / "target") == {"deep": None, "deep/keep.txt": b"keep"}
    assert (tmp_path / "target.txt").read_bytes() == b"file target"
    assert result.refused == [] and result.failed == []


def test_a_later_arrival_survives_and_its_folder_is_kept_and_reported(scanned):
    root = scan(scanned).root
    (scanned / "folder" / "sub" / "arrived.txt").write_bytes(b"new")

    result, statuses = _delete(root, [_find(root, "folder")])

    assert statuses == {"folder": (PARTIAL, "not_empty")}
    assert _snapshot(scanned / "folder") == {"sub": None, "sub/arrived.txt": b"new"}
    assert (str(scanned / "folder" / "sub" / "arrived.txt"), "arrived") in result.refused
    assert (str(scanned / "folder"), "not_empty") in result.refused
    assert [node.name for node in result.kept] == ["folder"] and not result.removed
    assert result.removed_entries == 3  # a.txt, b.txt and the empty folder


def test_a_changed_file_inside_an_approved_folder_stays_with_its_folders(scanned):
    root = scan(scanned).root
    (scanned / "folder" / "sub" / "b.txt").write_bytes(b"changed")

    result, statuses = _delete(root, [_find(root, "folder")])

    assert statuses == {"folder": (PARTIAL, "not_empty")}
    assert (str(scanned / "folder" / "sub" / "b.txt"), "changed") in result.refused
    assert _snapshot(scanned / "folder") == {"sub": None, "sub/b.txt": b"changed"}


def test_an_incompletely_scanned_folder_is_not_entered(scanned):
    root = scan(scanned).root
    sub = _find(root, "folder", "sub")
    sub.error = "access denied"

    result, _ = _delete(root, [_find(root, "folder")])

    assert (str(scanned / "folder" / "sub"), "incomplete") in result.refused
    assert (scanned / "folder" / "sub" / "b.txt").exists() and not (scanned / "folder" / "a.txt").exists()


def test_windows_managed_entries_are_refused_at_the_top_and_inside(scanned, monkeypatch):
    managed = {str(scanned / "sibling.txt"), str(scanned / "folder" / "a.txt")}
    def fake(path, **_kwargs):
        return SystemFile("pagefile", "memory") if os.path.normcase(path) in map(os.path.normcase, managed) else None
    monkeypatch.setattr(operations, "system_file", fake)
    monkeypatch.setattr(permanent_delete, "system_file", fake)
    root = scan(scanned).root

    result, statuses = _delete(root, [_find(root, "sibling.txt"), _find(root, "folder")])

    assert statuses["sibling.txt"] == (SKIPPED, "system_managed")
    assert statuses["folder"] == (PARTIAL, "not_empty")
    assert (str(scanned / "folder" / "a.txt"), "system_managed") in result.refused
    assert (scanned / "sibling.txt").exists() and (scanned / "folder" / "a.txt").exists()


def test_protection_must_match_what_the_user_approved(scanned):
    root = scan(scanned).root
    node = _find(root, "sibling.txt")
    places = [Protection(str(scanned / "sibling.txt"), PROGRAMS)]

    result, statuses = _delete(root, [node], places=places, approved={node: None})
    assert statuses == {"sibling.txt": (SKIPPED, "protected")} and (scanned / "sibling.txt").exists()

    result, statuses = _delete(root, [node], places=places, approved={node: places[0]})
    assert statuses == {"sibling.txt": (DELETED, "")} and not (scanned / "sibling.txt").exists()


def test_a_protected_place_inside_an_approved_folder_stays(scanned):
    root = scan(scanned).root
    folder = _find(root, "folder")
    places = [Protection(str(scanned / "folder" / "sub"), SETTINGS)]

    result, statuses = _delete(root, [folder], places=places, approved={folder: None})

    assert statuses == {"folder": (PARTIAL, "not_empty")}
    assert (str(scanned / "folder" / "sub"), "protected") in result.refused
    assert _snapshot(scanned / "folder") == {"sub": None, "sub/b.txt": b"b" * 30, "sub/empty": None}


def test_the_scan_root_and_foreign_entries_are_outside(scanned, tmp_path):
    root = scan(scanned).root
    other = tmp_path / "other"
    other.mkdir()
    (other / "x.txt").write_bytes(b"x")
    foreign = scan(other).root.children[0]

    result, statuses = _delete(root, [root, foreign])

    assert result.refused == [(root.path, "outside"), (foreign.path, "outside")] and not result.removed
    assert set(statuses.values()) == {(SKIPPED, "outside")}
    assert (other / "x.txt").exists() and scanned.is_dir()


def test_cancel_between_approved_entries_leaves_the_rest(scanned):
    root = scan(scanned).root
    cancel = threading.Event()
    nodes = [_find(root, name) for name in ("sibling.txt", "Target-copy.txt", "target.txt.bak")]

    result = delete_entries(root, nodes, approved=dict.fromkeys(nodes), cancel=cancel,
                            finished=lambda *_status: cancel.set())

    assert [node.name for node in result.removed] == ["sibling.txt"]
    assert result.refused == [(str(scanned / "Target-copy.txt"), "cancelled"),
                              (str(scanned / "target.txt.bak"), "cancelled")]
    assert (scanned / "Target-copy.txt").exists() and (scanned / "target.txt.bak").exists()


def test_cancel_inside_a_folder_keeps_the_folder_and_what_is_left(scanned, monkeypatch):
    root = scan(scanned).root
    cancel = threading.Event()
    guarded = permanent_delete.remove_entry

    def remove_then_cancel(path, expected, parent, *, directory):
        guarded(path, expected, parent, directory=directory)
        cancel.set()
    monkeypatch.setattr(permanent_delete, "remove_entry", remove_then_cancel)

    result, statuses = _delete(root, [_find(root, "folder")], cancel=cancel)

    assert statuses == {"folder": (PARTIAL, "cancelled")}
    assert result.removed_entries == 1 and (scanned / "folder").is_dir()
    assert len(_snapshot(scanned / "folder")) == 3  # one entry went before the cancel, the rest stayed


def test_a_system_failure_is_reported_and_the_rest_still_goes(scanned, monkeypatch):
    root = scan(scanned).root
    guarded = permanent_delete.remove_entry

    def refuse_one(path, expected, parent, *, directory):
        if path.endswith("b.txt"):
            raise PermissionError(13, "in use by a made-up program")
        guarded(path, expected, parent, directory=directory)
    monkeypatch.setattr(permanent_delete, "remove_entry", refuse_one)

    result, statuses = _delete(root, [_find(root, "folder"), _find(root, "sibling.txt")])

    assert statuses == {"folder": (PARTIAL, "not_empty"), "sibling.txt": (DELETED, "")}
    assert [path for path, _detail in result.failed] == [str(scanned / "folder" / "sub" / "b.txt")]
    assert "in use by a made-up program" in result.failed[0][1]
    assert _snapshot(scanned / "folder") == {"sub": None, "sub/b.txt": b"b" * 30}


def test_a_single_failed_file_is_reported_as_failed(scanned, monkeypatch):
    root = scan(scanned).root
    def refuse(path, *_args, **_kwargs):
        raise PermissionError(13, "made-up refusal", path)
    monkeypatch.setattr(permanent_delete, "remove_entry", refuse)

    result, statuses = _delete(root, [_find(root, "sibling.txt")])

    assert statuses == {"sibling.txt": (FAILED, "")} and len(result.failed) == 1
    assert (scanned / "sibling.txt").exists()


def test_a_replacement_swapped_in_right_before_removal_is_refused(scanned, monkeypatch):
    root = scan(scanned).root
    guarded = permanent_delete.remove_entry
    path = scanned / "sibling.txt"

    def swap_then_remove(target, expected, parent, *, directory):
        (scanned / "swap.tmp").write_bytes(b"s" * 13)
        os.replace(scanned / "swap.tmp", path)
        guarded(target, expected, parent, directory=directory)
    monkeypatch.setattr(permanent_delete, "remove_entry", swap_then_remove)

    result, statuses = _delete(root, [_find(root, "sibling.txt")])

    assert statuses == {"sibling.txt": (SKIPPED, "identity")}
    assert path.read_bytes() == b"s" * 13 and not result.removed


def test_every_removal_goes_through_the_single_remove_function(scanned, monkeypatch):
    root = scan(scanned).root
    guarded = permanent_delete.remove_entry
    calls: list[str] = []

    def count(path, expected, parent, *, directory):
        calls.append(path)
        guarded(path, expected, parent, directory=directory)
    monkeypatch.setattr(permanent_delete, "remove_entry", count)

    result, _ = _delete(root, [_find(root, "folder"), _find(root, "target")])

    assert len(calls) == result.removed_entries == 7
    assert all(os.path.normcase(path).startswith(os.path.normcase(str(scanned))) for path in calls)


@pytest.mark.skipif(os.name != "nt", reason="the read-only attribute is a Windows rule")
def test_a_read_only_file_is_refused_and_its_attribute_left_alone(scanned):
    path = scanned / "sibling.txt"
    os.chmod(path, stat.S_IREAD)
    try:
        root = scan(scanned).root
        result, statuses = _delete(root, [_find(root, "sibling.txt")])
        assert statuses == {"sibling.txt": (SKIPPED, "read_only")}
        assert path.exists() and not os.access(path, os.W_OK)
    finally:
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)


@pytest.mark.skipif(os.name != "nt", reason="volume mount folders are Windows junctions")
def test_a_volume_mount_folder_is_never_removed(tmp_path, monkeypatch):
    make_tree(tmp_path, {"scan": {"box": {"own.txt": b"o"}}, "target": {"keep.txt": b"keep"}})
    _dir_link(tmp_path / "scan" / "box" / "mounted", tmp_path / "target")
    root = scan(tmp_path / "scan").root
    real = os.readlink
    def volume(path):
        return "\\\\?\\Volume{00000000-0000-0000-0000-000000000000}\\" if path.endswith("mounted") else real(path)
    monkeypatch.setattr(os, "readlink", volume)

    result, statuses = _delete(root, [_find(root, "box")])

    assert statuses == {"box": (PARTIAL, "not_empty")}
    assert (str(tmp_path / "scan" / "box" / "mounted"), "mount_point") in result.refused
    assert os.path.lexists(tmp_path / "scan" / "box" / "mounted")
    assert (tmp_path / "target" / "keep.txt").read_bytes() == b"keep"


def test_a_deep_folder_is_walked_without_recursion(tmp_path):
    folder = tmp_path / "scan"
    deep = folder / "d"
    for _ in range(60):
        deep = deep / "d"
    try:
        deep.mkdir(parents=True)
    except OSError as error:
        pytest.skip(f"path too long here: {error}")
    (deep / "f").write_bytes(b"f")
    root = scan(folder).root

    result, statuses = _delete(root, [_find(root, "d")])

    assert statuses == {"d": (DELETED, "")} and result.removed_entries == 62
    assert not (folder / "d").exists()


# --- the only way in -------------------------------------------------------------------------


def _calls(name: str) -> list[tuple[str, str]]:
    """(file, enclosing function) of every call to ``name`` in the package."""
    found = []
    for path in sorted(_PACKAGE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for node in ast.walk(function):
                if isinstance(node, ast.Call):
                    called = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                    if called == name:
                        found.append((path.relative_to(_PACKAGE).as_posix(), function.name))
    return sorted(set(found))


def _references(name: str) -> list[tuple[str, str]]:
    """(file, enclosing function) of every use of ``name`` as an attribute or a bare name (calls,
    signal connections, assignments): any way of reaching it, not only direct calls."""
    found = []
    for path in sorted(_PACKAGE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        owners = {}
        for function in ast.walk(tree):
            if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for node in ast.walk(function):
                    owners.setdefault(id(node), function.name)  # outer functions are visited first
        for node in ast.walk(tree):
            used = (node.attr if isinstance(node, ast.Attribute) else node.id if isinstance(node, ast.Name)
                    else None)
            if used == name:
                found.append((path.relative_to(_PACKAGE).as_posix(), owners.get(id(node), "<module>")))
    return sorted(set(found))


def test_only_main_window_delete_permanently_reaches_the_deletion_core():
    assert _calls("PermanentDeleteWorker") == [("gui/main_window.py", "delete_permanently")]
    assert _calls("delete_entries") == [("gui/permanent_delete.py", "run")]
    assert _calls("remove_entry") == [("core/permanent_delete.py", "_remove")]
    assert _references("delete_permanently") == [("gui/main_window.py", "_delete_selected"),
                                                 ("gui/main_window.py", "show_menu_for")]
    assert _references("delete_entries") == [("gui/permanent_delete.py", "run")]
    assert {path for path, _function in _references("PermanentDeleteWorker")} == {"gui/main_window.py"}
    for name in ("delete_entries", "permanent_delete import", "import permanent_delete", "PermanentDeleteWorker"):
        mentioned = {path.relative_to(_PACKAGE).as_posix() for path in _PACKAGE.rglob("*.py")
                     if name in path.read_text(encoding="utf-8")}
        assert mentioned <= {"core/permanent_delete.py", "gui/permanent_delete.py", "gui/main_window.py"}, name


def test_clean_up_duplicates_and_suggestion_code_never_mention_permanent_deletion():
    suggestion_files = ["cleanup_panel.py", "cleanup_review.py", "cleanup_completion.py", "duplicates_panel.py",
                        "duplicate_link_dialog.py", "recurring_review.py", "recurring_dialog.py"]
    for name in suggestion_files:
        source = (_PACKAGE / "gui" / name).read_text(encoding="utf-8")
        assert "permanent" not in source.lower(), name


def test_only_the_platform_removers_call_removal_primitives():
    source = (_PACKAGE / "core" / "permanent_delete.py").read_text(encoding="utf-8")
    assert "shutil" not in source and "glob" not in source and "rmtree" not in source
    assert _primitive_callers() == {"unlink": ["_remove_posix"], "rmdir": ["_remove_posix"],
                                    "SetFileInformationByHandle": ["_mark_for_deletion"]}


def _primitive_callers() -> dict[str, list[str]]:
    tree = ast.parse((_PACKAGE / "core" / "permanent_delete.py").read_text(encoding="utf-8"))
    callers: dict[str, list[str]] = {}
    for function in ast.walk(tree):
        if isinstance(function, ast.FunctionDef):
            for node in ast.walk(function):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr in ("unlink", "rmdir", "remove", "removedirs",
                                               "SetFileInformationByHandle")):
                    callers.setdefault(node.func.attr, [])
                    if function.name not in callers[node.func.attr]:
                        callers[node.func.attr].append(function.name)
    return callers
