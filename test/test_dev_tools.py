"""Development tools are recognised by path, counted once, and their commands are only ever copied."""

import subprocess
import threading

import pytest
from PySide6.QtWidgets import QApplication

from test_gui import _wait, window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.core.dev_tools import TOOLS, dev_tools
from je_file_tree.core.node import Node
from je_file_tree.core.scanner import scan
from je_file_tree.gui import i18n, window_dialogs
from je_file_tree.gui.dev_tools import DevToolsDialog
from je_file_tree.gui.scan_worker import analyse


def _folder(parent, path, size=0, **fields):
    for name in path.split("/"):
        child = next((node for node in parent.children if node.name == name), None)
        if child is None:
            child = Node(name, True, children=[], parent=parent)
            parent.children.append(child)
        parent = child
    parent.size = parent.allocated = size
    for key, value in fields.items():
        setattr(parent, key, value)
    return parent


@pytest.fixture
def home():
    root = Node("C:\\Users\\me", True, children=[])
    _folder(root, "AppData/Local/pip/Cache", 500)
    _folder(root, "AppData/Local/NPM-CACHE", 900)
    _folder(root, ".cargo/registry", 70)
    _folder(root, ".cargo/git", 30)
    _folder(root, ".gradle/caches/.cache/pip", 5)
    _folder(root, "work/pip/Cache", 1)  # some other folder of the same name
    _folder(root, "go", 8)
    return root


def test_stores_are_recognised_counted_once_and_sorted(home):
    found = {use.tool.key: use for use in dev_tools(home)}
    assert set(found) == {"pip", "npm", "cargo", "gradle"}
    assert found["cargo"].size == 100 and len(found["cargo"].nodes) == 2
    assert [use.tool.key for use in dev_tools(home)][:2] == ["npm", "pip"]
    assert found["pip"].size == 500  # what lies inside another tool's store is not counted again


def test_links_errors_and_cancellation(home):
    _folder(home, "AppData/Local/uv/cache", 10, is_link=True)
    _folder(home, "AppData/Local/Yarn/Cache", 10, error="denied")
    found = {use.tool.key: use for use in dev_tools(home)}
    assert "uv" not in found and found["yarn"].incomplete and not found["pip"].incomplete
    cancel = threading.Event()
    cancel.set()
    assert dev_tools(home, cancel=cancel) is None


def test_anchored_paths_and_several_roots():
    system = Node("/", True, children=[])
    _folder(system, "var/lib/docker", 10)
    assert [use.tool.key for use in dev_tools(system)] == ["docker"]
    nested = Node("/home", True, children=[])
    _folder(nested, "me/var/lib/docker", 10)
    assert dev_tools(nested) == []
    virtual = Node("", True, children=[])
    drive = Node("D:\\", True, children=[], parent=virtual)
    virtual.children.append(drive)
    _folder(drive, "me/.ollama/models", 3)
    assert [use.tool.key for use in dev_tools(virtual)] == ["ollama"]


def test_the_table_of_tools_is_consistent():
    assert len({tool.key for tool in TOOLS}) == len(TOOLS)
    for tool in TOOLS:
        assert tool.name and tool.folders and tool.inspect and "\n" not in tool.inspect + tool.clean
        for folder in tool.folders:
            parts = folder.strip("/").split("/")
            assert all(parts) and "\\" not in folder and "*" not in parts[-1]
            assert len(parts) > 1 or folder.startswith("."), folder  # a bare common name would match anything


def test_commands_are_copied_and_never_run(qapp, home, monkeypatch):
    for name in ("run", "Popen", "call", "check_output"):
        monkeypatch.setattr(subprocess, name, lambda *_args, **_kwargs: pytest.fail("no command is ever run"))
    dialog = DevToolsDialog(home, "auto", partial=True)
    _wait(qapp, lambda: dialog.model.rowCount() == 4)
    assert not dialog.copy_clean.isEnabled() and i18n.tr("special_partial") in dialog.status.text()
    rows = {dialog.proxy.index(row, 0).data(): row for row in range(4)}
    dialog.view.setCurrentIndex(dialog.proxy.index(rows["pip"], 0))
    dialog.copy_clean.click()
    assert QApplication.clipboard().text() == "pip cache purge" and "pip cache purge" in dialog.status.text()
    dialog.copy_inspect.click()
    assert QApplication.clipboard().text() == "pip cache info"
    dialog.view.setCurrentIndex(dialog.proxy.index(rows["Cargo"], 0))
    assert not dialog.copy_clean.isEnabled()
    assert dialog.proxy.index(rows["Cargo"], 5).data() == i18n.tr("dev_tools_automatic")
    chosen = []
    dialog.selected.connect(chosen.append)
    dialog._select(dialog.proxy.index(rows["Cargo"], 0))
    assert [node.name for node in chosen] == ["registry"] and not dialog.worker.isRunning()
    dialog.deleteLater()


def test_nothing_found_is_said(qapp):
    dialog = DevToolsDialog(Node("C:\\empty", True, children=[]), "auto")
    _wait(qapp, lambda: dialog.status.text() == i18n.tr("dev_tools_none"))
    dialog.reject()
    dialog.deleteLater()


def test_the_window_opens_it_for_a_finished_scan(window, sample_tree, monkeypatch):
    opened = []
    monkeypatch.setattr(window_dialogs.DevToolsDialog, "exec", lambda dialog: opened.append(dialog) or 0)
    window.show_dev_tools()
    assert not opened
    window.results.show_outcome(analyse(scan(sample_tree)))
    window.show_dev_tools()
    assert len(opened) == 1
