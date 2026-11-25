"""The bar chart: one horizontal bar per entry of a folder, the largest first.

Easier to read exactly than the treemap: every entry has its name, its size and its share of the
folder in plain text, and the bars are scaled to the largest entry so small differences show. Only
the ``MAX_BARS`` largest entries get a bar; the rest share one line.

Only the lines on screen are drawn, and a hover change repaints just the two lines it changes: with
every line drawn, each repaint took about 19 ms (measured 2026-11-19, 100 bars, U-20261119-04). The
folder icon is asked of the style once: each ``standardIcon`` call took 41-52 ms on Windows, per folder line.
"""

from __future__ import annotations

import heapq
import html

from PySide6.QtCore import QEvent, QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QContextMenuEvent, QHelpEvent, QIcon, QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QStyle, QWidget

from je_file_tree.core.analysis import category_of, extension_of
from je_file_tree.core.formatting import AUTO_UNIT, format_count, format_share, format_size
from je_file_tree.core.node import Node
from je_file_tree.gui.node_text import node_name, node_path
from je_file_tree.gui.chart_palette import CATEGORY_COLOURS
from je_file_tree.gui.chart_tooltip import show_chart_tip
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.text_scale import text_scaled

MAX_BARS = 100
_NAME_SHARE = 0.34  # of the width, at most _NAME_MAX pixels
_NAME_MAX = 280
_VALUE_WIDTH = 150
_GAP = 8
_FOLDER_COLOUR = "#5b8def"
_REST_COLOUR = "#8f8f8f"


def bar_colour(node: Node) -> QColor:
    """Folders in one colour, files in the colour of their type (the treemap's legend)."""
    if node.is_dir:
        return QColor(_FOLDER_COLOUR)
    return QColor(CATEGORY_COLOURS[category_of(extension_of(node.name))])


