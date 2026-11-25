"""Check marks, dots and arrows for the style sheet, drawn at start-up and served from memory.

A style sheet can only show an indicator's glyph from a file or a Qt resource. Fusion draws its own, but
outlines check boxes and radio buttons darker than the window, which does not show on a dark one, and
shrinks the arrows of styled spin boxes to two pixels. Overriding ``QProxyStyle.drawPrimitive`` instead
made a tree repaint 12 and 43 ms slower in two runs (about 900 calls a frame, native Windows, 2026-11-25),
so the glyphs are registered as an in-memory resource: no image files in the package and nothing written
to disk.
"""

from __future__ import annotations

import struct
from collections.abc import Callable

from PySide6.QtCore import QBuffer, QIODevice, QPointF, QRectF, Qt, qRegisterResourceData
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPolygonF

INKS = {"black": "#000000", "white": "#ffffff", "grey": "#8c8c8c"}  # grey: unavailable, 3:1 on every surface
_FOLDER = "filetree"
_SIZE = 16
_DENSITIES = (1, 2, 3)
_RESOURCE_VERSION = 1
_DIRECTORY_FLAG = 2
_registered: list[tuple[bytes, bytes, bytes]] = []  # Qt reads these bytes for as long as the process runs


def _line(painter: QPainter, colour: QColor, points: list[tuple[float, float]]) -> None:
    painter.setPen(QPen(colour, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawPolyline(QPolygonF([QPointF(x, y) for x, y in points]))


def _dot(painter: QPainter, colour: QColor) -> None:
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(colour)
    painter.drawEllipse(QRectF(4.5, 4.5, 7, 7))


_GLYPHS: dict[str, Callable[[QPainter, QColor], None]] = {
    "check": lambda painter, colour: _line(painter, colour, [(3.5, 8.5), (6.7, 11.5), (12.5, 5)]),
    "dash": lambda painter, colour: _line(painter, colour, [(4, 8), (12, 8)]),
    "dot": _dot,
    "up": lambda painter, colour: _line(painter, colour, [(3.5, 10.5), (8, 6), (12.5, 10.5)]),
    "down": lambda painter, colour: _line(painter, colour, [(3.5, 6), (8, 10.5), (12.5, 6)]),
}


def _png(name: str, ink: str, density: int) -> bytes:
    image = QImage(_SIZE * density, _SIZE * density, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(density, density)
    _GLYPHS[name](painter, QColor(INKS[ink]))
    painter.end()
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data().data())


def _hash(name: str) -> int:
    """The hash Qt sorts and looks up resource names by."""
    value = 0
    for character in name:
        value = (value << 4) + ord(character)
        value ^= (value & 0xF0000000) >> 23
        value &= 0x0FFFFFFF
    return value


def pack(files: dict[str, bytes], folder: str = _FOLDER) -> tuple[bytes, bytes, bytes]:
    """The tree, names and data of a one-folder Qt resource holding ``files`` (what ``rcc`` writes)."""
    names, offsets = bytearray(), {}
    for name in (folder, *files):
        offsets[name] = len(names)
        names += struct.pack(">HI", len(name), _hash(name)) + name.encode("utf-16-be")
    root, children, first_file = 0, 1, 2
    tree = bytearray(struct.pack(">IHII", root, _DIRECTORY_FLAG, 1, children))
    tree += struct.pack(">IHII", offsets[folder], _DIRECTORY_FLAG, len(files), first_file)
    data = bytearray()
    for name in sorted(files, key=_hash):
        tree += struct.pack(">IHHHI", offsets[name], 0, 0, 1, len(data))  # no territory, the C language
        data += struct.pack(">I", len(files[name])) + files[name]
    return bytes(tree), bytes(names), bytes(data)


def register_glyphs() -> None:
    """Make every glyph available to style sheets, once per process; needs no window."""
    if _registered:
        return
    files = {f"{name}-{ink}{'' if density == 1 else f'@{density}x'}.png": _png(name, ink, density)
             for name in _GLYPHS for ink in INKS for density in _DENSITIES}
    _registered.append(pack(files))
    qRegisterResourceData(_RESOURCE_VERSION, *_registered[0])


def glyph_url(name: str, ink: str) -> str:
    """The style-sheet address of a registered glyph."""
    return f"url(:/{_FOLDER}/{name}-{ink}.png)"
