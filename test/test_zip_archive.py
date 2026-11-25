"""Archives hold exactly the scanned folder, verified before they appear; nothing is overwritten, moved or lost."""

import os
import sys
import threading
import zipfile

import pytest

from je_file_tree.core import zip_archive as module
from je_file_tree.core.scanner import scan
from je_file_tree.core.zip_archive import (
    ArchiveRefusedError, ArchiveStoppedError, _date, create_archive, plan_archive,
)


@pytest.fixture
def source(tmp_path):
    folder = tmp_path / "scan" / "資料 2019"
    (folder / "sub" / "empty").mkdir(parents=True)
    (folder / "a.txt").write_bytes(b"hello")
    (folder / "sub" / "b.bin").write_bytes(os.urandom(3 << 20))
    (folder / "zero").write_bytes(b"")
    (tmp_path / "out").mkdir()
    return folder


def _scan(folder):
    root = scan(folder.parent).root
    return root, next(child for child in root.children if child.name == folder.name)


def _contents(folder):
    return {path.relative_to(folder.parent).as_posix(): path.read_bytes()
            for path in folder.rglob("*") if path.is_file()}


def _refused(folder, target, reason):
    root, node = _scan(folder)
    with pytest.raises(ArchiveRefusedError) as refusal:
        create_archive(plan_archive(root, node, str(target)))
    assert refusal.value.reason == reason
    assert not [name for name in os.listdir(target.parent) if name.startswith(".file-tree-")]


def test_a_verified_archive_holds_everything_and_leaves_the_original(source, tmp_path):
    before = _contents(source)
    root, node = _scan(source)
    target = tmp_path / "out" / "old.zip"
    phases = []
    plan = plan_archive(root, node, str(target))
    proof = create_archive(plan, lambda phase, done, total: phases.append((phase, done, total)))
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert {name: archive.read(name) for name in names if not name.endswith("/")} == before
        assert "資料 2019/sub/empty/" in names and names[0] == "資料 2019/"
    assert proof.plan.files == 3 and proof.plan.bytes == 5 + (3 << 20) and proof.size == target.stat().st_size
    assert {phase for phase, _done, _total in phases} == {"pack", "verify"}
    assert all(0 < done <= total for _phase, done, total in phases)
    assert _contents(source) == before and os.listdir(tmp_path / "out") == ["old.zip"] and proof.unchanged()


def test_the_proof_notices_a_changed_or_missing_archive(source, tmp_path):
    root, node = _scan(source)
    target = tmp_path / "out" / "old.zip"
    proof = create_archive(plan_archive(root, node, str(target)))
    target.write_bytes(target.read_bytes() + b"x")
    assert not proof.unchanged()
    target.unlink()
    assert not proof.unchanged()


def test_targets_are_never_overwritten_or_inside_the_folder(source, tmp_path):
    existing = tmp_path / "out" / "old.zip"
    existing.write_bytes(b"keep me")
    _refused(source, existing, "exists")
    assert existing.read_bytes() == b"keep me"
    _refused(source, source / "inside.zip", "inside")
    _refused(source, source / "sub" / "inside.zip", "inside")
    _refused(source, tmp_path / "out" / "name.txt", "target")
    root, node = _scan(source)
    with pytest.raises(ArchiveRefusedError):
        plan_archive(root, node, str(tmp_path / "missing" / "x.zip"))


def test_an_arrival_at_the_target_is_kept(source, tmp_path, monkeypatch):
    root, node = _scan(source)
    target = tmp_path / "out" / "old.zip"
    plan = plan_archive(root, node, str(target))
    real = module.revalidate

    def arrive(*args, **kwargs):
        target.write_bytes(b"someone else's")
        return real(*args, **kwargs)
    monkeypatch.setattr(module, "revalidate", arrive)
    with pytest.raises(OSError):
        create_archive(plan)
    assert target.read_bytes() == b"someone else's" and os.listdir(tmp_path / "out") == ["old.zip"]


@pytest.mark.parametrize("change", ["content", "new", "gone"])
def test_folders_changed_since_the_scan_are_refused(source, tmp_path, change):
    root, node = _scan(source)
    if change == "content":
        (source / "a.txt").write_bytes(b"changed")
    elif change == "new":
        (source / "sub" / "new.txt").write_bytes(b"x")
    else:
        (source / "a.txt").unlink()
    with pytest.raises(ArchiveRefusedError):
        plan_archive(root, node, str(tmp_path / "out" / "old.zip"))


