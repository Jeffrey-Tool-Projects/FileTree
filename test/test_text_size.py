"""View → Text size: one remembered size for every text, followed by open windows, lists and the help."""

import pytest
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLabel, QTableWidget

from test_gui import window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.core.scanner import scan
from je_file_tree.gui import text_scale, window_fit
from je_file_tree.gui.app import create_window
from je_file_tree.gui.help_dialog import HelpDialog
from je_file_tree.gui.main_window import RESULTS_PAGE
from je_file_tree.gui.scan_worker import analyse
from je_file_tree.gui.text_size import neighbour, saved_text_size, text_size_controller
from je_file_tree.gui.themes import theme_controller


@pytest.fixture(autouse=True)
def _system_size_afterwards(qapp):
    yield
    text_size_controller().apply(text_scale.DEFAULT_TEXT_SIZE)


def _points() -> float:
    return QApplication.font().pointSizeF()


def test_a_chosen_size_reaches_open_and_later_widgets_and_is_remembered(window, qapp):
    theme_controller().apply("dark")  # an application style sheet is active
    try:
        system, heading = _points(), window.results.overview.values[0].font().pointSizeF()
        window.text_size_menu.actions_by_size[150].trigger()
        assert _points() == pytest.approx(1.5 * system)
        assert window.path_edit.font().pointSizeF() == pytest.approx(1.5 * system)
        assert window.results.overview.values[0].font().pointSizeF() == pytest.approx(1.5 * heading)
        later = QLabel()
        assert later.font().pointSizeF() == pytest.approx(1.5 * system)
        assert int(window.settings.value("text_size")) == 150
        window.text_size_menu.reset.trigger()
        assert _points() == pytest.approx(system)
        assert window.results.overview.values[0].font().pointSizeF() == pytest.approx(heading)
    finally:
        theme_controller().apply("system")


def test_larger_smaller_and_reset_step_through_the_offered_sizes(window):
    menu = window.text_size_menu
    menu.larger.trigger()
    assert text_scale.text_percent() == 110 and menu.actions_by_size[110].isChecked()
    for _ in text_scale.TEXT_SIZES:
        menu.larger.trigger()
    assert text_scale.text_percent() == 200 and not menu.larger.isEnabled() and menu.smaller.isEnabled()
    for _ in text_scale.TEXT_SIZES:
        menu.smaller.trigger()
    assert text_scale.text_percent() == 90 and not menu.smaller.isEnabled() and menu.larger.isEnabled()
    menu.reset.trigger()
    assert text_scale.text_percent() == 100 and menu.actions_by_size[100].isChecked()
    assert neighbour(90, -1) == 90 and neighbour(200, 1) == 200
    sequences = {shortcut.toString() for action in (menu.larger, menu.smaller, menu.reset)
                 for shortcut in action.shortcuts()}
    assert {"Ctrl+=", "Ctrl+-", "Ctrl+0"} <= sequences


def test_a_saved_size_is_used_at_the_start_and_unknown_values_mean_the_default(window):
    system = _points()
    window.settings.setValue("text_size", 125)
    other = create_window(window.settings)
    assert other.text_size_menu.actions_by_size[125].isChecked()
    assert window.text_size_menu.actions_by_size[125].isChecked()  # every tab shows the one choice
    assert _points() == pytest.approx(1.25 * system)
    other.close()
    other.deleteLater()
    for invalid in ("", "huge", "130", "-1", "99999999999999999999", "²"):
        window.settings.setValue("text_size", invalid)
        assert saved_text_size(window.settings) == 100, invalid


def test_a_language_change_keeps_the_text_size(window):
    system = _points()
    window.text_size_menu.choose(150)
    try:
        for language in ("ja", "zh-TW"):
            window.change_language(language)
            assert _points() == pytest.approx(1.5 * system)
        assert window.text_size_menu.title().startswith("文字大小")
        assert window.text_size_menu.actions_by_size[100].text() == "100%（系統大小）"
    finally:
        window.change_language("en")


