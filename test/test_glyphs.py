"""Indicator glyphs are served from memory, in inks that show, and drawn by the style sheet."""

import pytest
from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QCheckBox, QRadioButton, QSpinBox

from je_file_tree.gui.colours import contrast
from je_file_tree.gui.fluent_style import EDGE_CONTRAST, style_sheet, tokens_for
from je_file_tree.gui.glyphs import INKS, glyph_url, pack, register_glyphs
from je_file_tree.gui.themes import theme_controller


@pytest.mark.parametrize("name", ["check", "dash", "dot", "up", "down"])
@pytest.mark.parametrize("ink", INKS)
def test_every_glyph_is_registered_at_each_density_in_its_ink(qapp, name, ink):
    register_glyphs()
    register_glyphs()  # once per process
    for suffix, size in (("", 16), ("@2x", 32), ("@3x", 48)):
        image = QImage(f":/filetree/{name}-{ink}{suffix}.png")
        assert image.size().toTuple() == (size, size)
        solid = {image.pixelColor(x, y).name() for x in range(size) for y in range(size)
                 if image.pixelColor(x, y).alpha() == 255}
        assert solid and all(QColor(colour).lightness() == pytest.approx(QColor(INKS[ink]).lightness(), abs=3)
                             for colour in solid)


def test_the_resource_layout_orders_names_by_hash():
    tree, names, data = pack({"b.png": b"two", "a.png": b"one"}, "folder")
    assert len(tree) == 4 * 14 and "folder".encode("utf-16-be") in names
    assert data == b"\0\0\0\3one\0\0\0\3two"  # stored in the order Qt searches them


def test_every_glyph_a_style_sheet_names_exists(qapp):
    for scheme in ("light", "dark"):
        sheet = style_sheet(tokens_for(scheme))
        addresses = {part.split(")")[0] for part in sheet.split("url(")[1:]}
        assert addresses and all(QFile.exists(address) for address in addresses)
    assert glyph_url("check", "white") == "url(:/filetree/check-white.png)"


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_the_unavailable_ink_shows_on_the_surfaces_it_is_drawn_on(scheme):
    tokens = tokens_for(scheme)
    for surface in (tokens.subtle, tokens.card):
        assert contrast(QColor(INKS["grey"]), QColor(surface)) >= EDGE_CONTRAST


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("kind", [QCheckBox, QRadioButton])
def test_empty_boxes_are_outlined_and_checked_ones_filled_with_the_accent(qapp, theme, kind):
    controller = theme_controller()
    controller.apply(theme)
    try:
        tokens = tokens_for(theme, controller.accent)
        box = kind()
        box.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        box.resize(box.sizeHint())
        box.show()
        empty = box.grab().toImage()
        box.setChecked(True)
        checked = box.grab().toImage()

        def colours(image):
            return {image.pixelColor(x, y).name() for x in range(image.width()) for y in range(image.height())}
        # A circle is antialiased, so its ring need not hold the exact edge colour.
        assert max(contrast(QColor(colour), QColor(tokens.control)) for colour in colours(empty)) >= EDGE_CONTRAST
        assert tokens.accent not in colours(empty)
        assert tokens.accent in colours(checked)
        box.deleteLater()
    finally:
        controller.apply("system")


def test_spin_box_arrows_still_step_the_value(qapp):
    theme_controller().apply("dark")
    try:
        spin = QSpinBox()
        spin.setValue(5)
        spin.stepUp()
        assert spin.value() == 6 and spin.sizeHint().height() > spin.fontMetrics().height()
        spin.deleteLater()
    finally:
        theme_controller().apply("system")
