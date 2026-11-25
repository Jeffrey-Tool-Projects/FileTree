"""Cell painters."""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter
from PySide6.QtWidgets import QApplication, QStyle, QStyledItemDelegate, QStyleOptionViewItem

from je_file_tree.gui.colours import blend, contrast, luminance
from je_file_tree.gui.tree_model import SHARE_ROLE

_BAR_MARGIN = 3
_FADE, _FAINTEST = .025, .2
# On a light surface text reads best on a pale bar. On a dark one a bar that dark would vanish on the
# selected row, whose tint also keeps white text at 7:1, so the bar stays brighter there.
_TEXT_ON_LIGHT, _TEXT_ON_DARK = 7.0, 4.5
_DARK_SURFACE_LUMINANCE = .2


@lru_cache(maxsize=32)
def _bar_rgb(accent: int, surface: int, text: int) -> int:
    over, under, ink = QColor(accent), QColor(surface), QColor(text)
    wanted = _TEXT_ON_DARK if luminance(under) < _DARK_SURFACE_LUMINANCE else _TEXT_ON_LIGHT
    amount = 1.0
    while amount > _FAINTEST and contrast(blend(over, under, amount), ink) < wanted:
        amount -= _FADE
    return blend(over, under, amount).rgb()


def bar_colour(accent: QColor, surface: QColor, text: QColor) -> QColor:
    """The share bar's colour: the accent, faded towards ``surface`` until ``text`` on it is readable.

    Opaque, so it is the same on selected rows; cached, because every painted cell asks for it.
    """
    return QColor(_bar_rgb(accent.rgb(), surface.rgb(), text.rgb()))


class PathTailDelegate(QStyledItemDelegate):
    """Elides a folder path from the left, keeping its nearest folders; the tooltip keeps the whole path."""

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> None:
        """Qt: the usual cell options, eliding at the start instead of the view's mode."""
        super().initStyleOption(option, index)
        option.textElideMode = Qt.TextElideMode.ElideLeft


class ShareBarDelegate(QStyledItemDelegate):
    """Draws a cell's share (0..1, from ``SHARE_ROLE``) as a bar behind its percentage text."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem,
              index: QModelIndex | QPersistentModelIndex) -> None:
        """Qt: the usual cell with a bar underneath the text."""
        share = index.data(SHARE_ROLE)
        style = option.widget.style() if option.widget is not None else QApplication.style()
        style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)
        if isinstance(share, float) and share > 0:
            area = QRectF(option.rect).adjusted(_BAR_MARGIN, _BAR_MARGIN, -_BAR_MARGIN, -_BAR_MARGIN)
            area.setWidth(max(1.0, area.width() * min(share, 1.0)))
            palette = option.palette  # its accent: views use a pale selection tint as their highlight
            colour = bar_colour(palette.accent().color(), palette.base().color(), palette.text().color())
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(colour)
            painter.drawRoundedRect(area, 2, 2)
            painter.restore()
        text_option = QStyleOptionViewItem(option)
        self.initStyleOption(text_option, index)
        text_option.backgroundBrush = QBrush()
        # The panel (selection, hover) is already drawn under the bar; drawing it
        # again with the text would cover the bar.
        text_option.state &= ~(QStyle.StateFlag.State_Selected | QStyle.StateFlag.State_MouseOver)
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, text_option, painter, option.widget)
