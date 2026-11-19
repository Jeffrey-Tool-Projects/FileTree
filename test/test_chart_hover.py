"""Moving the mouse over a chart stays cheap: tooltips wait for Qt's tooltip event (U-20261119-04)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QHelpEvent, QMouseEvent, QPixmap, QRegion
from PySide6.QtWidgets import QApplication, QProxyStyle, QStyle, QToolTip, QWidget

from je_file_tree.core.scanner import scan
from je_file_tree.gui import bar_chart, chart_tooltip
from je_file_tree.gui.bar_chart import BarChartWidget
from je_file_tree.gui.sunburst_widget import SunburstWidget
from je_file_tree.gui.tree_diagram import TreeDiagramWidget
from je_file_tree.gui.treemap_widget import TreemapWidget


@pytest.fixture
def tips(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, QWidget, QRect]]:
    """Every tooltip a chart asks for, instead of a real one (each costs tens of milliseconds)."""
    shown: list[tuple[str, QWidget, QRect]] = []
    monkeypatch.setattr(chart_tooltip.QToolTip, "showText",
                        lambda _position, text, widget, area: shown.append((text, widget, area)))
    monkeypatch.setattr(chart_tooltip.QToolTip, "hideText", lambda: shown.append(("", None, QRect())))
    return shown


def _move(widget: QWidget, point: QPoint) -> None:
    QApplication.sendEvent(widget, QMouseEvent(
        QEvent.Type.MouseMove, QPointF(point), QPointF(widget.mapToGlobal(point)), Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier))


def _rest(widget: QWidget, point: QPoint) -> None:
    QApplication.sendEvent(widget, QHelpEvent(QEvent.Type.ToolTip, point, widget.mapToGlobal(point)))


def _bars(sample_tree: Path) -> BarChartWidget:
    chart = BarChartWidget()
    chart.resize(500, 300)
    chart.set_view_root(scan(sample_tree).root)
    chart.grab()
    return chart


def test_moving_over_the_bars_shows_no_tooltip_until_the_mouse_rests(qapp, sample_tree, tips):
    chart = _bars(sample_tree)
    line = chart._row_height()
    for row in range(4):
        _move(chart, QPoint(100, line * row + 3))
    assert tips == [], "a tooltip per hover change cost 35-45 ms"
    assert chart._hover == 3
    _rest(chart, QPoint(100, line + 3))
    text, widget, area = tips[-1]
    assert "photos" in text and widget is chart
    assert area == chart._line_rect(1).toRect(), "Qt hides it once the mouse leaves the bar"
    _rest(chart, QPoint(100, line * 30))
    assert tips[-1][0] == "", "below the bars the tooltip goes away"
    chart.deleteLater()


def test_the_bars_draw_only_the_lines_asked_for(qapp, sample_tree, monkeypatch):
    chart = _bars(sample_tree)
    drawn: list[int] = []
    original = BarChartWidget._draw_row

    def counted(self, painter, index, *rest):
        drawn.append(index)
        original(self, painter, index, *rest)
    monkeypatch.setattr(BarChartWidget, "_draw_row", counted)
    line = chart._row_height()
    picture = QPixmap(chart.size())
    chart.render(picture, QPoint(), QRegion(0, line, 500, line))
    assert drawn == [1], "a hover change repaints its own line, not all of them"
    drawn.clear()
    chart.render(picture)
    assert drawn == [0, 1, 2, 3]
    chart.deleteLater()


class _CountingStyle(QProxyStyle):
    def __init__(self) -> None:
        super().__init__("Fusion")
        self.asked = 0

    def standardIcon(self, icon, option=None, widget=None):  # noqa: N802 - Qt override
        if icon == QStyle.StandardPixmap.SP_DirIcon:
            self.asked += 1
        return super().standardIcon(icon, option, widget)


def test_the_folder_icon_is_asked_of_the_style_once(qapp, sample_tree):
    chart = _bars(sample_tree)
    style = _CountingStyle()
    chart.setStyle(style)
    for _ in range(3):
        chart.grab()
    assert style.asked == 1, "each standardIcon call took 41-52 ms on Windows, per folder line and paint"
    other = _CountingStyle()
    chart.setStyle(other)
    chart.grab()
    assert other.asked == 1, "a new style draws its own icon"
    chart.deleteLater()


def test_the_bar_selection_repaints_only_its_lines(qapp, sample_tree, monkeypatch):
    chart = _bars(sample_tree)
    asked: list[QRect] = []
    monkeypatch.setattr(BarChartWidget, "update", lambda self, *area: asked.append(area[0] if area else None))
    rows = chart._current_rows()
    chart.set_selected(rows[1])
    chart.set_selected(rows[2])
    chart.set_selected(rows[2])
    assert asked == [chart._line_rect(1).toAlignedRect(), chart._line_rect(1).toAlignedRect(),
                     chart._line_rect(2).toAlignedRect()]
    chart.deleteLater()


def test_the_bars_rest_line_still_counts_the_entries_without_a_bar(qapp, sample_tree, monkeypatch):
    monkeypatch.setattr(bar_chart, "MAX_BARS", 2)
    chart = _bars(sample_tree)
    assert [node.name for node in chart._current_rows()] == ["big.bin", "photos"]
    assert chart._rest == (2, 250), "code (150 bytes) and notes.txt (100)"
    chart.deleteLater()


def _treemap(root) -> tuple[QWidget, QPoint]:
    widget = TreemapWidget()
    widget.resize(400, 300)
    widget.set_view_root(root)
    widget.grab()
    tile = next(tile for tile in widget._tiles if not tile.grouped and tile.node.name == "big.bin")
    return widget, QPoint(round(tile.rect.x + tile.rect.width / 2), round(tile.rect.y + tile.rect.height / 2))


def _sunburst(root) -> tuple[QWidget, QPoint]:
    widget = SunburstWidget()
    widget.resize(400, 400)
    widget.set_view_root(root)
    widget.grab()
    inner, ring = widget._radii()
    return widget, QPoint(200, round(200 - inner - ring / 2))


def _diagram(root) -> tuple[QWidget, QPoint]:
    widget = TreeDiagramWidget()
    widget.set_view_root(root)
    widget.resize(widget.sizeHint())
    widget.grab()
    return widget, widget.card_rect(widget.rows()[0]).center().toPoint()


@pytest.mark.parametrize("make", [_treemap, _sunburst, _diagram])
def test_the_other_charts_wait_for_the_mouse_to_rest_too(qapp, sample_tree, tips, make):
    widget, point = make(scan(sample_tree).root)
    for offset in range(5):
        _move(widget, point + QPoint(offset, 0))
    assert tips == []
    _rest(widget, point)
    assert tips and tips[-1][0] and tips[-1][1] is widget
    _rest(widget, QPoint(-50, -50))
    assert tips[-1][0] == ""
    widget.deleteLater()


def test_a_real_tooltip_event_reaches_the_qt_tooltip(qapp, sample_tree):
    chart = _bars(sample_tree)
    chart.show()
    _rest(chart, QPoint(100, 3))
    assert "big.bin" in QToolTip.text()
    QToolTip.hideText()
    chart.deleteLater()
