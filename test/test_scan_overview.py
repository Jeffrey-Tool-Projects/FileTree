"""Saved scans of several computers are compared as numbers; they never become entries that can be acted on."""

import csv
import json
import threading

import pytest
from PySide6.QtWidgets import QFileDialog, QInputDialog

from test_gui import _wait, window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.core import scan_overview as module
from je_file_tree.core.compare import SavedScanError
from je_file_tree.core.export import JSON_FORMAT
from je_file_tree.core.node import Node
from je_file_tree.core.scan_overview import MAX_LABEL, MAX_SCANS, import_scan, overview, unique_label
from je_file_tree.gui import i18n, window_dialogs
from je_file_tree.gui.scan_overview import ScanOverviewDialog


def _save(path, folders: dict, root="C:\\", saved="2026-11-01T10:00:00"):
    """A saved scan with ``{name: size or (size, children)}``."""
    def nested(entries):
        return [{"name": name, "size": value[0] if isinstance(value, tuple) else value,
                 "children": nested(value[1]) if isinstance(value, tuple) else []} for name, value in entries.items()]
    total = sum(value[0] if isinstance(value, tuple) else value for value in folders.values())
    path.write_text(json.dumps({"format": JSON_FORMAT, "saved": saved,
                                "root": {"name": root, "size": total, "children": nested(folders)}}), encoding="utf-8")
    return path


@pytest.fixture
def files(tmp_path):
    return (_save(tmp_path / "Desk.json", {"Users": (90, {"me": (80, {"Downloads": 70})}), "Windows": 40}),
            _save(tmp_path / "Laptop.json", {"Users": (30, {"me": 20}), "Games": 500}, root="D:\\"))


def test_folders_share_rows_by_relative_path(files):
    result = overview([import_scan(file) for file in files], depth=2)
    rows = {row.path: (row.sizes, row.spread) for row in result.rows}
    assert rows == {"": ((130, 530), 400), "Games": ((None, 500), 500), "Users": ((90, 30), 60),
                    "Users/me": ((80, 20), 60), "Windows": ((40, None), 40)}
    assert [row.path for row in result.rows][:2] == ["", "Games"] and result.count == 5
    assert [scan.label for scan in result.scans] == ["Desk", "Laptop"]
    assert overview(result.scans, depth=3).count == 6 and len(overview(result.scans, limit=2).rows) == 2
    assert overview(result.scans, depth=0).count == 1


def test_limits_cancellation_and_labels(files):
    scans = [import_scan(file) for file in files]
    cancel = threading.Event()
    cancel.set()
    assert overview(scans, cancel=cancel) is None
    for bad in ([], scans * MAX_SCANS):
        with pytest.raises(ValueError):
            overview(bad)
    assert unique_label("PC", ["PC", "PC (2)"]) == "PC (3)" and unique_label(" a \n b ", []) == "a b"
    assert unique_label("", []) == "scan" and len(unique_label("x" * 500, [])) == MAX_LABEL


@pytest.mark.parametrize("text", ["", "{}", '{"format": "other"}', "[" * 100_000,
                                  '{"format": "file-tree/1", "root": 5}'])
def test_other_files_are_refused(tmp_path, text):
    path = tmp_path / "bad.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(SavedScanError):
        import_scan(path)


def test_oversized_files_are_refused_before_reading(files, monkeypatch):
    monkeypatch.setattr(module, "MAX_BYTES", 10)
    monkeypatch.setattr(module, "load_saved", lambda _path: pytest.fail("not read"))
    with pytest.raises(SavedScanError):
        import_scan(files[0])


@pytest.fixture
def dialog(qapp):
    made = ScanOverviewDialog("B")
    yield made
    made.reject()
    made.deleteLater()


def test_add_rename_remove_and_sort(dialog, qapp, files, tmp_path, monkeypatch):
    broken = tmp_path / "broken.json"
    broken.write_text("no", encoding="utf-8")
    assert not dialog.csv.isEnabled()
    dialog.add_files([str(files[0]), str(broken), str(files[1])])
    _wait(qapp, lambda: dialog._current is None)
    assert dialog.table.columnCount() == 4 and dialog.table.rowCount() == 5 and dialog.list.count() == 2
    assert "broken.json" in dialog.status.text() and dialog.csv.isEnabled()
    dialog.table.sortItems(2)
    assert dialog.table.item(0, 2).text() == "—"  # numbers sort as numbers, unknown first
    assert dialog.table.item(4, 2).text().startswith("530")
    dialog.add_files([str(files[0])])
    _wait(qapp, lambda: dialog._current is None)
    assert [scan.label for scan in dialog._scans] == ["Desk", "Laptop", "Desk (2)"]
    dialog.list.setCurrentRow(2)
    monkeypatch.setattr(QInputDialog, "getText", lambda *_args, **_kwargs: ("Laptop", True))
    dialog._rename()
    _wait(qapp, lambda: dialog._current is None)
    assert dialog._scans[2].label == "Laptop (2)" and dialog.table.horizontalHeaderItem(3).text() == "Laptop (2)"
    for _ in range(3):
        dialog.list.setCurrentRow(0)
        dialog._remove()
        _wait(qapp, lambda: dialog._current is None)
    assert dialog._scans == [] and dialog.table.rowCount() == 0 and not dialog.csv.isEnabled()
    assert dialog.status.text() == i18n.tr("overview_scans_empty")


