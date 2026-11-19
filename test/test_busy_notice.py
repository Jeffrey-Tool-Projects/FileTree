"""Actions that wait for a running scan or operation say so when used, instead of doing nothing."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QSettings
from PySide6.QtWidgets import QApplication, QMenu

from conftest import make_tree
from je_file_tree.gui import i18n
from je_file_tree.gui import main_window as main_window_module
from je_file_tree.gui.app import create_window
from je_file_tree.gui.busy_notice import action_name, busy_text
from je_file_tree.gui.i18n import tr


def _wait(app: QApplication, done, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while not done():
        assert time.monotonic() < deadline, "timed out"
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()


@pytest.fixture
def window(qapp: QApplication, tmp_path: Path):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue("language", "en")
    main = create_window(settings)
    yield main
    main._worker = None
    main._trash_worker = None
    main.close()
    _wait(qapp, lambda: main._close_ready)
    main.deleteLater()
    QCoreApplication.sendPostedEvents(main, QEvent.Type.DeferredDelete)
    i18n.set_language(i18n.DEFAULT_LANGUAGE)


@pytest.fixture
def scanned(window, qapp: QApplication, tmp_path: Path):
    folder = tmp_path / "scan"
    folder.mkdir()
    make_tree(folder, {"photos": {"a.jpg": b"a" * 300}, "notes.txt": b"n" * 20})
    window.start_scan(str(folder))
    _wait(qapp, lambda: window.results.outcome is not None and window._worker is None)
    return window.results.outcome.result.root


def test_action_names_read_like_part_of_a_sentence():
    assert action_name("&Move to Recycle Bin") == "Move to Recycle Bin"
    assert action_name("Export the chart…") == "Export the chart"
    assert action_name("Save && close...") == "Save & close"


def test_every_language_names_the_action_in_both_notices():
    for language in i18n.STRINGS:
        i18n.set_language(language)
        assert "Rescan" in busy_text("&Rescan…", scanning=True)
        assert "Rescan" in busy_text("Rescan", scanning=False)
    i18n.set_language("en")
    assert busy_text("Rescan", scanning=True) != busy_text("Rescan", scanning=False)


def test_menu_actions_stay_enabled_during_a_scan_and_explain_instead_of_running(window, scanned, monkeypatch):
    monkeypatch.setattr(window, "move_to_trash", lambda *_args, **_kwargs: pytest.fail("ran during a scan"))
    window._worker = object()  # a running scan
    window._update_actions()
    for key in ("trash", "permanent_delete", "rescan", "find", "export_json", "volumes"):
        assert window._actions[key].isEnabled(), key
    window.results.select_node(scanned.children[0])
    window._actions["trash"].trigger()
    assert window.statusBar().currentMessage() == busy_text(window._actions["trash"].text(), scanning=True)
    rescans = []
    monkeypatch.setattr(window, "start_scan", lambda *args, **_kwargs: rescans.append(args))
    window._actions["rescan"].trigger()
    assert rescans == []
    assert window.statusBar().currentMessage() == busy_text(window._actions["rescan"].text(), scanning=True)
    window._worker = None
    window._update_actions()
    window._actions["rescan"].trigger()  # once the scan is over the action simply runs
    assert len(rescans) == 1


def test_a_live_tree_before_any_result_offers_its_actions_with_the_notice(window, scanned):
    window.results._outcome = None  # a first scan: only the live tree is on screen
    window._worker = object()
    window._update_actions()
    assert window._actions["trash"].isEnabled() and window._actions["export_json"].isEnabled()
    window._worker = None
    window._update_actions()
    assert not window._actions["trash"].isEnabled() and not window._actions["export_json"].isEnabled()


def test_removals_from_menus_and_panels_explain_while_a_scan_runs(window, scanned):
    entry = scanned.children[0]
    window._worker = object()
    window.move_to_trash([entry])  # a context menu or a clean-up panel button calls these directly
    assert window.statusBar().currentMessage() == busy_text(tr("action_trash"), scanning=True)
    window.delete_permanently([entry])
    assert window.statusBar().currentMessage() == busy_text(tr("permanent_delete"), scanning=True)
    assert entry in scanned.children


def test_rescan_this_folder_in_the_context_menu_explains_while_a_scan_runs(window, scanned, monkeypatch):
    folder = next(child for child in scanned.children if child.is_dir)

    class ChoosingMenu(QMenu):
        def exec(self, *_args: object) -> None:  # instead of waiting for a click, choose Rescan this folder
            next(action for action in self.actions() if action.text() == tr("menu_rescan_here")).trigger()

    monkeypatch.setattr(main_window_module, "QMenu", ChoosingMenu)
    monkeypatch.setattr(window, "rescan_folder", lambda *_args, **_kwargs: pytest.fail("ran during a scan"))
    window._worker = object()
    window.show_menu_for(folder, [folder], window.mapToGlobal(window.rect().center()))
    assert window.statusBar().currentMessage() == busy_text(tr("menu_rescan_here"), scanning=True)


def test_another_operation_makes_scan_starting_actions_wait_too(window, scanned, monkeypatch):
    monkeypatch.setattr(main_window_module.QFileDialog, "getExistingDirectory",
                        lambda *_args, **_kwargs: pytest.fail("asked for a folder during an operation"))
    window._trash_worker = object()  # a move to the Recycle Bin is running
    window._update_actions()
    assert window._actions["open"].isEnabled()
    window._actions["open"].trigger()
    assert window.statusBar().currentMessage() == busy_text(window._actions["open"].text(), scanning=False)
    window._trash_worker = None
    window._worker = object()  # a scan alone does not hold up Open: choosing a folder starts a new scan
    assert not window._explain_busy(window._actions["open"].text(), scan=False)
