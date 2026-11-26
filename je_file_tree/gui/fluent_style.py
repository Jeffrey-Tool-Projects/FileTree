"""Fluent (Windows 11) design tokens and the one application style sheet built from them.

Every colour the style sheet uses comes from :class:`Tokens`, so light and dark share one set of
rules. Rules never style view items (``::item``) of the large result views: those keep painting
through the palette, which the style sheet does not slow down. Widgets opt into roles with
dynamic properties (``role="caption"``, ``role="primary"``) or object names (``scan_metric``,
``result_navigation``, ``main_toolbar``), so no widget carries its own style sheet.

Cost, measured natively on Windows (2026-10-18): repainting a 900-pixel tree of 100,000 rows took a
median 54–57 ms with the sheet against 46–47 ms with the native style. The difference is the same
when the sheet has no view rules at all, so it is Qt's style-sheet wrapper itself, not these rules.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QProxyStyle, QStyle, QStyleFactory, QStyleOption, QWidget

from je_file_tree.gui.colours import blend, contrast, luminance, readable_ink
from je_file_tree.gui.glyphs import glyph_url, register_glyphs

DEFAULT_ACCENT = "#0067c0"  # Windows' default blue, used when the platform reports no accent
RADIUS = 6
CARD_RADIUS = 8


@dataclass(frozen=True, slots=True)
class Tokens:
    """One colour scheme's surfaces, strokes, text and accent, as ``#rrggbb`` strings."""

    scheme: str
    window: str
    card: str
    subtle: str
    control: str
    control_hover: str
    control_pressed: str
    stroke: str
    stroke_strong: str
    text: str
    text_secondary: str
    text_disabled: str
    scrollbar: str
    accent: str
    accent_hover: str
    on_accent: str
    link: str
    selection: str
    success: str
    caution: str


# Contrast the tests hold for every theme and accent (WCAG 2.2): text 7:1 on every surface, unavailable text
# 4.5:1, control edges and scroll bars 3:1, dividers and card edges 1.8:1 (they only group, so they stay quiet).
TEXT_CONTRAST, DISABLED_CONTRAST, EDGE_CONTRAST, DIVIDER_CONTRAST = 7.0, 4.5, 3.0, 1.8
_ACCENT_CONTRAST = 4.5
_MID_LUMINANCE = .18  # black and white contrast equally with it
# Text on the selection; the light scheme leaves room for the share bar, which is drawn at 7:1, to show on it.
_SELECTION_TEXT = {"light": 8.5, "dark": TEXT_CONTRAST, "contrast": TEXT_CONTRAST}
_SELECTION_STRONGEST = {"light": .45, "dark": .45, "contrast": .6}
_SELECTION_FAINTEST, _SELECTION_STEP = .1, .025

_SURFACES = {
    "light": {"window": "#ededed", "card": "#ffffff", "subtle": "#f2f2f2", "control": "#fafafa",
              "control_hover": "#e6e6e6", "control_pressed": "#d6d6d6", "stroke": "#b0b0b0",
              "stroke_strong": "#767676", "text": "#111111", "text_secondary": "#414141",
              "text_disabled": "#666666", "scrollbar": "#767676", "success": "#085608", "caution": "#6b3f00"},
    "dark": {"window": "#141414", "card": "#1f1f1f", "subtle": "#2a2a2a", "control": "#2b2b2b",
             "control_hover": "#3d3d3d", "control_pressed": "#484848", "stroke": "#545454",
             "stroke_strong": "#8a8a8a", "text": "#ffffff", "text_secondary": "#e0e0e0",
             "text_disabled": "#9a9a9a", "scrollbar": "#a0a0a0", "success": "#7fdc72", "caution": "#fce100"},
    "contrast": {"window": "#000000", "card": "#000000", "subtle": "#141414", "control": "#000000",
                 "control_hover": "#2b2b2b", "control_pressed": "#3d3d3d", "stroke": "#a6a6a6",
                 "stroke_strong": "#ffffff", "text": "#ffffff", "text_secondary": "#ffffff",
                 "text_disabled": "#b3b3b3", "scrollbar": "#ffffff", "success": "#8dff7f", "caution": "#ffe100"},
}
CONTRAST_ACCENT = "#ffd400"  # high contrast uses yellow unless an accent was chosen


