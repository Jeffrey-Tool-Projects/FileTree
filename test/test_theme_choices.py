"""High contrast, a chosen accent and colour-blind chart colours: applied at once, remembered, validated."""

import itertools

import pytest
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QColorDialog

from test_gui import window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.core.analysis import CATEGORIES
from je_file_tree.core.scanner import scan
from je_file_tree.gui import themes
from je_file_tree.gui.app import create_window
from je_file_tree.gui.chart_palette import (
    CATEGORY_COLOURS, COLOUR_BLIND, PALETTES, STANDARD, palette_controller, saved_palette,
)
from je_file_tree.gui.colours import contrast
from je_file_tree.gui.fluent_style import CONTRAST_ACCENT, EDGE_CONTRAST, tokens_for
from je_file_tree.gui.scan_worker import analyse
from je_file_tree.gui.themes import theme_controller, valid_accent


@pytest.fixture(autouse=True)
def _defaults_afterwards(qapp):
    yield
    controller = theme_controller()
    controller.chosen_accent = ""
    controller.apply("system")
    palette_controller().apply(STANDARD)


def _deuteranopia(colour: str) -> tuple[float, float]:
    """A colour as someone without green cones sees it (Vienot, Brettel and Mollon 1999, linear sRGB)."""
    parts = QColor(colour).getRgbF()[:3]
    red, green, blue = (part / 12.92 if part <= 0.04045 else ((part + .055) / 1.055) ** 2.4 for part in parts)
    return .29275 * red + .70725 * green, -.02234 * red + .02234 * green + blue


def test_high_contrast_is_black_white_and_yellow(window, qapp):
    window.theme_menu.actions_by_theme["contrast"].trigger()
    controller = theme_controller()
    assert controller.resolved == "contrast" and window.settings.value("theme") == "contrast"
    assert controller.accent == QColor(CONTRAST_ACCENT)
    palette = QApplication.palette()
    assert palette.color(QPalette.ColorRole.Window) == QColor("#000000")
    assert palette.color(QPalette.ColorRole.Text) == QColor("#ffffff")
    tokens = tokens_for("contrast", CONTRAST_ACCENT)
    for edge in ("stroke", "stroke_strong", "scrollbar"):
        assert contrast(QColor(getattr(tokens, edge)), QColor(tokens.card)) >= 7, edge


def test_a_chosen_accent_replaces_the_platforms_in_every_theme(window, qapp, monkeypatch):
    controller = theme_controller()
    platform = QColor(controller.platform_accent)
    window.theme_menu.choose("dark")
    monkeypatch.setattr(QColorDialog, "getColor", lambda *_args: QColor("#00CC6A"))
    window.theme_menu.accent.trigger()
    assert controller.accent == QColor("#00cc6a") and window.settings.value("accent") == "#00cc6a"
    applied = QColor(tokens_for("dark", "#00cc6a").accent)
    assert QApplication.palette().color(QPalette.ColorRole.Accent) == applied
    assert window.theme_menu.platform_accent.isEnabled()
    window.theme_menu.choose("contrast")
    assert controller.accent == QColor("#00cc6a")
    monkeypatch.setattr(QColorDialog, "getColor", lambda *_args: QColor())  # cancelled
    window.theme_menu.accent.trigger()
    assert controller.accent == QColor("#00cc6a")
    window.theme_menu.choose("dark")
    window.theme_menu.platform_accent.trigger()
    assert controller.accent == platform and not window.settings.value("accent")
    assert not window.theme_menu.platform_accent.isEnabled()


@pytest.mark.parametrize("text, accent", [("#00CC6A", "#00cc6a"), ("", ""), ("red", ""), ("#12345", ""),
                                          ("#1234567", ""),
                                          (None, ""), (5, ""), ("#00cc6a; }", ""), ("#ggcc6a", "")])
def test_only_plain_colours_are_accents(text, accent):
    assert valid_accent(text) == accent


def test_saved_choices_are_used_at_the_start_and_broken_ones_ignored(window):
    window.settings.setValue("accent", "#f38064")
    window.settings.setValue("chart_palette", COLOUR_BLIND)
    window.settings.setValue("theme", "contrast")
    other = create_window(window.settings)
    assert theme_controller().chosen_accent == "#f38064" and theme_controller().resolved == "contrast"
    assert PALETTES[COLOUR_BLIND] == CATEGORY_COLOURS and other.theme_menu.colour_blind.isChecked()
    assert window.theme_menu.colour_blind.isChecked()  # every tab shows the one choice
    other.close()
    other.deleteLater()
    window.settings.setValue("accent", "}; evil")
    window.settings.setValue("chart_palette", "neon")
    assert saved_palette(window.settings) == STANDARD
    other = create_window(window.settings)
    assert theme_controller().chosen_accent == "" and PALETTES[STANDARD] == CATEGORY_COLOURS
    other.close()
    other.deleteLater()


def test_chart_colours_change_everywhere_at_once(window, sample_tree):
    results = window.results
    results.show_outcome(analyse(scan(sample_tree)))
    results.charts.treemap.grab()
    standard = [label.text() for label in results._legend.labels()]
    window.theme_menu.colour_blind.trigger()
    assert window.settings.value("chart_palette") == COLOUR_BLIND and PALETTES[COLOUR_BLIND] == CATEGORY_COLOURS
    assert results.charts.treemap._pixmap is None
    assert [label.text() for label in results._legend.labels()] != standard
    window.theme_menu.colour_blind.trigger()
    assert PALETTES[STANDARD] == CATEGORY_COLOURS
    assert [label.text() for label in results._legend.labels()] == standard


@pytest.mark.parametrize("palette", PALETTES)
@pytest.mark.parametrize("scheme", themes.SCHEMES)
def test_both_palettes_cover_every_type_and_stand_out(palette, scheme):
    assert set(PALETTES[palette]) == set(CATEGORIES)
    card = QColor(tokens_for(scheme).card)
    assert all(contrast(QColor(colour), card) >= EDGE_CONTRAST for colour in PALETTES[palette].values())


def test_the_colour_blind_palette_keeps_its_colours_further_apart_without_green_cones():
    def closest(palette):
        seen = [_deuteranopia(colour) for colour in PALETTES[palette].values()]
        return min(sum((a - b) ** 2 for a, b in zip(first, second, strict=True)) ** .5
                   for first, second in itertools.combinations(seen, 2))
    assert closest(COLOUR_BLIND) > closest(STANDARD)
