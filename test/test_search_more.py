"""Search by regular expression, exclusion, owner and depth: bounded, combined and removable one by one."""

import re
import time

import pytest

from test_gui import _wait, window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.core import search as search_module
from je_file_tree.core.name_regex import MAX_LENGTH, NameRegexError, name_regex
from je_file_tree.core.node import Node
from je_file_tree.core.scanner import scan
from je_file_tree.core.search import Query, accepts, search
from je_file_tree.gui import i18n
from je_file_tree.gui.scan_worker import analyse
from je_file_tree.gui.search_conditions import descriptions
from je_file_tree.gui.search_ranges import MAX_DEPTH, SearchRangeDialog, validate_more


@pytest.fixture
def tree() -> Node:
    root = Node("root", True, children=[])

    def add(parent, name, *, is_dir=False, owner=None):
        node = Node(name, is_dir, size=1, parent=parent, children=[] if is_dir else (), owner=owner)
        parent.children.append(node)
        return node
    photos = add(root, "Photos", is_dir=True)
    add(photos, "IMG_0001.JPG", owner=1000)
    add(photos, "IMG_0002.jpeg", owner=1001)
    deep = add(photos, "Old", is_dir=True)
    add(deep, "IMG_0003.jpg", owner=1000)
    cache = add(root, "node_modules", is_dir=True)
    add(cache, "IMG_0004.jpg", owner=1000)
    add(root, "notes.txt")
    return root


def _names(root, **query):
    return {node.name for node in search(root, Query(**query)).matches}


@pytest.mark.parametrize("pattern", [r"^IMG_\d+.*\.jpe?g$", r"\.(jpe?g|png|gif|tiff?|bmp|webp)$", r"(foo|bar).*\.txt",
                                     r"\d{4}-\d{2}-\d{2}", "(?i:abc)", "a++b", "[a-z]+[0-9]+", "(x(y(z)?)?)?",
                                     "a{1,5000}"])
def test_useful_patterns_are_accepted_and_quick_on_a_hostile_name(pattern):
    compiled = name_regex(pattern)
    started = time.perf_counter()
    compiled.search("a" * 255)
    compiled.search("1" * 255)
    assert time.perf_counter() - started < 1


@pytest.mark.parametrize("pattern", ["(a+)+$", "(a|aa)*b", r"(\w+)\1", "(?=x)a", "(?<!x)a", ".*.*.*x",
                                     "a?" * 30 + "a" * 30,
                                     "(a|a)" * 20 + "b", "(a?){50}", "(a{2}){3}", "[", "(", "", "x" * (MAX_LENGTH + 1),
                                     "(?(1)a|b)", "(?P<n>a)(?P=n)", "(a*)?" * 9])
def test_patterns_that_could_hang_or_are_broken_are_refused(pattern):
    with pytest.raises(NameRegexError):
        name_regex(pattern)


def test_regular_expressions_ignore_case_and_match_anywhere(tree):
    assert _names(tree, text=r"^img_\d+\.jpe?g$", regex=True) == {
        "IMG_0001.JPG", "IMG_0002.jpeg", "IMG_0003.jpg", "IMG_0004.jpg"}
    assert _names(tree, text="0003", regex=True) == {"IMG_0003.jpg"}
    assert _names(tree, text="a.c") == set()  # without the choice it stays plain text


def test_excluded_folders_go_with_their_contents(tree):
    assert _names(tree, text="*.jpg", exclude="NODE_MODULES; old") == {"IMG_0001.JPG"}
    everything = _names(tree, exclude="node_modules")  # an exclusion alone lists the rest
    assert "IMG_0004.jpg" not in everything and "IMG_0003.jpg" in everything and "Photos" in everything


def test_depth_counts_from_the_searched_folder_and_prunes(tree, monkeypatch):
    assert _names(tree, max_depth=1) == {"Photos", "node_modules", "notes.txt"}
    assert _names(tree, text="img", min_depth=3) == {"IMG_0003.jpg"}
    assert _names(tree, text="img", min_depth=2, max_depth=2) == {"IMG_0001.JPG", "IMG_0002.jpeg", "IMG_0004.jpg"}
    looked = []
    monkeypatch.setattr(search_module, "give_way", lambda: looked.append(1))
    _names(tree, max_depth=1)
    assert len(looked) <= 4  # nothing below the first level is looked into
    photos = tree.children[0]
    assert _names(photos, max_depth=1) == {"IMG_0001.JPG", "IMG_0002.jpeg", "Old"}