def _shift_until(colour: QColor, against: tuple[QColor, ...], ratio: float, lighter: bool) -> QColor:
    """Lighten or darken ``colour`` in small steps until it reaches ``ratio`` against every background."""
    shifted = QColor(colour)
    for _step in range(40):
        if min(contrast(shifted, background) for background in against) >= ratio:
            break
        hue, saturation, value, _alpha = shifted.getHsvF()
        value = min(1.0, value + .04) if lighter else max(0.0, value - .04)
        if lighter and value >= 1.0:
            saturation = max(0.0, saturation - .06)  # past full brightness, approach white instead
        shifted = QColor.fromHsvF(max(hue, 0.0), saturation, value)
    return shifted


def _selection(scheme: str, accent: QColor, card: QColor, text: QColor) -> QColor:
    """The strongest tint of ``accent`` over ``card``, up to a share, that keeps ``text`` readable on it."""
    amount = _SELECTION_STRONGEST[scheme]
    while amount > _SELECTION_FAINTEST and contrast(blend(accent, card, amount), text) < _SELECTION_TEXT[scheme]:
        amount -= _SELECTION_STEP
    return blend(accent, card, amount)


def tokens_for(scheme: str, accent: QColor | str | None = None) -> Tokens:
    """Tokens for ``light``, ``dark`` or ``contrast``, fitting ``accent`` so controls and links stay distinguishable.

    The accent is shifted until it has 4.5:1 against cards and the link colour until 7:1 against every
    surface text sits on; text on the accent is black or white, whichever reads better (always at least
    4.5:1). The selection is as strong a tint of the accent as its text allows at 7:1.
    """
    scheme = scheme if scheme in _SURFACES else "light"
    surfaces = _SURFACES[scheme]
    card = QColor(surfaces["card"])
    base = QColor(accent) if accent is not None and QColor(accent).isValid() else QColor(DEFAULT_ACCENT)
    lighter = scheme != "light"
    fitted = _shift_until(base, (card,), _ACCENT_CONTRAST, lighter)
    surfaces_behind_text = tuple(QColor(surfaces[name]) for name in ("window", "card", "subtle"))
    link = _shift_until(fitted, surfaces_behind_text, TEXT_CONTRAST, lighter)
    hover = fitted.lighter(112) if lighter else fitted.darker(112)
    return Tokens(scheme=scheme, accent=fitted.name(), accent_hover=hover.name(),
                  on_accent=readable_ink(fitted).name(), link=link.name(),
                  selection=_selection(scheme, fitted, card, QColor(surfaces["text"])).name(), **surfaces)


def style_sheet(tokens: Tokens) -> str:
    """The application style sheet for ``tokens``."""
    register_glyphs()
    t = tokens
    return "\n".join((
        _controls(t), _inputs(t), _indicators(t), _containers(t), _menus(t), _scrollbars(t), _roles(t),
    ))


def _controls(t: Tokens) -> str:
    return f"""
QPushButton {{
    background: {t.control}; color: {t.text}; border: 1px solid {t.stroke_strong};
    border-radius: {RADIUS}px; padding: 5px 14px; min-height: 20px;
}}
QPushButton:hover {{ background: {t.control_hover}; }}
QPushButton:pressed {{ background: {t.control_pressed}; }}
QPushButton:disabled {{ color: {t.text_disabled}; background: {t.subtle}; border-color: {t.stroke}; }}
QPushButton:focus {{ border: 2px solid {t.text}; padding: 4px 13px; }}
QPushButton:flat {{ background: transparent; border: 1px solid transparent; }}
QPushButton:flat:hover {{ background: {t.control_hover}; }}
QPushButton[role="primary"] {{
    background: {t.accent}; color: {t.on_accent}; border: 1px solid {t.accent};
}}
QPushButton[role="primary"]:hover {{ background: {t.accent_hover}; }}
QPushButton[role="primary"]:disabled {{
    background: {t.subtle}; color: {t.text_disabled}; border-color: {t.stroke};
}}
QPushButton[role="primary"]:focus {{ border: 2px solid {t.text}; }}
QToolButton {{ background: transparent; border: 1px solid transparent; border-radius: {RADIUS}px;
    padding: 3px 3px; color: {t.text}; }}
QToolButton:hover {{ background: {t.control_hover}; }}
QToolButton:pressed {{ background: {t.control_pressed}; }}
QToolButton:checked {{ background: {t.selection}; border-color: {t.accent}; }}
QToolButton:disabled {{ color: {t.text_disabled}; }}
QToolButton:focus {{ border: 2px solid {t.text}; }}
QProgressBar {{ background: {t.stroke}; border: 0; border-radius: 3px; text-align: center; color: {t.text}; }}
QProgressBar::chunk {{ background: palette(highlight); border-radius: 3px; }}
"""


