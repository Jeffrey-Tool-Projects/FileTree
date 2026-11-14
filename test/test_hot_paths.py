"""The measured shortcuts of the whole-tree passes answer exactly like the plain definitions."""

import random
import threading

import pytest

from je_file_tree.core import analysis, cleanup
from je_file_tree.core.analysis import AGES, AnalysisCancelledError, age_of, age_stats, extension_of, summarise
from je_file_tree.core.cleanup import RULES, find_cleanup
from je_file_tree.core.coverage import coverage_of
from je_file_tree.core.node import Node, outermost
from je_file_tree.core.search import Query, search

_NOW = 1_800_000_000.0
_DAY = 86400.0
_NAMES = ("report.txt", "Thumbs.db", "a.TMP", "photo.JPG", ".bashrc", "noext", "trailing.", "x.pyc", "core.dmp",
          "desktop.ini", "~$draft.docx", "big.log", "data.tmp.bak", "match-me.bin")
_FOLDERS = ("src", "node_modules", "__pycache__", "Temp", "match-me", "cache", "build", "docs")


def _tree(seed: int, folders: int = 300) -> Node:
    rng = random.Random(seed)  # noqa: S311 - a repeatable made-up tree, not security
    root = Node("C:\\made-up", True, children=[])
    made = [root]
    for number in range(folders):
        parent = rng.choice(made)
        folder = Node(f"{rng.choice(_FOLDERS)}{number if rng.random() < .5 else ''}", True, children=[], parent=parent)
        parent.children.append(folder)
        made.append(folder)
        for index in range(rng.randint(0, 6)):
            modified = rng.choice((0.0, -5.0, _NOW + 9 * _DAY, _NOW - rng.uniform(0, 900) * _DAY,
                                   _NOW - 30 * _DAY, _NOW - 182.5 * _DAY, _NOW - 365 * _DAY, _NOW - 730 * _DAY))
            size = rng.randint(0, 5000)
            folder.children.append(Node(f"{index}{rng.choice(_NAMES)}", False, size=size, allocated=size,
                                        file_count=1, modified=modified, parent=folder))
    for folder in reversed(made):
        folder.size = sum(child.size for child in folder.children)
        folder.file_count = sum(child.file_count for child in folder.children)
        folder.modified = max((child.modified for child in folder.children), default=0.0)
    return root


@pytest.mark.parametrize("seed", range(4))
def test_age_totals_equal_the_group_of_every_file(seed):
    files = list(_tree(seed).iter_files())
    sizes, counts = dict.fromkeys(AGES, 0), dict.fromkeys(AGES, 0)
    for node in files:
        sizes[age_of(node.modified, _NOW)] += node.size
        counts[age_of(node.modified, _NOW)] += 1
    stats = age_stats(files, _NOW)
    assert [(stat.age, stat.size, stat.count) for stat in stats] == [(age, sizes[age], counts[age]) for age in AGES]
    assert age_stats(iter(files), _NOW) == stats  # an iterator is counted like a list


@pytest.mark.parametrize("seed", range(4))
def test_extension_totals_equal_extension_of_per_file(seed):
    root = _tree(seed)
    sizes: dict[str, int] = {}
    for node in root.iter_files():
        sizes[extension_of(node.name)] = sizes.get(extension_of(node.name), 0) + node.size
    summary = summarise(root, now=_NOW)
    assert {stat.extension: stat.size for stat in summary.extensions} == sizes
    assert [node.size for node in summary.largest] == sorted((node.size for node in root.iter_files()),
                                                              reverse=True)[:1000]


def test_a_summary_still_stops_when_cancelled_at_any_point(monkeypatch):
    root = _tree(1)
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(AnalysisCancelledError):
        summarise(root, now=_NOW, cancel=cancel)
    monkeypatch.setattr(analysis, "_CANCEL_STRIDE", 7)
    files = list(root.iter_files())
    seen = 0
    late = threading.Event()
    with pytest.raises(AnalysisCancelledError):
        for _node in analysis._checked_files(files, late):
            seen += 1
            if seen == 10:
                late.set()
    assert seen == 14  # the batch in hand is finished; the next one is not started


@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("query", ["match-me", "*.tmp", "cache", Query(text="src", kind="folders"), Query(min_size=1)])
def test_a_search_total_counts_each_outermost_match_once(seed, query):
    root = _tree(seed)
    result = search(root, query, limit=10**9, now=_NOW)
    assert result is not None and result.count == len(result.matches)
    assert result.size == sum(node.size for node in outermost(result.matches))


@pytest.mark.parametrize("seed", range(4))
def test_one_combined_file_pattern_finds_what_the_rules_find_one_by_one(seed):
    root = _tree(seed)
    matcher = cleanup._Matcher(RULES, _NOW)

    def one_by_one(node: Node, folder_name: str) -> str | None:
        for names, rule in matcher._files:
            if (names.match(node.name) and (rule.in_folder is None or folder_name == rule.in_folder.casefold())
                    and matcher.old_enough(node, rule.details.minimum_age)):
                return rule.key
        return None

    checked = 0
    for folder in root.iter_nodes():
        for child in folder.children:
            if not child.is_dir:
                assert matcher.file_key(child, folder.name.casefold()) == one_by_one(child, folder.name.casefold())
                checked += 1
    assert checked > 200
    assert find_cleanup(root, now=_NOW) is not None


def test_a_matcher_without_file_rules_matches_no_file():
    rules = tuple(rule for rule in RULES if not rule.files)
    assert cleanup._Matcher(rules, _NOW).file_key(Node("a.tmp", False, modified=1.0), "") is None


def test_coverage_counts_folders_with_a_path_and_not_a_virtual_root():
    real = _tree(2, folders=40)
    survey = coverage_of(real)
    assert survey is not None and survey.known_folders == sum(1 for node in real.iter_nodes() if node.is_dir)
    virtual = Node("", True, children=[real])
    real.parent = virtual
    assert virtual.path is None
    assert coverage_of(virtual).known_folders == survey.known_folders  # the pathless root is not counted
