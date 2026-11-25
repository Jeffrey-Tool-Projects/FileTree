"""A page fills its window while it fits, and scrolls instead of stretching the window when it does not."""

import pytest
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from test_gui import window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.core.scanner import scan
from je_file_tree.gui.window_settings import RESULTS_PAGE
from je_file_tree.gui.scan_worker import analyse
from je_file_tree.gui.scrolling_page import ScrollingPage


def _settle(qapp) -> None:
    for _ in range(5):  # a shown or hidden scroll bar asks for one more layout
        qapp.processEvents()


@pytest.fixture
def page(qapp):
    content = QWidget()
    layout = QVBoxLayout(content)
    label = QLabel("wrapping words " * 200)
    label.setWordWrap(True)  # its preferred height is far above the minimum
    label.setMinimumSize(100, 60)
    layout.addWidget(label)
    area = ScrollingPage(content)
    area.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    yield area, label
    area.deleteLater()


def test_a_page_that_fits_fills_the_window_without_scroll_bars(page, qapp):
    area, _label = page
    area.resize(400, 300)
    area.show()
    _settle(qapp)
    assert area.widget().size() == area.viewport().size() == QSize(400, 300)
    assert not area.verticalScrollBar().isVisible()


def test_a_page_below_its_minimum_scrolls_and_follows_a_changed_minimum(page, qapp):
    area, label = page
    area.resize(400, 300)
    area.show()
    label.setMinimumHeight(900)
    _settle(qapp)
    assert area.height() == 300 and area.widget().height() >= 900
    assert area.verticalScrollBar().isVisible() and not area.horizontalScrollBar().isVisible()
    label.setMinimumHeight(60)
    _settle(qapp)
    assert area.widget().size() == area.viewport().size() == QSize(400, 300)


def test_results_never_stretch_a_small_window(window, qapp, sample_tree):
    window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    window.results.show_outcome(analyse(scan(sample_tree)))
    window.pages.setCurrentIndex(RESULTS_PAGE)
    window.show()
    window.resize(1000, 500)
    _settle(qapp)
    assert window.size() == QSize(1000, 500)
    assert window.results.height() >= window.results.minimumSizeHint().height()
