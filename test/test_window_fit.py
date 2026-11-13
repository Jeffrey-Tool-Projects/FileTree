"""Windows open at a size adapted to the screen: cut back on small screens, grown on large ones."""

import ast
from pathlib import Path

import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QDialog

from je_file_tree.gui import window_fit
from je_file_tree.gui.help_dialog import HelpDialog
from je_file_tree.gui.window_fit import DESIGN, fit_window, fitted_size

GUI = Path(window_fit.__file__).parent
# Not top-level windows: an off-screen chart rendered for a report, and a diagram sized to its content.
_NOT_WINDOWS = {"report_export.py", "tree_diagram.py", "window_fit.py"}


def test_the_design_screen_keeps_the_preferred_size():
    assert fitted_size(1240, 800, DESIGN) == QSize(1240, 800)
    assert fitted_size(560, 170, DESIGN) == QSize(560, 170)


def test_an_unknown_screen_keeps_the_preferred_size():
    assert fitted_size(1560, 540, None) == QSize(1560, 540)
    assert fitted_size(1560, 540, QSize(0, 0)) == QSize(1560, 540)


@pytest.mark.parametrize("available", [QSize(1366, 728), QSize(1280, 680), QSize(1024, 728), QSize(800, 560)])
def test_a_small_screen_cuts_the_window_back_inside_the_screen(available):
    for width, height in ((1560, 540), (1240, 800), (900, 760), (560, 170)):
        size = fitted_size(width, height, available)
        assert size.width() <= min(width, available.width()) and size.height() <= min(height, available.height())
        assert size.width() < available.width() or width < available.width()  # room for the frame
    assert fitted_size(560, 170, QSize(1366, 728)) == QSize(560, 170)  # what fits is left alone


def test_a_large_screen_grows_the_window_in_proportion_up_to_a_limit():
    assert fitted_size(1000, 600, QSize(2560, 1387)) == QSize(1333, 800)
    huge = fitted_size(1000, 600, QSize(7680, 4200))
    assert huge == QSize(1500, 900)  # never more than half as large again
    wide = fitted_size(1000, 600, QSize(3840, 1040))  # an ultrawide screen is no taller: no growth
    assert wide == QSize(1000, 600)


def test_a_tiny_screen_never_asks_for_more_than_it_has():
    size = fitted_size(1240, 800, QSize(240, 120))
    assert size.width() <= 240 and size.height() <= 120 and size.width() > 0 and size.height() > 0


def test_a_window_follows_the_screen_it_opens_on(qapp, monkeypatch):
    dialog = QDialog()
    monkeypatch.setattr(window_fit, "_available", lambda _window: QSize(1366, 728))
    fit_window(dialog, 1560, 540)
    assert dialog.size() == QSize(1256, 540)
    monkeypatch.setattr(window_fit, "_available", lambda _window: QSize(2560, 1387))
    fit_window(dialog, 1560, 540)
    assert dialog.size() == QSize(2080, 720)
    dialog.deleteLater()


def test_a_real_dialog_opens_inside_a_small_screen(qapp, monkeypatch):
    monkeypatch.setattr(window_fit, "_available", lambda _window: QSize(600, 400))
    dialog = HelpDialog()
    assert dialog.width() <= 552 and dialog.height() <= 368
    dialog.deleteLater()


def test_no_window_is_opened_at_a_fixed_pixel_size():
    """``resize(number, number)`` on a window bypasses the screen; windows use ``fit_window``."""
    fixed = []
    for source in sorted(GUI.glob("*.py")):
        if source.name in _NOT_WINDOWS:
            continue
        for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "resize"
                    and len(node.args) == 2 and all(isinstance(arg, ast.Constant) for arg in node.args)):
                fixed.append(f"{source.name}:{node.lineno}")
    assert not fixed
