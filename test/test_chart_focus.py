"""Keys meant for the chart never reach the path box, where Enter scanned the whole root (U-20261119-01)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from conftest import make_tree
from je_file_tree.gui import i18n
from je_file_tree.gui.app import create_window
from je_file_tree.gui.results_view import CHART_TAB


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
    main.show()
    yield main
    main.close()
    _wait(qapp, lambda: main._close_ready)
    main.deleteLater()
    QCoreApplication.sendPostedEvents(main, QEvent.Type.DeferredDelete)
    i18n.set_language(i18n.DEFAULT_LANGUAGE)


def _scan_from_the_path_box(window, qapp: QApplication, folder: Path) -> None:
    """Type the folder and press Enter, as a user starts a scan from the box at the top."""
    window.path_edit.setFocus()
    window.path_edit.setText(str(folder))
    QTest.keyClick(window.path_edit, Qt.Key.Key_Return)
    _wait(qapp, lambda: window.results.outcome is not None and window._worker is None)


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    root = tmp_path / "scan"
    root.mkdir()
    make_tree(root, {"photos": {"2024": {"a.jpg": b"a" * 400}, "b.jpg": b"b" * 200}, "notes.txt": b"n" * 20})
    return root


def test_a_scan_started_from_the_path_box_moves_focus_to_the_results(window, qapp, folder):
    _scan_from_the_path_box(window, qapp, folder)
    assert window.focusWidget() is window.results.tree


def test_enter_and_backspace_after_the_chart_buttons_stay_in_the_chart(window, qapp, folder, monkeypatch):
    _scan_from_the_path_box(window, qapp, folder)
    window.path_edit.setFocus()  # the worst case: the path box has focus while the chart is used
    results = window.results
    results.tabs.setCurrentIndex(CHART_TAB)
    root = results.tree_model.root
    photos = next(child for child in root.children if child.name == "photos")
    scans = []
    monkeypatch.setattr(window, "_begin_scan", lambda *args, **kwargs: scans.append(args))
    results.breadcrumbs.navigate.emit(photos)  # an ancestor button or Back/Forward
    assert window.focusWidget() is results.charts.current_chart()
    QTest.mouseClick(results._treemap_up, Qt.MouseButton.LeftButton)
    assert results.charts.view_root is root
    assert window.focusWidget() is results.charts.current_chart()
    for key in (Qt.Key.Key_Return, Qt.Key.Key_Backspace):
        QTest.keyClick(window.focusWidget(), key)
    assert scans == [], "a key meant for the chart scanned the whole root again"
    assert window.path_edit.text() == str(folder), "Backspace edited the path box"
    for button in (results.breadcrumbs.back, results.breadcrumbs.forward):
        window.path_edit.setFocus()
        button.setEnabled(True)
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)
        assert window.focusWidget() is results.charts.current_chart()