def _inputs(t: Tokens) -> str:
    fields = "QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QDateTimeEdit, QTimeEdit, QPlainTextEdit"
    focused = ", ".join(f"{name.strip()}:focus" for name in fields.split(","))
    return f"""
{fields} {{
    background: {t.control}; color: {t.text}; border: 1px solid {t.stroke_strong};
    border-radius: {RADIUS}px; padding: 4px 8px;
    selection-background-color: {t.accent}; selection-color: {t.on_accent};
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QDateTimeEdit, QTimeEdit {{ min-height: 20px; }}
{focused} {{ border-bottom: 2px solid {t.accent}; background: {t.card}; }}
QLineEdit:disabled, QComboBox:disabled {{ color: {t.text_disabled}; background: {t.subtle}; }}
QComboBox QAbstractItemView {{
    background: {t.card}; border: 1px solid {t.stroke_strong}; selection-background-color: {t.selection};
    selection-color: {t.text}; outline: 0;
}}
"""


def _ink(colour: str) -> str:
    """The glyph ink closest to a token: black or white."""
    return "white" if luminance(QColor(colour)) > _MID_LUMINANCE else "black"


def _indicators(t: Tokens) -> str:
    """Check boxes, radio buttons and the arrows of spin and combo boxes, outlined like every other control."""
    boxes = ("QCheckBox", "QRadioButton", "QGroupBox", "QAbstractItemView")
    on, text = _ink(t.on_accent), _ink(t.text)

    def rule(state: str = "", owners: tuple[str, ...] = boxes) -> str:
        return ", ".join(f"{owner}::indicator{state}" for owner in owners)

    return f"""
{rule()} {{
    width: 14px; height: 14px; border: 1px solid {t.stroke_strong}; border-radius: 3px; background: {t.control};
}}
QRadioButton::indicator {{ border-radius: 8px; }}
{rule(":hover")} {{ border-color: {t.text}; }}
{rule(":focus")} {{ border-color: {t.text}; }}
{rule(":checked")}, {rule(":indeterminate")} {{ background: {t.accent}; border-color: {t.accent}; }}
{rule(":checked", ("QCheckBox", "QGroupBox", "QAbstractItemView"))} {{ image: {glyph_url("check", on)}; }}
{rule(":indeterminate")} {{ image: {glyph_url("dash", on)}; }}
QRadioButton::indicator:checked {{ image: {glyph_url("dot", on)}; }}
{rule(":disabled")} {{ background: {t.subtle}; border-color: {t.stroke}; }}
{rule(":checked:disabled", ("QCheckBox", "QGroupBox", "QAbstractItemView"))} {{ image: {glyph_url("check", "grey")}; }}
{rule(":indeterminate:disabled")} {{ image: {glyph_url("dash", "grey")}; }}
QRadioButton::indicator:checked:disabled {{ image: {glyph_url("dot", "grey")}; }}
QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{
    subcontrol-origin: border; width: 20px; border: 0; background: transparent;
}}
QAbstractSpinBox::up-button {{ subcontrol-position: top right; }}
QAbstractSpinBox::down-button {{ subcontrol-position: bottom right; }}
QAbstractSpinBox::up-button:hover, QAbstractSpinBox::down-button:hover {{ background: {t.control_hover}; }}
QAbstractSpinBox::up-arrow {{ image: {glyph_url("up", text)}; width: 11px; height: 11px; }}
QAbstractSpinBox::down-arrow, QComboBox::down-arrow {{
    image: {glyph_url("down", text)}; width: 11px; height: 11px;
}}
QAbstractSpinBox::up-arrow:disabled, QAbstractSpinBox::up-arrow:off {{ image: {glyph_url("up", "grey")}; }}
QAbstractSpinBox::down-arrow:disabled, QAbstractSpinBox::down-arrow:off, QComboBox::down-arrow:disabled {{
    image: {glyph_url("down", "grey")};
}}
QComboBox::drop-down, QDateEdit::drop-down, QDateTimeEdit::drop-down {{
    subcontrol-origin: border; subcontrol-position: center right; width: 24px; border: 0; background: transparent;
}}
"""


