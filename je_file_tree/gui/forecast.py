"""Free-space forecast for the drive overview: settings, the data file, texts and a used-space sparkline."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QPointF, QSettings, QStandardPaths, Qt
from PySide6.QtGui import QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from je_file_tree.core.forecast import (
    HORIZON_DAYS, MAX_SAMPLES, MIN_INTERVAL, MIN_SAMPLES, MIN_SPAN_DAYS, WINDOW_DAYS, Forecast, ForecastState,
)
from je_file_tree.core.formatting import format_count, format_size
from je_file_tree.gui.i18n import tr

SETTING = "forecast_enabled"
TREND_ROLE = Qt.ItemDataRole.UserRole + 21
_SPARK_WIDTH = 56
_SPARK_MARGIN = 4
_MIN_POINTS = 2
_YEAR_DAYS = 365


def forecast_file() -> Path | None:
    """The observation file in FileTree's local application data, or None when the OS reports no location."""
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    return Path(location) / "forecast" / "volumes.json" if location else None


def recording_enabled(settings: QSettings) -> bool:
    """Whether opening the drive overview records a used-space sample; default is enabled."""
    enabled = settings.value(SETTING, True)
    return not (enabled is False or str(enabled).lower() == "false")


def _date(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")


def forecast_text(result: Forecast | None, unit: str, *, recording: bool) -> str:
    """One short line for the forecast column."""
    if result is None:
        return tr("forecast_off") if not recording else tr("forecast_unknown")
    if result.state is ForecastState.NOT_ENOUGH_DATA:
        return tr("forecast_not_enough")
    if result.state is ForecastState.STABLE_OR_SHRINKING:
        return tr("forecast_stable")
    rate = format_size(round(result.bytes_per_day), unit)
    if result.full_at is None:
        return tr("forecast_not_soon", rate=rate, years=format_count(round(HORIZON_DAYS / _YEAR_DAYS)))
    return tr("forecast_growing", rate=rate, date=_date(result.full_at))


def forecast_tooltip(result: Forecast | None, *, recording: bool) -> str:
    """Explain what the estimate is based on."""
    if result is None:
        return tr("forecast_off_tip") if not recording else tr("forecast_unknown_tip")
    days = f"{result.span_days:.1f}"
    if result.state is ForecastState.NOT_ENOUGH_DATA:
        return tr("forecast_not_enough_tip", count=format_count(result.samples), days=days,
                  needed=format_count(MIN_SAMPLES), needed_days=f"{MIN_SPAN_DAYS:g}")
    return tr("forecast_estimate_tip", count=format_count(result.samples), days=days, window=f"{WINDOW_DAYS:g}")


def record_tip() -> str:
    """What the recording setting stores, with the store's actual bounds."""
    return tr("forecast_record_tip", hours=f"{MIN_INTERVAL / 3600:g}", count=format_count(MAX_SAMPLES))


def sort_value(result: Forecast | None) -> float:
    """Sooner full dates first; growing without a date, then not growing, then unknown."""
    if result is None:
        return float("inf")
    if result.full_at is not None:
        return result.full_at
    order = {ForecastState.GROWING: 1e18, ForecastState.STABLE_OR_SHRINKING: 2e18}
    return order.get(result.state, 3e18)


class SparklineDelegate(QStyledItemDelegate):
    """Draw the recent used share as a small line at the start of the cell, then the forecast text."""

    def paint(self, painter: QPainter, option, index) -> None:
        """Qt: a palette-coloured polyline from ``TREND_ROLE`` (used/total shares, oldest first)."""
        trend = index.data(TREND_ROLE)
        if not isinstance(trend, tuple) or len(trend) < _MIN_POINTS:
            super().paint(painter, option, index)
            return
        option = QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        if selected:
            painter.fillRect(option.rect, option.palette.highlight())
        area = option.rect.adjusted(_SPARK_MARGIN, _SPARK_MARGIN, 0, -_SPARK_MARGIN)
        area.setWidth(_SPARK_WIDTH)
        low, high = min(trend), max(trend)
        spread = high - low
        step = area.width() / (len(trend) - 1)
        points = [QPointF(area.left() + number * step,
                          area.center().y() if spread <= 0 else area.bottom() - (value - low) / spread * area.height())
                  for number, value in enumerate(trend)]
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colour = option.palette.highlightedText() if selected else option.palette.link()
        painter.setPen(QPen(colour.color(), 1.5))
        painter.drawPolyline(QPolygonF(points))
        text_rect = option.rect.adjusted(_SPARK_WIDTH + 2 * _SPARK_MARGIN, 0, -_SPARK_MARGIN, 0)
        painter.setPen(option.palette.highlightedText().color() if selected else option.palette.text().color())
        text = option.fontMetrics.elidedText(option.text, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), text)
        painter.restore()
