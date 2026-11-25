"""A short window folds the results page's extras, a tall one shows them, and the user's choice wins."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QBoxLayout

from test_gui import window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.core.scanner import scan
from je_file_tree.gui.window_settings import RESULTS_PAGE
from je_file_tree.gui.scan_worker import analyse


@pytest.fixture
def page(window, qapp, sample_tree):
    window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    window.results.show_outcome(analyse(scan(sample_tree)))
    window.pages.setCurrentIndex(RESULTS_PAGE)
    window.show()

    def resize(height: int):
        window.resize(1280, height)
        for _ in range(8):
            qapp.processEvents()
        return window.results
    return resize


def test_a_short_window_folds_the_extras_and_a_tall_one_shows_them_again(page):
    results = page(1000)
    assert not results._short_layout.short and results.highlights.toggle.isChecked()
    tall = results.minimumSizeHint().height()
    results = page(560)
    assert results._short_layout.short and not results.highlights.toggle.isChecked()
    assert results.overview._card_layouts[0].direction() == QBoxLayout.Direction.LeftToRight
    assert not results._analysis_hint.isVisible() and results._short_layout._saved > 0
    assert results.minimumSizeHint().height() < tall
    results = page(1000)
    assert not results._short_layout.short and results.highlights.toggle.isChecked()
    assert results.overview._card_layouts[0].direction() == QBoxLayout.Direction.TopToBottom
    assert results._analysis_hint.isVisible()


def test_the_layout_does_not_flip_at_any_height(page, qapp):
    results = page(1000)
    for height in range(980, 520, -20):
        results = page(height)
        state = results._short_layout.short
        for _ in range(6):
            qapp.processEvents()
            assert results._short_layout.short == state, height


def test_the_users_choice_of_open_highlights_is_kept(page):
    results = page(560)
    results.highlights.toggle.click()  # open them although the window is short
    assert results.highlights.toggle.isChecked()
    results = page(1000)
    results = page(560)
    assert results._short_layout.short and results.highlights.toggle.isChecked()
    results.highlights.toggle.click()
    results = page(1000)
    assert not results.highlights.toggle.isChecked()


def test_an_idle_window_does_not_keep_laying_itself_out(page, qapp, monkeypatch):
    results = page(560)
    calls = []
    monkeypatch.setattr(results._short_layout, "fit", calls.append)
    for _ in range(20):
        qapp.processEvents()
    assert len(calls) <= 2


@pytest.mark.parametrize("percent", [150, 200])
def test_a_changed_text_size_settles(page, qapp, percent):
    results = page(900)
    menu = results.window().text_size_menu
    try:
        menu.choose(percent)
        for _ in range(10):
            qapp.processEvents()
        state = results._short_layout.short
        for _ in range(10):
            qapp.processEvents()
            assert results._short_layout.short == state
    finally:
        menu.choose(100)


def test_totals_stay_readable_beside_their_names(page):
    results = page(560)
    for caption, value in zip(results.overview.captions, results.overview.values, strict=True):
        assert caption.text() and value.text() and value.accessibleName() == caption.text()
