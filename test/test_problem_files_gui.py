"""The problem list filters by kind, selects in the tree and joins its worker."""

from PySide6.QtCore import Qt

from test_gui import _wait, window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.core.node import Node
from je_file_tree.core.problem_files import BAD_NAME, EMPTY
from je_file_tree.core.scanner import scan
from je_file_tree.gui import i18n, window_dialogs
from je_file_tree.gui.problem_files import ProblemFilesDialog
from je_file_tree.gui.scan_worker import analyse
from je_file_tree.gui.tree_model import NODE_ROLE


def _root() -> Node:
    root = Node("root", True, children=[])
    for name, size in (("end.", 5), ("nul", 0), ("empty", 0), ("fine", 9)):
        root.children.append(Node(name, False, size=size, parent=root, children=()))
    return root


def test_list_filter_and_selection(qapp):
    dialog = ProblemFilesDialog(_root(), "auto", partial=True)
    _wait(qapp, lambda: dialog.model.rowCount() == 3)
    assert i18n.tr("special_partial") in dialog.status.text()
    dialog.filter.setCurrentIndex(dialog.filter.findData(EMPTY))
    assert dialog.model.rowCount() == 2 and "2" in dialog.filter.currentText()
    dialog.filter.setCurrentIndex(dialog.filter.findData(BAD_NAME))
    names = {dialog.model.index(row, 0).data() for row in range(dialog.model.rowCount())}
    assert names == {"end.", "nul"}
    chosen = []
    dialog.selected.connect(chosen.append)
    index = dialog.proxy.index(0, 0)
    dialog._select(index)
    assert chosen == [index.data(NODE_ROLE)] and not dialog.worker.isRunning()
    dialog.deleteLater()


def test_stop_and_close_join_the_worker(qapp):
    dialog = ProblemFilesDialog(_root(), "auto")
    dialog.stop()
    assert dialog.status.text() == i18n.tr("scan_cancelled") and not dialog.stop_button.isEnabled()
    dialog.reject()
    _wait(qapp, lambda: not dialog.worker.isRunning())
    dialog.deleteLater()


def test_the_window_opens_it_for_a_finished_scan_and_selects_the_choice(window, sample_tree, monkeypatch):
    opened = []

    def choose(dialog):
        opened.append(dialog)
        dialog.selected.emit(window.results.tree_model.root.children[0])
        return 0
    monkeypatch.setattr(window_dialogs.ProblemFilesDialog, "exec", choose)
    window.show_problem_files()
    assert opened == []
    window.results.show_outcome(analyse(scan(sample_tree)))
    window.show_problem_files()
    assert len(opened) == 1 and window.results.selected_node() is window.results.tree_model.root.children[0]


def test_columns_have_tooltips_and_text_in_every_language(qapp):
    dialog = ProblemFilesDialog(_root(), "auto")
    _wait(qapp, lambda: dialog.model.rowCount() == 3)
    assert dialog.model.index(0, 0).data(Qt.ItemDataRole.ToolTipRole)
    for table in i18n.STRINGS.values():
        assert len({table[f"problem_files_{kind}"] for kind in ("empty", "dead_link", "long_path", "bad_name")}) == 4
    dialog.reject()
    dialog.deleteLater()