class BarChartWidget(QWidget):
    """Bars for the entries of one folder; click selects, double-click opens a folder, right-click asks for a menu."""

    node_clicked = Signal(object)
    view_root_changed = Signal(object)
    context_menu_requested = Signal(object, QPoint)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.unit = AUTO_UNIT
        self._view_root: Node | None = None
        self._rows: list[Node] | None = None  # None: to be read from the folder at the next paint
        self._rest: tuple[int, int] = (0, 0)  # entries without a bar: count, size
        self._hover: int | None = None
        self._selected: Node | None = None
        self._folder_icon: QIcon | None = None  # the style's, asked for once (it is slow)

    # --- the same interface as the treemap --------------------------------

    @property
    def view_root(self) -> Node | None:
        """The folder shown."""
        return self._view_root

    def set_view_root(self, node: Node | None) -> None:
        """Show the entries of ``node`` (a folder; a file shows its folder)."""
        if node is not None and not node.is_dir:
            node = node.parent
        self._view_root = node
        self._hover = None
        self.invalidate()
        self.view_root_changed.emit(node)

    def zoom_out(self) -> None:
        """Show the parent of the current folder."""
        if self._view_root is not None and self._view_root.parent is not None:
            self.set_view_root(self._view_root.parent)

    def set_selected(self, node: Node | None) -> None:
        """Outline ``node`` when it has a bar."""
        if node is self._selected:
            return
        if self._rows is not None:
            for old in (self._selected, node):
                if old is not None and old in self._rows:
                    self._update_line(self._rows.index(old))
        else:
            self.update()
        self._selected = node

    def invalidate(self) -> None:
        """Read the folder again (after a scan step, a deletion or a rescan)."""
        self._rows = None
        self.updateGeometry()
        self.update()

    def node_at(self, y: float) -> Node | None:
        """The entry whose bar is at height ``y`` (None on the summary line or below the bars)."""
        rows = self._current_rows()
        index = int(y // self._row_height())
        return rows[index] if 0 <= index < len(rows) else None

    # --- Qt -----------------------------------------------------------------

    def sizeHint(self) -> QSize:
        """Qt: one line per bar, plus one for the entries without a bar."""
        lines = len(self._current_rows()) + (1 if self._rest[0] else 0)
        return QSize(400, max(lines, 1) * self._row_height())

    def minimumSizeHint(self) -> QSize:
        """Qt: tall enough for every line, so a scroll area scrolls rather than squeezes."""
        return QSize(200, self.sizeHint().height())

    def paintEvent(self, event: QPaintEvent) -> None:
        """Qt: draw the bars."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        root = self._view_root
        if root is None:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, tr("treemap_empty"))
            return
        rows = self._current_rows()
        if not rows:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, tr("bars_empty_folder"))
            return
        largest = max(rows[0].accounted_size, 1)
        height = self._row_height()
        first = max(event.rect().top() // height, 0)
        last = event.rect().bottom() // height
        for index in range(first, min(last + 1, len(rows))):
            node = rows[index]
            self._draw_row(painter, index, node, node.accounted_size / largest, root.accounted_size)
        count, size = self._rest
        if count and first <= len(rows) <= last:
            label = tr("bars_more", count=format_count(count), size=format_size(size, self.unit))
            self._draw_line(painter, len(rows), label, None, min(size / largest, 1.0), size, root.accounted_size)

    def event(self, event: QEvent) -> bool:
        """Qt: describe the bar under the mouse once it rests (``chart_tooltip``); a new style, a new icon."""
        if event.type() == QEvent.Type.StyleChange:
            self._folder_icon = None
        if event.type() == QEvent.Type.ToolTip and isinstance(event, QHelpEvent):
            node = self.node_at(event.pos().y())
            if node is None:
                return show_chart_tip(self, event, None)
            index = int(event.pos().y() // self._row_height())
            return show_chart_tip(self, event, self._describe(node), self._line_rect(index).toRect())
        return super().event(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Qt: highlight the bar under the mouse."""
        node = self.node_at(event.position().y())
        self._set_hover(None if node is None else int(event.position().y() // self._row_height()))
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """Qt: drop the highlight when the mouse leaves."""
        self._set_hover(None)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Qt: a left click selects the entry."""
        if event.button() == Qt.MouseButton.LeftButton:
            node = self.node_at(event.position().y())
            if node is not None:
                self.node_clicked.emit(node)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Qt: a double click on a folder shows its entries."""
        node = self.node_at(event.position().y())
        if node is not None and node.is_dir and not node.is_link:
            self.set_view_root(node)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Qt: ask the window for the menu of the entry under the mouse (or of the folder shown)."""
        node = self.node_at(event.pos().y())
        self.context_menu_requested.emit(node if node is not None else self._view_root, event.globalPos())

    # --- drawing -----------------------------------------------------------

    def _set_hover(self, index: int | None) -> None:
        if index != self._hover:
            for line in (self._hover, index):
                if line is not None:
                    self._update_line(line)
            self._hover = index

    def _update_line(self, index: int) -> None:
        self.update(self._line_rect(index).toAlignedRect())

    def _row_height(self) -> int:
        return self.fontMetrics().height() + 10

    def _current_rows(self) -> list[Node]:
        """The entries with a bar, the largest first (read from the folder when it changed)."""
        if self._rows is None:
            children = list(self._view_root.children) if self._view_root is not None else []
            sizes = [node.accounted_size for node in children]  # each size read once: a property call
            largest = heapq.nlargest(MAX_BARS, range(len(children)), key=sizes.__getitem__)
            self._rows = [children[index] for index in largest]
            shown = sum(sizes[index] for index in largest)
            self._rest = (len(children) - len(largest), sum(sizes) - shown)
        return self._rows

    def _draw_row(self, painter: QPainter, index: int, node: Node, fraction: float, total: int) -> None:
        if index == self._hover:
            painter.fillRect(self._line_rect(index), self.palette().alternateBase())
        self._draw_line(painter, index, node.name, node, fraction, node.accounted_size, total)
        if node is self._selected:
            painter.setPen(self.palette().highlight().color())
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self._line_rect(index).adjusted(1, 1, -1, -1))

    def _draw_line(self, painter: QPainter, index: int, label: str, node: Node | None,  # noqa: PLR0913
                   fraction: float, size: int, total: int) -> None:
        line = self._line_rect(index)
        height = line.height()
        name_width = min(self.width() * _NAME_SHARE, text_scaled(_NAME_MAX))
        icon_size = self.fontMetrics().height()
        text_colour = self.palette().text().color()
        if node is not None and node.is_dir:
            if self._folder_icon is None:
                self._folder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
            self._folder_icon.paint(painter, int(line.x() + 4), int(line.y() + (height - icon_size) / 2),
                                    icon_size, icon_size)
        name_rect = QRectF(line.x() + icon_size + 8, line.y(), name_width - icon_size - 8, height)
        painter.setPen(text_colour)
        align = Qt.AlignmentFlag.AlignVCenter
        painter.drawText(name_rect, align | Qt.AlignmentFlag.AlignLeft,
                         self.fontMetrics().elidedText(label, Qt.TextElideMode.ElideMiddle, int(name_rect.width())))
        bar_left = name_width + _GAP
        value_width = text_scaled(_VALUE_WIDTH)
        bar_space = max(self.width() - bar_left - value_width - _GAP, 0)
        bar = QRectF(bar_left, line.y() + height * 0.2, max(bar_space * fraction, 1.0), height * 0.6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bar_colour(node) if node is not None else QColor(_REST_COLOUR))
        painter.drawRoundedRect(bar, 2, 2)
        share = format_share(size / total) if total else ""
        value = QRectF(self.width() - value_width, line.y(), value_width - 6, height)
        painter.setPen(text_colour)
        painter.drawText(value, align | Qt.AlignmentFlag.AlignRight, f"{format_size(size, self.unit)}   {share}")

    def _line_rect(self, index: int) -> QRectF:
        height = self._row_height()
        return QRectF(0, index * height, self.width(), height)

    def _describe(self, node: Node) -> str:
        root = self._view_root
        share = node.accounted_size / root.accounted_size if root is not None and root.accounted_size else 0.0
        return tr("treemap_tooltip", name=html.escape(node_name(node)),
                  size=format_size(node.accounted_size, self.unit), share=format_share(share),
                  path=html.escape(node_path(node)))
