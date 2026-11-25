"""The scan reads with fewer threads while other programs use the processors, and never with none."""

import threading

import pytest

from test_gui import window as window  # noqa: PLC0414 - explicit fixture re-export
from je_file_tree.core import cpu_load, scanner
from je_file_tree.core.cpu_load import SAMPLE_SECONDS, WorkerGovernor
from je_file_tree.core.scanner import ScanOptions, scan
from je_file_tree.gui import window_scans
from je_file_tree.gui.window_settings import AUTO_CPU_KEY, read_flag


class _Machine:
    """Eight processors whose other programs keep ``others`` of them busy; this process uses ``own``."""

    def __init__(self) -> None:
        self.now = self.busy = self.total = self.used = 0.0

    def run(self, *, others: float, own: float = 0.0, seconds: float = SAMPLE_SECONDS) -> None:
        self.now += seconds
        self.total += 8 * seconds
        self.used += own * seconds
        self.busy += (others + own) * seconds

    def governor(self, ceiling: int) -> WorkerGovernor:
        return WorkerGovernor(ceiling, times=lambda: (self.busy, self.total), own=lambda: self.used,
                              clock=lambda: self.now, processors=8)


def test_threads_follow_the_processors_other_programs_leave_free():
    machine = _Machine()
    governor = machine.governor(4)
    assert governor.limit == 4
    machine.run(others=0.0, own=3.5)  # this scan's own work is not somebody else's
    assert governor.update() == 4
    seen = []
    for _ in range(5):
        machine.run(others=7.0, own=1.0)  # one processor left
        seen.append(governor.update())
    assert seen == [3, 2, 1, 1, 1]  # one step at a time, never below one
    for _ in range(4):
        machine.run(others=5.6, own=2.0)  # 2.4 free: two threads
        seen.append(governor.update())
    assert seen[5:] == [2, 2, 2, 2]
    for _ in range(4):
        machine.run(others=0.0, own=2.0)
    assert [governor.update() for _ in range(3)] == [3, 3, 3]  # one reading per sample period
    machine.run(others=0.0)
    assert governor.update() == 4
    machine.run(others=0.0)
    assert governor.update() == 4  # never past the chosen number


def test_readings_are_compared_once_per_sample_period():
    machine = _Machine()
    governor = machine.governor(4)
    machine.run(others=8.0, seconds=SAMPLE_SECONDS / 2)
    assert governor.update() == 4
    machine.run(others=8.0, seconds=SAMPLE_SECONDS / 2)
    assert governor.update() == 3


def test_without_a_reading_the_chosen_number_is_kept():
    now = [0.0]
    governor = WorkerGovernor(3, times=lambda: None, clock=lambda: now[0])
    now[0] += 5
    assert governor.update() == 3 and WorkerGovernor(0, times=lambda: None).limit == 1


def test_this_machine_reports_processor_time_or_nothing():
    reading = cpu_load.system_times()
    assert reading is None or 0 <= reading[0] <= reading[1]


def test_unreadable_processor_time_is_no_reading(monkeypatch):
    def refuse():
        raise OSError("refused")
    monkeypatch.setattr(cpu_load, "_windows_times", refuse)
    monkeypatch.setattr(cpu_load, "_linux_times", refuse)
    assert cpu_load.system_times() is None


@pytest.mark.parametrize("limit", [1, 2])
def test_adaptive_scan_reads_no_more_folders_at_once_than_allowed(tmp_path, monkeypatch, limit):
    for number in range(40):
        (tmp_path / f"folder{number}" / "inner").mkdir(parents=True)
        (tmp_path / f"folder{number}" / "file").write_bytes(b"12345")

    class Governor:
        def __init__(self, ceiling):
            assert ceiling == 4
            self.limit = limit

        def update(self):
            return self.limit

    lock, reading, most = threading.Lock(), [0], [0]
    read_folder = scanner._read_folder

    def counted(*args):
        with lock:
            reading[0] += 1
            most[0] = max(most[0], reading[0])
        try:
            threading.Event().wait(0.002)
            return read_folder(*args)
        finally:
            with lock:
                reading[0] -= 1

    monkeypatch.setattr(scanner, "WorkerGovernor", Governor)
    monkeypatch.setattr(scanner, "_read_folder", counted)
    result = scan(tmp_path, options=ScanOptions(workers=4, adaptive=True))
    assert most[0] == limit and not result.errors
    assert (result.root.file_count, result.root.dir_count, result.root.size) == (40, 80, 200)


def test_allowed_threads_change_while_the_scan_runs(tmp_path, monkeypatch):
    for number in range(60):
        (tmp_path / f"folder{number}").mkdir()
    limits = iter([1, 1, 3])

    class Governor:
        limit = 1

        def __init__(self, _ceiling):
            pass

        def update(self):
            self.limit = next(limits, 3)
            return self.limit

    lock, reading, most = threading.Lock(), [0], [0]
    read_folder = scanner._read_folder

    def counted(*args):
        with lock:
            reading[0] += 1
            most[0] = max(most[0], reading[0])
        try:
            threading.Event().wait(0.005)
            return read_folder(*args)
        finally:
            with lock:
                reading[0] -= 1

    monkeypatch.setattr(scanner, "WorkerGovernor", Governor)
    monkeypatch.setattr(scanner, "_read_folder", counted)
    result = scan(tmp_path, options=ScanOptions(workers=4, adaptive=True), progress_interval=0.01)
    assert most[0] == 3 and result.root.dir_count == 60


def test_a_plain_scan_has_no_governor(tmp_path, monkeypatch):
    monkeypatch.setattr(scanner, "WorkerGovernor", lambda _ceiling: pytest.fail("not asked for"))
    assert scan(tmp_path, options=ScanOptions(workers=2)).root.file_count == 0


def test_window_adjusts_by_default_and_remembers_the_choice(window):
    action = window._actions["auto_cpu"]
    assert action.isCheckable() and action.isChecked() and window._scan_options().adaptive
    assert action in window._menus["menu_options"].actions()
    action.trigger()
    assert not window._scan_options().adaptive and not read_flag(window.settings, AUTO_CPU_KEY, True)
    assert window._scan_options().workers == window_scans.DEFAULT_WORKERS
    action.trigger()
    assert window._scan_options().adaptive and read_flag(window.settings, AUTO_CPU_KEY, False)
