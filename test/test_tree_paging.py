"""Large folders are shown a page at a time, so the tree never lays out every row (U-20261119-02)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QItemSelectionModel, QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtTest import QAbstractItemModelTester, QTest

from test_gui import window as window, _child, _scanned  # noqa: PLC0414 - explicit pytest fixture re-export
from test_tree_filter import _filter, _wait
from test_tree_row_identity import model as model  # noqa: PLC0414 - shared owned-model cleanup
from je_file_tree.core.node import Node
from je_file_tree.gui import tree_model
from je_file_tree.gui.list_transfer import ListCapture
from je_file_tree.gui.tree_filter import ExpandedTreeProxy
from je_file_tree.gui.tree_model import NAME, NODE_ROLE, SIZE, MoreRows

PAGE = 3


@pytest.fixture(autouse=True)
def small_pages(monkeypatch):
    monkeypatch.setattr(tree_model, "PAGE_ROWS", PAGE)


def _root(count: int) -> Node:
    root = Node("root", True, children=[])
    root.children.extend(Node(f"file-{row}", False, size=100 - row, parent=root) for row in range(count))
    root.size = sum(child.size for child in root.children)
    return root


def _rows(model, parent: QModelIndex) -> list:
    return [model.index(row, NAME, parent).internalPointer() for row in range(model.rowCount(parent))]


def test_a_large_folder_shows_one_page_and_a_row_for_the_rest(model):
    root = _root(8)
    model.set_root(root)
    QAbstractItemModelTester(model, QAbstractItemModelTester.FailureReportingMode.Fatal)
    parent = model.index_for(root)
    rows = _rows(model, parent)
    assert rows[:PAGE] == root.children[:PAGE]
    more = rows[PAGE]
    assert isinstance(more, MoreRows) and more.hidden == 5
    assert more.size == sum(child.size for child in root.children[PAGE:])
    last = model.index(PAGE, NAME, parent)
    assert "5" in last.data() and str(PAGE) in last.data()
    assert model.index(PAGE, SIZE, parent).data()
    assert last.data(NODE_ROLE) is None and model.node(last) is None, "the row is never a file to act on"
    assert not model.hasChildren(last) and model.rowCount(last) == 0
    assert not model.index_for(root.children[PAGE]).isValid(), "entries past the page have no row yet"
    assert model.hidden_rows(root) == root.children[PAGE:]
    assert model.row_nodes(0, PAGE, parent) == root.children[:PAGE]


def test_small_folders_are_not_paged(model):
    root = _root(PAGE)
    model.set_root(root)
    assert _rows(model, model.index_for(root)) == root.children
    assert model.hidden_rows(root) == []
    assert model.show_more(root) is None


def test_show_more_adds_a_page_and_keeps_the_selection_and_the_last_row(model):
    root = _root(8)
    model.set_root(root)
    QAbstractItemModelTester(model, QAbstractItemModelTester.FailureReportingMode.Fatal)
    parent = model.index_for(root)
    pinned = QPersistentModelIndex(model.index(1, NAME, parent))
    more = QPersistentModelIndex(model.index(PAGE, NAME, parent))
    assert model.show_more(root) is root.children[PAGE]
    assert _rows(model, parent)[:2 * PAGE] == root.children[:2 * PAGE]
    assert pinned.row() == 1 and pinned.internalPointer() is root.children[1]
    assert more.row() == 2 * PAGE and isinstance(more.internalPointer(), MoreRows), "the last row follows the page"
    assert model.show_more(root) is root.children[2 * PAGE]
    assert _rows(model, parent) == root.children, "the last page leaves no extra row"
    assert not more.isValid()


def test_show_rows_for_extends_every_paged_folder_above_the_node(model):
    root = _root(8)
    folder = Node("folder", True, size=1, children=[], parent=root)
    root.children.append(folder)  # last in size order: past the root's first page
    folder.children.extend(Node(f"inner-{row}", False, size=50 - row, parent=folder) for row in range(7))
    model.set_root(root)
    target = folder.children[5]
    assert not model.index_for(target).isValid()
    model.show_rows_for(target)
    index = model.index_for(target)
    assert index.isValid() and index.internalPointer() is target
    assert model.index_for(folder).isValid()
    assert model.rowCount(model.index_for(folder)) == 2 * PAGE + 1, "pages up to the target, then the last row"


def test_sorting_keeps_the_pages_shown_in_the_new_order(model):
    root = _root(8)
    model.set_root(root)
    parent = model.index_for(root)
    model.show_more(root)
    model.sort(NAME, Qt.SortOrder.AscendingOrder)
    ordered = sorted(root.children, key=lambda node: node.name.lower())
    assert _rows(model, parent)[:2 * PAGE] == ordered[:2 * PAGE]
    assert isinstance(_rows(model, parent)[-1], MoreRows)


def test_a_live_scan_pages_its_frozen_rows_and_counts_new_arrivals(model):
    root = _root(5)
    model.set_root(root, live=True)
    parent = model.index_for(root)
    assert model.rowCount(parent) == PAGE + 1
    root.children.append(Node("late", False, size=1000, parent=root))
    model.refresh()
    rows = _rows(model, parent)
    assert rows[0].name == "late" and len(rows) == PAGE + 1
    assert rows[-1].hidden == 3
    model.finish_live()
    assert model.rowCount(parent) == PAGE + 1


def test_the_filter_keeps_the_last_row_only_while_a_hidden_entry_matches(model):
    root = _root(8)
    model.set_root(root)
    proxy = ExpandedTreeProxy(model, model)
    QAbstractItemModelTester(proxy, QAbstractItemModelTester.FailureReportingMode.Fatal)
    proxy.allowed = frozenset({id(root.children[0]), id(root.children[6])})
    proxy.invalidate()
    parent = proxy.index(0, NAME)
    rows = [proxy.index(row, NAME, parent).internalPointer() for row in range(proxy.rowCount(parent))]
    assert rows[0] is root.children[0] and isinstance(rows[1], MoreRows)
    more = proxy.index(1, NAME, parent)
    assert proxy.mapFromSource(proxy.mapToSource(more)) == more
    assert proxy.row_nodes(0, 1, parent) == [root.children[0]], "the last row is never a selected entry"
    proxy.allowed = frozenset({id(root.children[0])})
    proxy.invalidate()
    assert proxy.rowCount(parent) == 1


def _big_folder(tmp_path, count: int):
    folder = tmp_path / "tree"
    many = folder / "many"
    many.mkdir(parents=True)
    for number in range(count):
        (many / f"file-{number}.bin").write_bytes(b"x" * (number + 1))
    return folder


def _more_row(results, folder: Node) -> QModelIndex:
    parent = results.tree_filter.index_for(folder)
    results.tree.expand(parent)
    index = results.tree.model().index(results.tree.model().rowCount(parent) - 1, NAME, parent)
    assert isinstance(index.internalPointer(), MoreRows)
    return index


def test_clicking_the_last_row_shows_the_next_page_and_moves_to_it(window, qapp, tmp_path):
    _scanned(window, qapp, _big_folder(tmp_path, 7))
    results = window.results
    many = _child(results.tree_model.root, "many")
    results.tree.resize(600, 400)
    more = _more_row(results, many)
    QTest.mouseClick(results.tree.viewport(), Qt.MouseButton.LeftButton,
                     pos=results.tree.visualRect(more).center())
    current = results.tree.currentIndex()
    assert current.data(NODE_ROLE) is many.children[PAGE]
    assert results.selected_nodes() == [many.children[PAGE]]
    results.tree.setCurrentIndex(_more_row(results, many))
    results.tree.activated.disconnect(results._show_more_rows)  # as on macOS, where Return never activates
    QTest.keyClick(results.tree, Qt.Key.Key_Return)
    assert results.tree.currentIndex().data(NODE_ROLE) is many.children[2 * PAGE]
    assert results.tree_model.rowCount(results.tree_model.index_for(many)) == len(many.children)


def test_selecting_a_hidden_entry_from_another_view_shows_its_page(window, qapp, tmp_path):
    _scanned(window, qapp, _big_folder(tmp_path, 7))
    results = window.results
    many = _child(results.tree_model.root, "many")
    target = many.children[-1]
    results.select_node(target)
    assert results.tree.currentIndex().data(NODE_ROLE) is target


def test_selecting_everything_never_selects_the_last_row(window, qapp, tmp_path):
    _scanned(window, qapp, _big_folder(tmp_path, 7))
    results = window.results
    many = _child(results.tree_model.root, "many")
    _more_row(results, many)
    results.tree.selectAll()
    picked = results.selected_nodes()
    assert many.children[0] in picked and not any(isinstance(node, MoreRows) for node in picked)
    assert results.tree.selectionModel().isSelected(_more_row(results, many))


def test_a_filter_match_past_the_page_is_one_click_away(window, qapp, tmp_path):
    _scanned(window, qapp, _big_folder(tmp_path, 7))
    results = window.results
    many = _child(results.tree_model.root, "many")
    results.tree.expand(results.tree_filter.index_for(many))
    hidden = many.children[PAGE]  # the first entry past the page
    _filter(results, qapp, hidden.name)
    more = _more_row(results, many)
    results.tree.resize(600, 400)
    QTest.mouseClick(results.tree.viewport(), Qt.MouseButton.LeftButton,
                     pos=results.tree.visualRect(more).center())
    qapp.processEvents()
    assert results.tree_filter.index_for(hidden).isValid()
    selection = results.tree.selectionModel()
    selection.select(results.tree_filter.index_for(hidden),
                     QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows)
    assert results.selected_nodes() == [hidden]


def test_copying_a_selection_leaves_out_the_last_row(window, qapp, tmp_path):
    _scanned(window, qapp, _big_folder(tmp_path, 7))
    results = window.results
    many = _child(results.tree_model.root, "many")
    _more_row(results, many)
    results.tree.selectAll()
    capture, ready = ListCapture(results.tree, results.tree, selected=True), []
    capture.ready.connect(lambda _header, rows: ready.append(rows))
    capture.start()
    _wait(qapp, lambda: bool(ready))
    names = [row[NAME] for row in ready[0]]
    assert [child.name for child in many.children[:PAGE]] == names[-PAGE:]
    assert not any("more" in name for name in names)
    capture.deleteLater()