def test_lists_keep_columns_rows_and_hidden_columns_in_proportion(window, qapp, sample_tree):
    window.results.show_outcome(analyse(scan(sample_tree)))
    tree, table = window.results.tree, window.results.largest_table
    header = tree.header()
    tree.setColumnHidden(2, False)
    widths = {column: header.sectionSize(column) for column in (0, 1, 2)}
    tree.setColumnHidden(2, True)
    selected = window.results.tree.currentIndex()
    rows = table.verticalHeader().defaultSectionSize()
    window.text_size_menu.choose(200)
    assert tree.isColumnHidden(2) and tree.currentIndex() == selected
    assert header.sectionSize(0) == 2 * widths[0] and header.sectionSize(1) == 2 * widths[1]
    tree.setColumnHidden(2, False)
    assert header.sectionSize(2) == 2 * widths[2]
    assert table.verticalHeader().defaultSectionSize() == text_scale.line_height(table) > rows
    window.text_size_menu.choose(100)
    assert header.sectionSize(0) == widths[0] and table.verticalHeader().defaultSectionSize() == rows


def test_plain_table_rows_only_grow_when_text_no_longer_fits(qapp):
    table = QTableWidget(2, 1)
    table.verticalHeader().setDefaultSectionSize(200)
    text_scale.fit_rows(table)
    assert table.verticalHeader().defaultSectionSize() == 200
    table.verticalHeader().setDefaultSectionSize(table.verticalHeader().minimumSectionSize())
    text_scale.fit_rows(table)
    assert table.verticalHeader().defaultSectionSize() >= text_scale.line_height(table)


def test_fonts_sized_in_points_or_pixels_are_scaled(qapp):
    points, pixels = QFont(), QFont()
    points.setPointSizeF(10)
    pixels.setPixelSize(14)
    assert text_scale.scaled_font(points, 1.5).pointSizeF() == pytest.approx(15)
    assert text_scale.scaled_font(pixels, 1.5).pixelSize() == 21
    assert points.pointSizeF() == 10 and pixels.pixelSize() == 14


def test_the_tree_diagram_cards_grow_with_their_text(window, sample_tree):
    window.results.show_outcome(analyse(scan(sample_tree)))
    diagram = window.results.charts.tree
    card = diagram.card_rect(diagram.rows()[0])
    window.text_size_menu.choose(200)
    assert diagram.card_rect(diagram.rows()[0]).size() == card.size() * 2
    assert diagram._zoom == 1.0  # the chart's own zoom is a separate choice


def test_a_changed_size_redraws_the_cached_treemap(window, sample_tree):
    window.results.show_outcome(analyse(scan(sample_tree)))
    chart = window.results.charts.treemap
    chart.grab()
    assert chart._pixmap is not None
    window.text_size_menu.choose(150)
    assert chart._pixmap is None


def test_the_help_is_larger_than_labels_and_its_own_commands_change_the_size(window, qapp):
    dialog = HelpDialog(window, window.text_size_menu)
    reading = dialog.browser.document().defaultFont().pointSizeF()
    assert reading >= 1.25 * _points()
    assert window.text_size_menu.larger in dialog.actions()  # its shortcut works in the modal window
    window.text_size_menu.choose(150)
    assert dialog.browser.document().defaultFont().pointSizeF() == pytest.approx(1.5 * reading)
    dialog.deleteLater()


def test_windows_open_larger_for_larger_text_but_stay_on_the_screen(window, monkeypatch):
    monkeypatch.setattr(window_fit, "_available", lambda _window: QSize(1280, 672))
    window.text_size_menu.choose(200)
    small, large = QLabel(), QLabel()
    window_fit.fit_window(small, 400, 200)
    window_fit.fit_window(large, 1100, 600)
    assert small.size() == QSize(800, 400)
    assert large.width() <= 1280 * .92 and large.height() <= 672 * .92
    window.text_size_menu.choose(90)
    window_fit.fit_window(small, 400, 200)
    assert small.size() == QSize(400, 200)  # smaller text never makes a cramped window


@pytest.mark.parametrize("percent", text_scale.TEXT_SIZES)
def test_the_window_fits_a_small_screen_at_every_size(window, qapp, sample_tree, percent):
    window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    window.results.show_outcome(analyse(scan(sample_tree)))
    window.pages.setCurrentIndex(RESULTS_PAGE)
    window.text_size_menu.choose(percent)
    window.show()
    window.resize(1280, 640)
    qapp.processEvents()
    assert window.height() == 640  # results that need more height scroll instead of stretching the window