def test_owners_are_looked_up_once_and_unknown_ones_never_match(tree, monkeypatch):
    looked = []

    def name(owner):
        looked.append(owner)
        return {1000: "DESKTOP\\Alice", 1001: "bob"}[owner]
    monkeypatch.setattr(search_module, "owner_name", name)
    assert _names(tree, owner="ALICE") == {"IMG_0001.JPG", "IMG_0003.jpg", "IMG_0004.jpg"}
    assert sorted(looked) == [1000, 1001]
    assert _names(tree, owner="uid:1001") == {"IMG_0002.jpeg"}
    assert _names(tree, owner="nobody") == set()


def test_all_conditions_hold_together_and_none_finds_nothing(tree):
    assert _names(tree, text=r"img.*\.jpe?g$", regex=True, exclude="old", min_depth=2, max_depth=2, kind="files") == {
        "IMG_0001.JPG", "IMG_0002.jpeg", "IMG_0004.jpg"}
    assert accepts(Query(regex=True, exclude=" ; ", owner=" "), 0) is None and _names(tree) == set()


@pytest.mark.parametrize("state", [{"regex": 1}, {"exclude": 3}, {"owner": None}, {"exclude": "x" * 501},
                                   {"min_depth": 0},
                                   {"max_depth": True}, {"min_depth": "1"}, {"max_depth": MAX_DEPTH + 1},
                                   {"min_depth": 3, "max_depth": 2}])
def test_malformed_saved_conditions_are_refused(state):
    with pytest.raises(ValueError):
        validate_more(state)


def test_the_dialog_edits_and_returns_them(qapp):
    dialog = SearchRangeDialog({"regex": True, "exclude": "a", "owner": "b", "min_depth": 2, "max_depth": 4})
    assert dialog.regex.isChecked() and dialog.exclude.text() == "a" and dialog.min_depth.value() == 2
    dialog.max_depth.setValue(1)
    dialog.accept()
    assert dialog.values is None and dialog.field_errors[dialog.max_depth].text() == i18n.tr("search_depth_error")
    dialog.max_depth.setValue(0)
    dialog.owner.setText("  ")
    dialog.accept()
    assert dialog.values["max_depth"] is None and dialog.values["owner"] == "" and dialog.values["regex"] is True
    dialog.deleteLater()


def test_the_panel_searches_shows_saves_and_removes_them(window, qapp, sample_tree):
    window.results.show_outcome(analyse(scan(sample_tree)))
    panel = window.results.search
    panel.box.setText(r"\.bin$")
    panel.filters.apply({"regex": True, "exclude": "code", "max_depth": 5})
    _wait(qapp, lambda: not panel.busy)
    shown = {key for key, label in panel.conditions_view.labels.items() if not label.isHidden()}
    assert shown == {"text", "exclude", "depth"}
    assert panel.conditions_view.labels["text"].text() == i18n.tr("search_condition_regex", value=r"\.bin$")
    assert panel.query() == Query(text=r"\.bin$", regex=True, exclude="code", max_depth=5)
    panel.save("mine")
    assert panel._searches["mine"] == {"text": r"\.bin$", **panel.filters.state()}
    panel.remove_condition("depth")
    panel.remove_condition("exclude")
    assert panel.query() == Query(text=r"\.bin$", regex=True)
    panel.box.setText("(a+)+")
    panel.rerun()
    assert panel._validation_error and panel.summary.text() == i18n.tr("search_regex_invalid")
    panel.save("broken")
    assert "broken" not in panel._searches
    panel.saved.setCurrentIndex(panel.saved.findData("mine"))
    panel._load_saved()
    _wait(qapp, lambda: not panel.busy)
    assert panel.query() == Query(text=r"\.bin$", regex=True, exclude="code", max_depth=5)
    panel.clear_conditions()
    assert panel.query() == Query()


def test_descriptions_name_every_condition():
    texts = descriptions("a", {"regex": True, "exclude": "b", "owner": "c", "min_depth": 2}, "auto")
    assert set(texts) == {"text", "exclude", "owner", "depth"}
    assert i18n.tr("search_no_limit") in texts["depth"] and re.search("2", texts["depth"])
