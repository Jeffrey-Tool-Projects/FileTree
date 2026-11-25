"""The Disks dialog with a made-up provider: details, partition bar, problems, languages and fixed tools."""

from __future__ import annotations

import threading

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox

from test_gui import _wait, window as window  # noqa: PLC0414 - explicit fixture re-export
from je_file_tree.core.disks import DiskSurvey, Partition, PhysicalDisk
from je_file_tree.gui import disks_dialog, i18n, system_files
from je_file_tree.gui import window_dialogs
from je_file_tree.gui.strings import STRINGS

_GB = 1_000_000_000
_SSD = PhysicalDisk("\\\\.\\PhysicalDrive0", "Made-up NVMe", "NVMe", "ssd", 100 * _GB, "healthy", "GPT", 41, 3,
                    1234, "reported",
                    (Partition(1, 0, 10 * _GB, "System", "", (), "FAT32"),
                     Partition(2, 10 * _GB, 60 * _GB, "Basic", "Owned", ("C:\\",), "NTFS"),
                     Partition(3, 80 * _GB, 20 * _GB, "Recovery", "", (), "NTFS")))
_HDD = PhysicalDisk("\\\\.\\PhysicalDrive1", "", "", "hdd", None, "unhealthy", "", None, None, None, "denied", ())


def _provider(*disks: PhysicalDisk, problem: str | None = None, detail: str = ""):
    calls = []
    def provide(*, cancel: threading.Event) -> DiskSurvey:
        calls.append(cancel)
        return DiskSurvey(tuple(disks), problem, detail)
    provide.calls = calls
    return provide


@pytest.fixture
def dialog(qapp):
    created = []
    def make(provider) -> disks_dialog.DisksDialog:
        shown = disks_dialog.DisksDialog("auto", provider=provider)
        shown.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
        created.append(shown)
        return shown
    yield make
    for shown in created:
        shown.reject()
        shown.deleteLater()
    i18n.set_language(i18n.DEFAULT_LANGUAGE)


def test_disk_list_details_bar_and_table_follow_the_selection(qapp, dialog) -> None:
    shown = dialog(_provider(_SSD, _HDD))
    _wait(qapp, lambda: shown.disks.rowCount() == 2)
    assert shown.status.text() == "Physical disks found: 2."
    assert shown.disks.index(0, 2).data() == "SSD" and shown.disks.index(0, 6).data() == "Healthy"
    assert shown.disks.index(1, 1).data() == "Unknown" and shown.disks.index(1, 5).data() == "Unknown"
    assert shown.selected_disk() is _SSD and shown.partitions.rowCount() == 3
    assert shown.partitions.index(1, 3).data() == "C:\\" and shown.partitions.index(1, 4).data() == "NTFS"
    assert shown.health.text().startswith("Health: Healthy. The drive reports no problems.")
    assert shown.counters.text() == "Temperature: 41 °C · Wear: 3% of rated life used · Powered on: 1,234 hours"
    assert shown.note.isHidden()
    assert [segment.partition for segment in shown.bar.segments] == [0, 1, None, 2]
    shown.partition_view.selectRow(2)
    assert shown.bar.selected == 2
    shown.show()
    qapp.processEvents()
    assert not shown.bar.grab().isNull()
    middle = shown.bar.segment_rects()[1].center()
    QTest.mouseClick(shown.bar, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, middle)
    assert shown.partition_view.currentIndex().row() == 1 and shown.bar.selected == 1
    free = shown.bar.segment_rects()[2].center()
    QTest.mouseClick(shown.bar, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, free)
    assert shown.partition_view.currentIndex().row() == 1
    shown.disk_view.selectRow(1)
    assert shown.partitions.rowCount() == 0 and shown.bar.segments == ()
    assert "Failing" in shown.health.text() and "Back up important files now" in shown.health.text()
    assert shown.counters.text().count("not available") == 3
    assert "administrator rights" in shown.note.text() and "No partitions" in shown.note.text()
    assert not shown.note.isHidden()


def test_problem_and_empty_surveys_explain_themselves(qapp, dialog) -> None:
    failed = dialog(_provider(problem="timeout", detail="system said no"))
    _wait(qapp, lambda: failed.survey is not None)
    assert "took too long" in failed.status.text() and failed.status.toolTip() == "system said no"
    assert failed.health.text() == "Select a disk to see its health and partitions."
    empty = dialog(_provider())
    _wait(qapp, lambda: empty.survey is not None)
    assert empty.status.text() == "The system reported no physical disks."


def test_refresh_replaces_the_query_and_close_ignores_late_results(qapp, dialog) -> None:
    provider = _provider(_SSD)
    shown = dialog(provider)
    _wait(qapp, lambda: shown.survey is not None)
    shown.refresh_button.click()
    assert shown.status.text() == "Reading physical disks…"
    _wait(qapp, lambda: shown.survey is not None and len(provider.calls) == 2)
    assert provider.calls[0].is_set() and shown.disks.rowCount() == 1
    shown.reject()
    shown._show(DiskSurvey((_SSD, _HDD)))
    shown.refresh()
    assert shown.disks.rowCount() == 1 and shown._closed and len(provider.calls) == 2


def test_a_cancelled_query_reports_nothing(qapp, dialog) -> None:
    started, results = threading.Event(), []
    def slow(*, cancel: threading.Event):
        started.set()
        cancel.wait(10)
    shown = dialog(slow)
    shown.worker.ready.connect(results.append)
    _wait(qapp, started.is_set)
    shown.reject()
    _wait(qapp, lambda: not shown.worker.isRunning())
    assert results == [] and shown.survey is None and shown.worker.cancel.is_set()