def test_a_change_while_packing_leaves_nothing(source, tmp_path, monkeypatch):
    root, node = _scan(source)
    plan = plan_archive(root, node, str(tmp_path / "out" / "old.zip"))
    real = module._read_back

    def change(*args):
        real(*args)
        (source / "late.txt").write_bytes(b"arrived while packing")
    monkeypatch.setattr(module, "_read_back", change)
    with pytest.raises(ArchiveRefusedError) as refusal:
        create_archive(plan)
    assert refusal.value.reason == "changed" and os.listdir(tmp_path / "out") == []


def test_a_member_that_reads_back_differently_is_refused(source, tmp_path, monkeypatch):
    root, node = _scan(source)
    plan = plan_archive(root, node, str(tmp_path / "out" / "old.zip"))
    real = module._write

    def wrong(*args):
        digests = real(*args)
        return dict.fromkeys(digests, b"\0" * 32)
    monkeypatch.setattr(module, "_write", wrong)
    with pytest.raises(ArchiveRefusedError) as refusal:
        create_archive(plan)
    assert refusal.value.reason == "verify" and os.listdir(tmp_path / "out") == []


@pytest.mark.parametrize("phase", ["pack", "verify"])
def test_stopping_leaves_nothing(source, tmp_path, phase):
    root, node = _scan(source)
    cancel = threading.Event()
    plan = plan_archive(root, node, str(tmp_path / "out" / "old.zip"), cancel)
    with pytest.raises(ArchiveStoppedError):
        create_archive(plan, lambda now, _done, _total: now == phase and cancel.set(), cancel)
    assert os.listdir(tmp_path / "out") == []
    with pytest.raises(ArchiveStoppedError):
        plan_archive(root, node, str(tmp_path / "out" / "other.zip"), cancel)


def test_a_full_disk_leaves_nothing(source, tmp_path, monkeypatch):
    root, node = _scan(source)
    plan = plan_archive(root, node, str(tmp_path / "out" / "old.zip"))

    def full(*_args):
        raise OSError(28, "No space left on device")
    monkeypatch.setattr(module, "_write", full)
    with pytest.raises(OSError, match="No space"):
        create_archive(plan)
    assert os.listdir(tmp_path / "out") == []


def test_files_and_links_are_refused(source, tmp_path):
    root, node = _scan(source)
    file = next(child for child in node.children if child.name == "a.txt")
    with pytest.raises(ArchiveRefusedError) as refusal:
        plan_archive(root, file, str(tmp_path / "out" / "x.zip"))
    assert refusal.value.reason == "folder_required"
    with pytest.raises(ArchiveRefusedError):
        plan_archive(root, root, str(tmp_path / "out" / "x.zip"))  # the scan root itself


@pytest.mark.skipif(sys.platform == "win32", reason="creating a symlink needs rights on Windows")
def test_a_folder_holding_a_link_is_refused(source, tmp_path):
    os.symlink("a.txt", source / "link")
    _refused(source, tmp_path / "out" / "x.zip", "copy_unsupported")


@pytest.mark.skipif(sys.platform == "win32", reason="Windows cannot hold such a name")
def test_names_a_zip_cannot_keep_are_refused(source, tmp_path):
    (source / "back\\slash").write_bytes(b"x")
    _refused(source, tmp_path / "out" / "x.zip", "name")


@pytest.mark.skipif(sys.platform != "win32", reason="NTFS streams")
def test_named_streams_are_refused(source, tmp_path):
    try:
        with open(f"{source / 'a.txt'}:extra", "wb") as stream:
            stream.write(b"hidden")
    except OSError:
        pytest.skip("this volume has no named streams")
    _refused(source, tmp_path / "out" / "x.zip", "streams")


@pytest.mark.parametrize("modified, year", [(0, 1980), (-1e12, 1980), (float("nan"), 1980), (1e18, 1980), (5e9, 2107),
                                            (1_700_000_000, 2023)])
def test_dates_stay_within_what_a_zip_can_hold(modified, year):
    assert _date(modified)[0] == year
