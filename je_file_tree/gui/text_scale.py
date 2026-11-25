"""The chosen interface text size, as plain values every widget can lay itself out by.

The choice itself (menu, saving, applying it to open windows) is in ``text_size``; this module only
holds it, so layout code can ask without depending on the menu.
"""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QTableView

TEXT_SIZES = (90, 100, 110, 125, 150, 175, 200)  # per cent of the system's own text size
DEFAULT_TEXT_SIZE = 100
_COMPACT_ROWS = "_filetree_compact_rows"  # widget property: rows as tall as one line of text
_ROW_PADDING = 6

_state = {"percent": DEFAULT_TEXT_SIZE}


def text_percent() -> int:
    """The text size in use, in per cent of the system's."""
    return _state["percent"]


def set_text_percent(percent: int) -> None:
    """Record the text size; anything that is not offered means the default."""
    _state["percent"] = percent if percent in TEXT_SIZES else DEFAULT_TEXT_SIZE


def text_scale() -> float:
    """The factor text is drawn at: 1.0 is the system's size."""
    return text_percent() / 100


def text_scaled(pixels: float) -> int:
    """``pixels`` chosen for text of the system's size (a column width, say) at the size in use."""
    return round(pixels * text_scale())


def scaled_font(font: QFont, factor: float) -> QFont:
    """A copy of ``font`` at ``factor`` times its size, whichever unit that size is given in."""
    scaled = QFont(font)
    if font.pointSizeF() > 0:
        scaled.setPointSizeF(font.pointSizeF() * factor)
    elif font.pixelSize() > 0:
        scaled.setPixelSize(max(1, round(font.pixelSize() * factor)))
    return scaled


def line_height(table: QTableView) -> int:
    """The height of a row of ``table`` holding one line of text."""
    return table.fontMetrics().height() + _ROW_PADDING


def compact_rows(table: QTableView) -> None:
    """Give ``table`` rows as tall as one line of text, also after the text size changes."""
    table.setProperty(_COMPACT_ROWS, True)
    table.verticalHeader().setDefaultSectionSize(line_height(table))


def fit_rows(table: QTableView) -> None:
    """Follow a changed text size: compact rows exactly, any other rows only when text no longer fits."""
    rows, needed = table.verticalHeader(), line_height(table)
    if table.property(_COMPACT_ROWS) or rows.defaultSectionSize() < needed:
        rows.setDefaultSectionSize(needed)
