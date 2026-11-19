"""A hidden clean-up list opens its groups when it is shown, not when suggestions arrive (U-20261119-05)."""

from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QWidget

from je_file_tree.core.node import Node
from je_file_tree.gui import grouped_list
from je_file_tree.gui.cleanup_panel import CleanupPanel
from je_file_tree.gui.grouped_list import GroupedListModel
from je_file_tree.gui.tree_model import NODE_ROLE


def _tabs(view):
    """The view on a second tab, hidden behind the first like the Clean-up tab during charting."""
    tabs = QTabWidget()
    tabs.addTab(QWidget(), "charts")
    tabs.addTab(view, "clean-up")
    tabs.resize(500, 400)
    tabs.show()
    return tabs


def _groups(count: int):
    nodes = [Node(f"empty-{row}", True) for row in range(count)]
    return nodes, [("empty folders", nodes[:count - 2]), ("temporary", nodes[count - 2:])]


def test_a_marked_hidden_view_opens_its_groups_only_when_shown(qapp, monkeypatch):
    model = GroupedListModel()
    view = grouped_list.build_view(model)
    grouped_list.open_groups_when_shown(view)
    grouped_list.open_groups_when_shown(view)  # marking twice keeps one watcher
    tabs = _tabs(view)
    expanded = []
    original = type(view).expand
    monkeypatch.setattr(type(view), "expand", lambda self, index: (expanded.append(index.row()), original(self, index)))
    nodes, groups = _groups(10)
    grouped_list.fill(model, view, groups, "auto")
    assert expanded == [], "the hidden list lays out nothing yet: 56,321 lines took 0.6-0.7 s"
    assert not view.isExpanded(model.index(0, 0))
    grouped_list.fill(model, view, groups, "auto")  # refilled while still hidden: still waiting
    assert expanded == []
    tabs.setCurrentIndex(1)
    assert view.isVisible()
    assert view.isExpanded(model.index(0, 0)) and view.isExpanded(model.index(1, 0))
    assert expanded == [0, 1]
    grouped_list.select_group(model, view, 1)
    assert [index.data(NODE_ROLE) for index in view.selectionModel().selectedRows()] == nodes[8:]
    tabs.setCurrentIndex(0)
    tabs.setCurrentIndex(1)
    assert expanded == [0, 1], "shown again: nothing to open twice"
    assert len(view.findChildren(grouped_list._ExpandWhenShown)) == 1
    tabs.deleteLater()


def test_a_marked_visible_view_opens_its_groups_at_once(qapp):
    model = GroupedListModel()
    view = grouped_list.build_view(model)
    grouped_list.open_groups_when_shown(view)
    tabs = _tabs(view)
    tabs.setCurrentIndex(1)
    _nodes, groups = _groups(5)
    grouped_list.fill(model, view, groups, "auto")
    assert view.isExpanded(model.index(0, 0)) and view.isExpanded(model.index(1, 0))
    tabs.setCurrentIndex(0)
    grouped_list.fill(model, view, groups[:1], "auto")
    tabs.setCurrentIndex(1)
    assert view.isExpanded(model.index(0, 0)), "a later hidden fill still opens when shown"
    tabs.deleteLater()


def test_an_unmarked_hidden_view_still_opens_its_groups_at_once(qapp):
    model = GroupedListModel()
    view = grouped_list.build_view(model)
    tabs = _tabs(view)
    _nodes, groups = _groups(5)
    grouped_list.fill(model, view, groups, "auto")
    assert view.isExpanded(model.index(0, 0)) and view.isExpanded(model.index(1, 0))
    tabs.deleteLater()


def test_the_clean_up_list_is_marked(qapp):
    panel = CleanupPanel()
    assert panel.view.findChild(grouped_list._ExpandWhenShown) is not None
    panel.deleteLater()
