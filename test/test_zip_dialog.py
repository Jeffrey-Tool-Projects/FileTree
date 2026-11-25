"""The archive window starts and moves only on request, and the original goes through the usual questions."""

import os

import pytest
from PySide6.QtWidgets import QFileDialog, QMessageBox

from test_gui import _wait, window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.core.scanner import scan
from je_file_tree.gui import i18n, main_window
from je_file_tree.gui.scan_worker import analyse
from je_file_tree.gui.zip_dialog import ZipDialog


@pytest.fixture
def folder(tmp_path):
    made = tmp_path / "scan" / "old"
    made.mkdir(parents=True)
    (made / "a.txt").write_bytes(b"hello")
    return made


def _node(folder):
    root = scan(folder.parent).root
    return root, root.children[0]


def test_nothing_starts_by_itself_and_success_offers_the_move(qapp, folder, tmp_path):
    root, node = _node(folder)
    target = tmp_path / "old.zip"
    dialog = ZipDialog(root, node, str(target), "auto")
    qapp.processEvents()
    assert dialog.worker is None and not dialog.move.isEnabled() and not target.exists()
    dialog.start.click()
    _wait(qapp, lambda: dialog.proof is not None)
    assert target.exists() and dialog.move.isEnabled() and not dialog.stop.isEnabled()
    dialog.begin()
    assert not dialog.start.isEnabled()
    dialog.move.click()
    assert dialog.move_requested and folder.exists()
    dialog.deleteLater()


def test_refusals_failures_and_stops_are_explained_and_can_be_retried(qapp, folder, tmp_path):
    root, node = _node(folder)
    target = tmp_path / "old.zip"
    target.write_bytes(b"mine")
    dialog = ZipDialog(root, node, str(target), "auto")
    dialog.begin()
    _wait(qapp, dialog.start.isEnabled)
    assert dialog.status.text() == i18n.tr("zip_reason_exists", path=str(target)) and not dialog.move.isEnabled()
    for emit, text in ((lambda: dialog._refused("missing", "p"), i18n.tr("zip_reason_changed", path="p")),
                       (lambda: dialog._refused("directory_streams", "p"), i18n.tr("zip_reason_streams", path="p")),
                       (lambda: dialog.worker.failed.emit("disk full"), i18n.tr("zip_failed", reason="disk full")),
                       (dialog.worker.stopped.emit, i18n.tr("zip_stopped"))):
        emit()
        qapp.processEvents()
        assert dialog.status.text() == text and dialog.start.isEnabled()
    dialog.cancel()
    target.unlink()
    dialog.begin()
    _wait(qapp, lambda: dialog.proof is not None)
    dialog.reject()
    assert not dialog.move_requested
    dialog.deleteLater()


def test_closing_stops_and_joins(qapp, folder, tmp_path):
    root, node = _node(folder)
    dialog = ZipDialog(root, node, str(tmp_path / "old.zip"), "auto")
    dialog.begin()
    dialog.reject()
    _wait(qapp, lambda: not dialog.worker.isRunning())
    assert [name for name in os.listdir(tmp_path) if name.startswith(".file-tree-")] == []
    dialog.deleteLater()


@pytest.fixture
def opened(window, folder, tmp_path, monkeypatch):
    window.results.show_outcome(analyse(scan(folder.parent)))
    target = tmp_path / "old.zip"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *_args, **_kwargs: (str(target), ""))
    moved = []
    monkeypatch.setattr(window, "move_to_trash", moved.append)
    return window, window.results.tree_model.root.children[0], target, moved


def test_the_original_is_moved_only_when_asked_and_through_move_to_trash(opened, qapp, monkeypatch):
    window, node, target, moved = opened

    def archive(dialog, *, move):
        dialog.begin()
        _wait(qapp, lambda: dialog.proof is not None)
        dialog.move_requested = move
        return 1
    monkeypatch.setattr(main_window.ZipDialog, "exec", lambda dialog: archive(dialog, move=False))
    window.show_zip(node)
    assert target.exists() and moved == [] and not window._trash_rescans  # outside the scan
    target.unlink()
    monkeypatch.setattr(main_window.ZipDialog, "exec", lambda dialog: archive(dialog, move=True))
    window.show_zip(node)
    assert moved == [[node]] and not window._path_dialogs


def test_an_archive_inside_the_scan_offers_its_folder_for_a_rescan(opened, qapp, folder, monkeypatch):
    window, node, _target, _moved = opened
    root = window.results.tree_model.root
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        lambda *_args, **_kwargs: (str(folder.parent / "inside.zip"), ""))

    def archive(dialog):
        dialog.begin()
        _wait(qapp, lambda: dialog.proof is not None)
        return 0
    monkeypatch.setattr(main_window.ZipDialog, "exec", archive)
    window.show_zip(node)
    assert window._trash_rescans == [root]


def test_a_lost_archive_never_moves_the_original(opened, qapp, monkeypatch):
    window, node, target, moved = opened

    def lose(dialog):
        dialog.begin()
        _wait(qapp, lambda: dialog.proof is not None)
        dialog.move_requested = True
        target.unlink()
        return 1
    told = []
    monkeypatch.setattr(main_window.ZipDialog, "exec", lose)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: told.append(args[2]))
    window.show_zip(node)
    assert moved == [] and told == [i18n.tr("zip_lost")]


def test_a_cancelled_file_choice_or_the_scan_root_open_nothing(opened, monkeypatch):
    window, node, _target, _moved = opened
    monkeypatch.setattr(main_window.ZipDialog, "exec", lambda _dialog: pytest.fail("nothing opens"))
    window.show_zip(window.results.tree_model.root)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *_args, **_kwargs: ("", ""))
    window.show_zip(node)
