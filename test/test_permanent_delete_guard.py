"""The test-suite guard refuses permanent deletion outside pytest's temporary directory.

These tests only assert the refusal. The real removal primitives are replaced by recorders first,
so even a broken guard could not remove anything: nothing here can reach a real unlink.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from je_file_tree.core import permanent_delete

_REPOSITORY = Path(__file__).resolve().parents[1]


@pytest.fixture
def no_real_removal(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Replace every removal primitive with a recorder, so an assertion is all that can happen."""
    reached: list[str] = []

    def record(path, *_args, **_kwargs):
        reached.append(str(path))
        raise AssertionError("a real removal primitive was reached")

    for name in ("unlink", "remove", "rmdir", "removedirs"):
        monkeypatch.setattr(os, name, record)
    for name in ("_remove_windows", "_remove_posix"):
        if hasattr(permanent_delete, name):
            monkeypatch.setattr(permanent_delete, name, record)
    return reached


@pytest.mark.parametrize("place", ["repository", "home", "drive_root", "repository_file"])
def test_guard_refuses_real_places(place, no_real_removal, _permanent_delete_guard):
    target = {"repository": _REPOSITORY, "home": Path.home(),
              "drive_root": Path(Path.cwd().anchor or os.sep),
              "repository_file": _REPOSITORY / "pyproject.toml"}[place]

    with pytest.raises(AssertionError, match="Tests may only delete fixtures under"):
        permanent_delete.remove_entry(str(target), b"", b"", directory=target.is_dir())

    assert _permanent_delete_guard == [str(target)]
    assert no_real_removal == []
    assert target.exists()
    _permanent_delete_guard.clear()  # the refusal was the expected outcome of this test


def test_guard_refuses_the_temporary_base_itself_and_a_link_escape(tmp_path_factory, no_real_removal,
                                                                   _permanent_delete_guard):
    base = tmp_path_factory.getbasetemp()
    with pytest.raises(AssertionError):
        permanent_delete.remove_entry(str(base), b"", b"", directory=True)
    with pytest.raises(AssertionError):
        permanent_delete.remove_entry(os.path.join(str(base), "..", "elsewhere"), b"", b"", directory=False)
    assert len(_permanent_delete_guard) == 2
    assert no_real_removal == []
    _permanent_delete_guard.clear()


def test_guard_place_check_accepts_only_entries_strictly_inside_the_base(tmp_path, tmp_path_factory):
    from conftest import _inside_temporary

    base = os.path.normcase(os.path.realpath(tmp_path_factory.getbasetemp()))
    assert _inside_temporary(str(tmp_path / "made-up.txt"), base)
    assert _inside_temporary(str(tmp_path), base)
    assert not _inside_temporary(base, base)
    assert not _inside_temporary(base + "-sibling", base)
    assert not _inside_temporary(str(_REPOSITORY), base)
    assert not _inside_temporary(str(Path.home()), base)
    assert not _inside_temporary(Path.cwd().anchor or os.sep, base)
    assert not _inside_temporary(os.path.join(str(tmp_path), "..", "..", "..", "escape"), base)


def test_guard_is_installed_around_the_single_removal_function(_permanent_delete_guard):
    assert permanent_delete.remove_entry.__name__ == "guarded"
    assert _permanent_delete_guard == []


def test_a_test_undoing_its_own_patches_keeps_every_guard(monkeypatch):
    from je_file_tree.core import finder_bin
    from je_file_tree.gui import elevation, history

    guarded = (permanent_delete.remove_entry, finder_bin._run_finder_empty, elevation.run_as_admin,
               history.history_folder)
    monkeypatch.setattr(permanent_delete, "remove_entry", lambda *_args, **_options: None)
    monkeypatch.undo()
    assert guarded == (permanent_delete.remove_entry, finder_bin._run_finder_empty, elevation.run_as_admin,
                       history.history_folder)
    assert permanent_delete.remove_entry.__name__ == "guarded"


def test_names_that_are_no_entry_are_refused(tmp_path, tmp_path_factory):
    from conftest import _inside_temporary

    base = os.path.normcase(os.path.realpath(tmp_path_factory.getbasetemp()))
    for name in (".", "..", ""):
        assert not _inside_temporary(os.path.join(str(tmp_path), name), base)
