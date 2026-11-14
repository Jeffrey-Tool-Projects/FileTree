"""How removal advice (``core.advice``) is worded and coloured in lists, highlights and details."""

from __future__ import annotations

import sys

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap

from je_file_tree.core.advice import LOW, MANAGED, PENDING, PERSONAL, PROTECTED, REVIEW, Advice
from je_file_tree.gui.cleanup_text import explanation
from je_file_tree.gui.i18n import tr

# Mid-tone inks that stay readable on the light and the dark surface; the label always says the same.
ADVICE_COLOURS = {LOW: "#2e9e5b", REVIEW: "#d99a00", PERSONAL: "#8a8f98", PROTECTED: "#d64545",
                  MANAGED: "#8e5bd6", PENDING: "#b4b8bf"}
_DOT, _CANVAS, _SCALE = 10, 16, 2
_icons: dict[str, QIcon] = {}


def label(advice: Advice) -> str:
    """The short answer shown in a cell."""
    return tr(f"advice_{advice.kind}")


def reason(advice: Advice) -> str:
    """Why: the rule's evidence or the protected place, as a full sentence."""
    if advice.group is not None:
        return tr(f"advice_{advice.kind}_tip") + "\n" + explanation(advice.group.key, advice.group.details)
    if advice.protection is not None:
        return tr("advice_protected_tip", reason=tr(f"protected_{advice.protection.reason}"))
    return tr(f"advice_{advice.kind}_tip")


def summary(advice: Advice) -> str:
    """The answer and its reason on one line (tooltips, details)."""
    return tr("advice_summary", label=label(advice), reason=reason(advice))


def legend() -> list[tuple[str, str]]:
    """Colour and label of every answer a finished scan can give on this platform."""
    kinds = [LOW, REVIEW, PERSONAL, PROTECTED] + ([MANAGED] if sys.platform == "win32" else [])
    return [(ADVICE_COLOURS[kind], tr(f"advice_{kind}")) for kind in kinds]


def dot(kind: str) -> QIcon:
    """A round marker in the colour of ``kind`` (drawn once, at twice the size for sharp scaling)."""
    icon = _icons.get(kind)
    if icon is None:
        pixmap = QPixmap(_CANVAS * _SCALE, _CANVAS * _SCALE)
        pixmap.setDevicePixelRatio(_SCALE)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(ADVICE_COLOURS[kind]))
        offset = (_CANVAS - _DOT) / 2
        painter.drawEllipse(QRectF(offset, offset, _DOT, _DOT))
        painter.end()
        icon = _icons[kind] = QIcon(pixmap)
    return icon
