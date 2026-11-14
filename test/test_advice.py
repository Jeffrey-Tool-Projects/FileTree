"""Removal advice: one careful answer per entry, shown beside the largest files and in the highlights."""

from __future__ import annotations

import pytest

from test_gui import _wait, window as window  # noqa: PLC0414 - shared fixture
from test_protected import WINDOWS_ENV
from je_file_tree.core.advice import LOW, MANAGED, PENDING, PERSONAL, PROTECTED, REVIEW, Adviser
from je_file_tree.core.cleanup import DETAILS, CleanupGroup
from je_file_tree.core.node import Node
from je_file_tree.core.protected import protected_places
from je_file_tree.core.scanner import scan
from je_file_tree.gui import advice_text, i18n
from je_file_tree.gui.scan_worker import analyse
from je_file_tree.gui.tables import SORT_ROLE, LargestFilesModel
from je_file_tree.gui.tree_model import SHARE_ROLE

_ADVICE_COLUMN, _SIZE_COLUMN = 2, 1


def _node(path: str, *, is_dir: bool = False, parent: Node | None = None, size: int = 1) -> Node:
    name = path if parent is None else path.rsplit("\\", 1)[-1]  # only a root keeps its whole path as its name
    node = Node(name, is_dir, size=size, parent=parent, children=[] if is_dir else ())
    if parent is not None:
        parent.children.append(node)
    return node


def _adviser(groups: list[CleanupGroup] | None) -> Adviser:
    return Adviser(protected_places("win32", WINDOWS_ENV), groups, platform="win32", environ=WINDOWS_ENV)


def test_the_most_careful_answer_wins() -> None:
    cache = _node(r"C:\Users\me\AppData\Local\Google\Chrome\User Data\Default\Cache", is_dir=True)
    inside = _node(cache.path + r"\data_1", parent=cache)
    dumps = _node(r"D:\work\crash.dmp")
    movie = _node(r"D:\Videos\holiday.mp4")
    program = _node(r"C:\Program Files\Tool\tool.exe")
    guarded_cache = _node(r"C:\ProgramData\App\Cache", is_dir=True)
    pagefile = _node(r"C:\pagefile.sys")
    groups = [CleanupGroup("browser_cache", [cache, guarded_cache], 2, DETAILS["browser_cache"]),
              CleanupGroup("crash_dumps", [dumps], 1, DETAILS["crash_dumps"])]
    adviser = _adviser(groups)
    assert adviser.advice(cache).kind == LOW
    assert adviser.advice(inside).kind == LOW, "a suggested folder covers what is inside it"
    assert adviser.advice(inside).group is groups[0]
    assert adviser.advice(dumps).kind == REVIEW
    assert adviser.advice(movie).kind == PERSONAL
    assert adviser.advice(program).kind == PROTECTED
    assert adviser.advice(guarded_cache).kind == PROTECTED, "a rule never overrides a protected place"
    assert adviser.advice(pagefile).kind == MANAGED
    ranks = [adviser.advice(node).rank for node in (cache, dumps, movie, program, pagefile)]
    assert ranks == sorted(ranks), "what can go sorts first, what must stay last"


def test_unknown_suggestions_are_pending_not_personal() -> None:
    movie = _node(r"D:\Videos\holiday.mp4")
    program = _node(r"C:\Windows\explorer.exe")
    waiting = _adviser(None)
    assert not waiting.ready
    assert waiting.advice(movie).kind == PENDING
    assert waiting.advice(program).kind == PROTECTED, "protection needs no clean-up analysis"
    assert _adviser([]).advice(movie).kind == PERSONAL