def _containers(t: Tokens) -> str:
    return f"""
QToolTip {{ background: {t.card}; color: {t.text}; border: 1px solid {t.stroke_strong}; padding: 4px 8px; }}
QTreeView, QTableView, QListView, QTextEdit, QTextBrowser {{
    background: {t.card}; border: 1px solid {t.stroke}; border-radius: {CARD_RADIUS}px;
    alternate-background-color: {t.subtle};
}}
QAbstractItemView {{ selection-background-color: {t.selection}; selection-color: {t.text}; }}
QHeaderView {{ background: {t.card}; border: 0; }}
QHeaderView::section {{
    background: {t.card}; color: {t.text_secondary}; border: 0; border-bottom: 1px solid {t.stroke};
    border-right: 1px solid {t.stroke}; padding: 5px 8px;
}}
QHeaderView::section:last {{ border-right: 0; }}
QHeaderView::section:hover {{ background: {t.control_hover}; }}
QTabWidget::pane {{ border: 1px solid {t.stroke}; border-radius: {CARD_RADIUS}px; background: {t.card}; top: -1px; }}
QTabBar::tab {{
    background: transparent; color: {t.text_secondary}; border: 0; border-bottom: 2px solid transparent;
    padding: 6px 14px 4px;
    margin-right: 2px; border-top-left-radius: {RADIUS}px; border-top-right-radius: {RADIUS}px;
}}
QTabBar::tab:selected {{ background: {t.card}; color: {t.text}; border-bottom-color: {t.accent}; }}
QTabBar::tab:hover:!selected {{ background: {t.control_hover}; color: {t.text}; }}
QTabBar::close-button:hover {{ background: {t.control_hover}; border-radius: 4px; }}
QGroupBox {{ border: 1px solid {t.stroke}; border-radius: {CARD_RADIUS}px; margin-top: 14px; padding: 10px 8px 8px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {t.text}; }}
QSplitter::handle {{ background: transparent; }}
QStatusBar {{ background: {t.window}; color: {t.text_secondary}; border-top: 1px solid {t.stroke}; }}
QStatusBar::item {{ border: 0; }}
QToolBar {{ background: {t.window}; border: 0; spacing: 4px; padding: 4px; }}
QToolBar#main_toolbar {{ border-bottom: 1px solid {t.stroke}; spacing: 6px; padding: 6px 10px; }}
QToolBar::separator {{ background: {t.stroke}; width: 1px; margin: 6px 6px; }}
"""


def _menus(t: Tokens) -> str:
    return f"""
QMenuBar {{ background: {t.window}; color: {t.text}; padding: 2px 6px; }}
QMenuBar::item {{ background: transparent; padding: 5px 10px; border-radius: 4px; }}
QMenuBar::item:selected, QMenuBar::item:pressed {{ background: {t.selection}; }}
QMenu {{ background: {t.card}; color: {t.text}; border: 1px solid {t.stroke_strong}; padding: 4px; }}
QMenu::item {{ padding: 6px 28px 6px 24px; border-radius: 4px; margin: 1px 2px; }}
QMenu::item:selected {{ background: {t.selection}; }}
QMenu::item:disabled {{ color: {t.text_disabled}; }}
QMenu::indicator {{ width: 16px; height: 16px; left: 5px; }}
QMenu::indicator:checked {{ image: {glyph_url("check", _ink(t.text))}; }}
QMenu::separator {{ height: 1px; background: {t.stroke}; margin: 4px 8px; }}
"""