@pytest.mark.parametrize("language", list(STRINGS))
def test_every_text_retranslates(qapp, dialog, language) -> None:
    shown = dialog(_provider(_SSD, _HDD))
    _wait(qapp, lambda: shown.disks.rowCount() == 2)
    i18n.set_language(language)
    shown.retranslate()
    table = STRINGS[language]
    assert shown.windowTitle() == table["disks_title"] and shown.hint.text() == table["disks_hint"]
    assert shown.refresh_button.text() == table["disks_refresh"]
    assert shown.tool_buttons["disk_management"].text() == table["disks_tool_management"]
    assert shown.disks.headerData(6, Qt.Orientation.Horizontal) == table["disks_col_health"]
    assert shown.partitions.headerData(3, Qt.Orientation.Horizontal) == table["disks_col_mounts"]
    assert shown.disks.index(0, 6).data() == table["disks_state_healthy"]
    assert table["disks_meaning_healthy"] in shown.health.text()
    assert shown.status.text() == table["disks_summary"].format(count="2")
    assert shown.bar.accessibleName() == table["disks_bar_name"]


def test_tool_buttons_use_only_the_fixed_launcher(qapp, dialog, monkeypatch) -> None:
    opened, warnings = [], []
    monkeypatch.setattr(disks_dialog, "open_system_tool", lambda tool, path: opened.append((tool, path)) or True)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[-1]))
    shown = dialog(_provider(_SSD))
    for tool, button in shown.tool_buttons.items():
        button.click()
        assert opened[-1] == (tool, "")
    assert [tool for tool, _path in opened] == [tool for tool, _key in disks_dialog.TOOLS] and warnings == []
    monkeypatch.setattr(disks_dialog, "open_system_tool", lambda *_args: False)
    shown.open_tool("optimize")
    assert warnings == ["The Windows tool could not be opened."]


def test_fixed_disk_tools_open_through_the_shell_without_arguments(monkeypatch) -> None:
    commands, urls = [], []
    monkeypatch.setattr(system_files.sys, "platform", "win32")
    monkeypatch.setenv("SYSTEMROOT", "C:\\Windows")
    monkeypatch.setattr(system_files.subprocess, "Popen", commands.append)
    # Off Windows, Qt keeps the backslashes of a Windows path as %5C; the tool itself only runs on Windows.
    monkeypatch.setattr(system_files.QDesktopServices, "openUrl",
                        lambda url: urls.append(url.toString().replace("%5C", "/")) or True)
    for tool, _key in disks_dialog.TOOLS:
        assert system_files.open_system_tool(tool, "D:\\ignored")
    assert urls == ["file:///C:/Windows/System32/diskmgmt.msc", "file:///C:/Windows/System32/dfrgui.exe",
                    "ms-settings:disksandvolumes", "ms-settings:storagesense"]
    assert commands == []
    monkeypatch.setenv("SYSTEMROOT", "relative")
    assert not system_files.open_system_tool("disk_management", "")
    monkeypatch.setattr(system_files.sys, "platform", "linux")
    assert not system_files.open_system_tool("optimize", "")


def test_main_window_offers_disks_beside_volumes(qapp, window, monkeypatch) -> None:
    action = window._actions["disks"]
    assert action.text() == "Physical disks…" and action.isEnabled()
    menus = [entry.menu() for entry in window.menuBar().actions() if entry.menu() is not None]
    menu_actions = next(menu.actions() for menu in menus if window._actions["volumes"] in menu.actions())
    assert menu_actions.index(action) == menu_actions.index(window._actions["volumes"]) + 1
    events = []
    class FakeDialog:
        def __init__(self, unit, parent):
            events.append(("create", unit, parent))
        def exec(self):
            events.append("exec")
        def shutdown(self):
            events.append("shutdown")
        def deleteLater(self):  # noqa: N802 - Qt's name
            events.append("delete")
    monkeypatch.setattr(window_dialogs, "DisksDialog", FakeDialog)
    action.trigger()
    assert events == [("create", window._unit, window), "exec", "shutdown", "delete"]
    window._worker = object()
    window.show_disks()
    window._worker = None
    assert len(events) == 4


def test_tiny_partitions_stay_visible_and_clickable(qapp) -> None:
    bar = disks_dialog.PartitionBar()
    bar.resize(402, 30)
    tiny = PhysicalDisk("d", "", "", "ssd", 256 * _GB, "healthy", "GPT", None, None, None, "missing",
                        (Partition(1, 0, 100_000_000, "System", "", (), "FAT32"),
                         Partition(2, 100_000_000, 256 * _GB - 100_000_000, "Basic", "", ("C:\\",), "NTFS")))
    bar.set_disk(tiny)
    first, second = bar.segment_rects()
    assert first.width() >= 8 and first.right() < second.left() and second.right() == 400
    clicked = []
    bar.partition_clicked.connect(clicked.append)
    QTest.mouseClick(bar, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, first.center())
    assert clicked == [0]
    bar.deleteLater()


def test_partition_bar_ignores_clicks_without_a_disk(qapp) -> None:
    bar = disks_dialog.PartitionBar()
    clicked = []
    bar.partition_clicked.connect(clicked.append)
    bar.resize(200, 30)
    QTest.mouseClick(bar, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(50, 15))
    assert clicked == [] and not bar.grab().isNull()
    bar.deleteLater()
