"""Charts coloured by change use the captured comparison, folder by folder, and go grey without one."""

import pytest
from PySide6.QtGui import QColor

from test_gui import _wait, window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.core.compare import FolderChange, load_saved
from je_file_tree.core.export import export_json
from je_file_tree.core.node import Node
from je_file_tree.core.scanner import scan
from je_file_tree.gui import i18n
from je_file_tree.gui.change_colours import (
    CHANGE_COLOURS,
    GREW,
    GREW_LOT,
    NEW,
    SAME,
    SHRANK,
    SHRANK_LOT,
    ChangeColours,
    kind_of,
)
from je_file_tree.gui.colours import contrast
from je_file_tree.gui.fluent_style import tokens_for
from je_file_tree.gui.scan_worker import analyse
from je_file_tree.gui.treemap_widget import BY_CHANGE


@pytest.mark.parametrize("before, after, kind", [
    (None, 5, NEW), (100, 100, SAME), (100, 125, GREW), (100, 126, GREW_LOT), (0, 1, GREW_LOT),
    (100, 75, SHRANK), (100, 74, SHRANK_LOT), (100, 0, SHRANK_LOT), (10**12, 10**12 + 1, GREW),
])
def test_kinds_by_share_of_the_size_before(before, after, kind):
    node = Node("folder", True, size=after)
    assert kind_of(FolderChange("folder", node, before, after)) == kind


def test_files_take_their_folders_colour_and_unlisted_folders_did_not_change():
    root = Node("root", True, children=[])
    folder = Node("grown", True, children=[], parent=root)
    file = Node("a.bin", False, size=9, parent=folder)
    link = Node("link", True, is_link=True, parent=folder)
    folder.children, root.children = [file, link], [folder]
    colours = ChangeColours([FolderChange("grown", folder, 1, 9), FolderChange("gone", None, 5, None)])
    assert colours.kind(folder) == colours.kind(file) == colours.kind(link) == GREW_LOT
    assert colours.kind(root) == SAME and ChangeColours().kind(file) == SAME
    assert colours.colour(file) == QColor(CHANGE_COLOURS[GREW_LOT])


@pytest.mark.parametrize("scheme", ["light", "dark"])
@pytest.mark.parametrize("colour", CHANGE_COLOURS.values())
def test_colours_stand_out_from_the_surface(scheme, colour):
    assert contrast(QColor(colour), QColor(tokens_for(scheme).card)) >= 3


def test_a_comparison_colours_the_charts_and_stopping_it_greys_them(window, qapp, tmp_path):
    source = tmp_path / "source"
    (source / "grown").mkdir(parents=True)
    (source / "same").mkdir()
    (source / "grown" / "a.bin").write_bytes(b"x" * 100)
    (source / "same" / "b.bin").write_bytes(b"x" * 100)
    saved = tmp_path / "saved.json"
    export_json(scan(source).root, str(saved))
    (source / "grown" / "a.bin").write_bytes(b"x" * 1000)
    results = window.results
    results.show_outcome(analyse(scan(source)))
    results.charts.set_colour_mode(BY_CHANGE)
    results._update_chart_controls()
    assert [label.accessibleName() for label in results._legend.labels()] == [i18n.tr("change_colour_none")]
    results.changes.compare_saved(load_saved(saved))
    _wait(qapp, lambda: results.changes.changes and not results.changes.busy)
    folders = {node.name: node for node in results.tree_model.root.children}
    for chart in (results.charts.treemap, results.charts.sunburst):
        assert chart.colour_mode == BY_CHANGE
        assert chart.change_colours.kind(folders["grown"]) == GREW_LOT
        assert chart.change_colours.kind(folders["grown"].children[0]) == GREW_LOT
        assert chart.change_colours.kind(folders["same"]) == SAME
    results.charts.treemap.grab()
    file = folders["grown"].children[0]
    assert results.charts.treemap._colour(file, 2) == QColor(CHANGE_COLOURS[GREW_LOT])
    assert results.charts.treemap._colour(folders["grown"], 1).lightness() < QColor(CHANGE_COLOURS[GREW_LOT]).lightness()
    assert len(results._legend.labels()) == len(CHANGE_COLOURS)
    results.changes.stop_comparing()
    assert results.charts.treemap.change_colours.kind(folders["grown"]) == SAME
    assert len(results._legend.labels()) == 1


def test_a_new_scan_forgets_the_comparison(window, sample_tree):
    results = window.results
    results.show_outcome(analyse(scan(sample_tree)))
    results.charts.set_changes([FolderChange("", results.tree_model.root, 1, 100)])
    assert results.charts.treemap.change_colours.kind(results.tree_model.root) == GREW_LOT
    root = results.tree_model.root
    results.begin_scan()
    assert results.charts.treemap.change_colours.kind(root) == SAME