def _scrollbars(t: Tokens) -> str:
    return f"""
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
QScrollBar::handle {{ background: {t.scrollbar}; border-radius: 4px; }}
QScrollBar::handle:vertical {{ min-height: 32px; margin: 0 2px; }}
QScrollBar::handle:horizontal {{ min-width: 32px; margin: 2px 0; }}
QScrollBar::handle:hover {{ background: {t.text_secondary}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; border: 0; background: none; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
"""


def _roles(t: Tokens) -> str:
    return f"""
QLabel[role="caption"] {{ color: {t.text_secondary}; }}
QLabel[role="chip"] {{
    background: {t.subtle}; color: {t.text_secondary}; border: 1px solid {t.stroke};
    border-radius: 8px; padding: 1px 10px;
}}
QLabel[role="chip"][tone="success"] {{ color: {t.success}; }}
QLabel[role="chip"][tone="caution"] {{ color: {t.caution}; }}
QLabel[role="chip"][tone="accent"] {{ color: {t.link}; }}
QLabel[role="title"] {{ color: {t.text}; }}
QPushButton[role="list"] {{ text-align: left; padding: 5px 10px; }}
QFrame#scan_metric, QFrame[role="card"] {{
    background: {t.card}; border: 1px solid {t.stroke}; border-radius: {CARD_RADIUS}px;
}}
QLabel#metric_caption {{ color: {t.text_secondary}; }}
QListWidget#result_navigation {{ background: transparent; border: 0; outline: 0; }}
QListWidget#result_navigation::item {{
    padding: 8px 10px; margin: 1px 0; border-radius: {RADIUS}px; color: {t.text};
    border-left: 3px solid transparent;
}}
QListWidget#result_navigation::item:hover {{ background: {t.control_hover}; }}
QListWidget#result_navigation::item:selected {{
    background: {t.selection}; color: {t.text}; border-left: 3px solid {t.accent};
}}
"""


def set_style_property(widget: QWidget, name: str, value: object) -> None:
    """Set a dynamic property the style sheet selects on and re-polish, which Qt does not do by itself."""
    if widget.property(name) == value:
        return
    widget.setProperty(name, value)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


class FluentStyle(QProxyStyle):
    """Fusion with Fluent close/clear glyphs drawn in the theme's secondary text colour.

    Fusion's own tab-close icon is a red square; these glyphs are painted at run time, so the
    package needs no image files.
    """

    def __init__(self, tokens: Tokens) -> None:
        super().__init__(QStyleFactory.create("Fusion"))
        self.tokens = tokens
        self._cross = _cross_icon(QColor(tokens.text_secondary), QColor(tokens.text))

    def standardIcon(self, icon: QStyle.StandardPixmap, option: QStyleOption | None = None,  # noqa: N802
                     widget: QWidget | None = None) -> QIcon:
        """Qt: the theme's cross for closing tabs and clearing fields; Fusion's icon otherwise."""
        if icon in (QStyle.StandardPixmap.SP_TabCloseButton, QStyle.StandardPixmap.SP_LineEditClearButton):
            return self._cross
        return super().standardIcon(icon, option, widget)


def _cross_icon(normal: QColor, active: QColor) -> QIcon:
    """A thin, round-capped cross at 16 and 32 pixels, darker or brighter while hovered."""
    icon = QIcon()
    for size in (16, 32):
        for mode, colour in ((QIcon.Mode.Normal, normal), (QIcon.Mode.Active, active)):
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(colour, size / 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            inset = size * .3
            painter.drawLine(QPointF(inset, inset), QPointF(size - inset, size - inset))
            painter.drawLine(QPointF(size - inset, inset), QPointF(inset, size - inset))
            painter.end()
            icon.addPixmap(pixmap, mode)
    return icon