def test_advice_reads_no_children_and_no_disk(monkeypatch: pytest.MonkeyPatch) -> None:
    class Unreadable(list):
        def __iter__(self):
            pytest.fail("advice iterated the tree")

    folder = _node(r"D:\data", is_dir=True)
    file = _node(r"D:\data\big.bin", parent=folder)
    folder.children = Unreadable(folder.children)
    monkeypatch.setattr("os.lstat", lambda *_args, **_kwargs: pytest.fail("advice queried storage"))
    monkeypatch.setattr("os.stat", lambda *_args, **_kwargs: pytest.fail("advice queried storage"))
    assert _adviser([]).advice(file).kind == PERSONAL


@pytest.mark.parametrize("language", i18n.LANGUAGES)
def test_every_answer_is_worded_in_every_language(qapp, language: str) -> None:
    i18n.set_language(language)
    try:
        cache = _node(r"D:\cache", is_dir=True)
        adviser = _adviser([CleanupGroup("browser_cache", [cache], 1, DETAILS["browser_cache"])])
        nodes = [cache, _node(r"D:\movie.mp4"), _node(r"C:\Windows\explorer.exe"), _node(r"C:\pagefile.sys")]
        answers = [adviser.advice(node) for node in nodes] + [_adviser(None).advice(nodes[1])]
        labels = [advice_text.label(answer) for answer in answers]
        assert len(set(labels)) == len(labels) and all(labels)
        for answer in answers:
            assert advice_text.label(answer) in advice_text.summary(answer)
            assert not advice_text.dot(answer.kind).isNull()
        assert i18n.tr("protected_system") in advice_text.reason(answers[2])
    finally:
        i18n.set_language(i18n.DEFAULT_LANGUAGE)


def test_largest_files_show_size_bars_and_sortable_advice(qapp) -> None:
    big, small = _node(r"D:\big.iso", size=400), _node(r"C:\Windows\small.dll", size=100)
    model = LargestFilesModel()
    model.set_rows([big, small])
    assert model.index(0, _ADVICE_COLUMN).data() == "", "no adviser: the column stays empty"
    model.set_adviser(_adviser([]))
    assert model.index(0, _ADVICE_COLUMN).data() == i18n.tr("advice_personal")
    assert model.index(1, _ADVICE_COLUMN).data() == i18n.tr("advice_protected")
    assert model.index(0, _ADVICE_COLUMN).data(SORT_ROLE) < model.index(1, _ADVICE_COLUMN).data(SORT_ROLE)
    assert i18n.tr("advice_personal") in model.index(0, _ADVICE_COLUMN).data(qt_tooltip())
    assert model.index(0, 0).data(qt_tooltip()) == big.path, "other cells keep the full path"
    assert model.index(0, _SIZE_COLUMN).data(SHARE_ROLE) == 1.0
    assert model.index(1, _SIZE_COLUMN).data(SHARE_ROLE) == 0.25
    assert i18n.tr("advice_protected").casefold() in model.filter_text(1)


def qt_tooltip() -> object:
    from PySide6.QtCore import Qt
    return Qt.ItemDataRole.ToolTipRole


def test_results_answer_once_the_clean_up_analysis_is_done(window, sample_tree, qapp) -> None:
    results = window.results
    results.begin_scan()
    assert not results._adviser.ready
    outcome = analyse(scan(sample_tree))
    results.show_outcome(outcome)
    _wait(qapp, lambda: results.cleanup.proposal_summary is not None)
    assert results._adviser.ready
    kinds = {results._adviser.advice(node).kind for node in results.largest_model.rows()}
    assert PENDING not in kinds
    highlights = results.highlights
    shown = [button for button in highlights.files if not button.isHidden()]
    assert len(shown) == min(3, len(outcome.largest))
    assert not shown[0].icon().isNull() and outcome.largest[0].path in shown[0].toolTip()
    shown[0].click()
    assert results.selected_node() is outcome.largest[0]
    assert i18n.tr("column_advice") in results.details.facts.text()
    adviser = results._adviser
    results.set_unit("KB")
    results.retranslate()
    assert results._adviser is adviser, "unit and language changes do not rebuild the answers"
    results.begin_scan()
    assert not results._adviser.ready and all(button.isHidden() for button in highlights.files)