def test_depth_changes_and_quick_additions_keep_every_file(dialog, qapp, files):
    dialog.add_files([str(files[0])])
    dialog.add_files([str(files[1])])  # before the first is read
    _wait(qapp, lambda: dialog._current is None)
    assert [scan.label for scan in dialog._scans] == ["Desk", "Laptop"]
    dialog.depth.setValue(3)
    _wait(qapp, lambda: dialog._current is None)
    assert dialog.table.rowCount() == 6


def test_at_most_sixteen_scans(dialog, qapp, files):
    dialog.add_files([str(files[0])] * (MAX_SCANS + 3))
    _wait(qapp, lambda: dialog._current is None)
    assert len(dialog._scans) == MAX_SCANS and not dialog.add.isEnabled()
    assert i18n.tr("overview_scans_limit", limit=str(MAX_SCANS)) in dialog.status.text()


def test_quick_additions_past_the_limit_end(dialog, qapp, files):
    dialog.add_files([str(files[0])] * MAX_SCANS)
    dialog.add_files([str(files[1])] * 4)  # before the first ones are read
    _wait(qapp, lambda: dialog._current is None)
    assert len(dialog._scans) == MAX_SCANS
    assert i18n.tr("overview_scans_limit", limit=str(MAX_SCANS)) in dialog.status.text()


def test_reports_hold_exact_bytes_and_escape_names(dialog, qapp, tmp_path, monkeypatch):
    hostile = _save(tmp_path / "=cmd<script>.json".replace("<script>", "x"), {"=SUM(A1)": 5, "<b>bold</b>": 7})
    dialog.add_files([str(hostile)])
    _wait(qapp, lambda: dialog._current is None)
    for kind in ("csv", "html"):
        target = tmp_path / f"out.{kind}"
        monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *_args, path=target: (str(path), ""))
        dialog._export(kind)
        assert target.exists()
    with (tmp_path / "out.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    assert rows[0][1] == "'=cmdx" and ["'=SUM(A1)", "5", "0"] in rows
    html = (tmp_path / "out.html").read_text(encoding="utf-8")
    assert "<b>bold</b>" not in html and "&lt;b&gt;bold&lt;/b&gt;" in html
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *_args: ("", ""))
    dialog._export("csv")


def test_a_failed_export_says_so(dialog, qapp, files, tmp_path, monkeypatch):
    dialog.add_files([str(files[0])])
    _wait(qapp, lambda: dialog._current is None)
    told = []
    monkeypatch.setattr("je_file_tree.gui.scan_overview.QMessageBox.warning", lambda *args: told.append(args[2]))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *_args: (str(tmp_path / "missing" / "x.csv"), ""))
    dialog._export("csv")
    assert len(told) == 1


def test_imported_scans_never_become_nodes(files):
    result = overview([import_scan(file) for file in files])
    seen, stack = set(), [result]
    while stack:
        value = stack.pop()
        assert not isinstance(value, Node)
        if id(value) in seen:
            continue
        seen.add(id(value))
        if isinstance(value, (tuple, list)):
            stack.extend(value)
        elif isinstance(value, dict):
            stack.extend(value.values())
        elif hasattr(value, "__slots__"):
            stack.extend(getattr(value, name) for name in value.__slots__)


def test_closing_joins_a_running_read(qapp, files):
    made = ScanOverviewDialog("B")
    made.add_files([str(file) for file in files])
    made.reject()
    _wait(qapp, lambda: not made._running or not any(worker.isRunning() for worker in made._running))
    made.deleteLater()


def test_the_window_opens_it_without_a_scan(window, monkeypatch):
    opened = []
    monkeypatch.setattr(window_dialogs.ScanOverviewDialog, "exec", lambda made: opened.append(made) or 0)
    window._actions["scan_overview"].trigger()
    assert len(opened) == 1
