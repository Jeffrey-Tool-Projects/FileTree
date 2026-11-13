"""Physical-disk parsing from made-up sample outputs, degradation and the fixed, shell-less queries."""

from __future__ import annotations

import json
from pathlib import Path
import plistlib
import subprocess
import threading

import pytest

from je_file_tree.core import disks
from je_file_tree.core.disks import Partition, PhysicalDisk

_WINDOWS_SAMPLE = json.dumps([
    {"Id": "0", "Model": "Made-up NVMe 512GB", "Bus": "NVMe", "Media": "SSD", "Size": 512_000_000_000,
     "Health": "Healthy", "Style": "GPT", "Temperature": 41, "Wear": 3, "Hours": 1234, "Reliability": "",
     "Partitions": [
         {"Number": 1, "Offset": 1_048_576, "Size": 104_857_600, "Type": "System", "Letter": "\u0000",
          "Paths": ["\\\\?\\Volume{00000000-0000-0000-0000-000000000001}\\"], "FileSystem": "FAT32", "Label": ""},
         {"Number": 2, "Offset": 105_906_176, "Size": 16_777_216, "Type": "Reserved", "Letter": "\u0000",
          "Paths": [None], "FileSystem": "", "Label": ""},
         {"Number": 3, "Offset": 122_683_392, "Size": 400_000_000_000, "Type": "Basic", "Letter": "C",
          "Paths": ["C:\\", "D:\\Mounted\\", "\\\\?\\Volume{00000000-0000-0000-0000-000000000002}\\"],
          "FileSystem": "NTFS", "Label": "Owned"}]},
    {"Id": "1", "Model": "Made-up spinning disk", "Bus": 11, "Media": 3, "Size": 2_000_000_000_000,
     "Health": 1, "Style": 1, "Temperature": None, "Wear": None, "Hours": None,
     "Reliability": "PermissionDenied", "Partitions": []},
    {"Id": "2", "Model": "", "Bus": "Unknown", "Media": "Unspecified", "Size": None, "Health": "Unhealthy",
     "Style": "", "Temperature": 0, "Wear": 250, "Hours": None, "Reliability": "", "Partitions": "bad"},
])

_LSBLK_SAMPLE = json.dumps({"blockdevices": [
    {"name": "sda", "path": "/dev/sda", "type": "disk", "size": 1_000_204_886_016, "rota": True, "tran": "sata",
     "vendor": "ATA     ", "model": "Made-up HDD", "pttype": "gpt", "serial": "SHOULD-NOT-APPEAR",
     "mountpoints": [None],
     "children": [
         {"name": "sda1", "type": "part", "size": 536_870_912, "start": 2048, "partn": 1, "fstype": "vfat",
          "parttypename": "EFI System", "label": None, "mountpoints": ["/boot/efi"]},
         {"name": "sda2", "type": "part", "size": "999000000000", "start": "1050624", "fstype": "crypto_LUKS",
          "parttypename": "Linux filesystem", "mountpoints": [None],
          "children": [{"name": "luks-x", "type": "crypt", "fstype": "LVM2_member", "mountpoints": [None],
                        "children": [{"name": "vg-root", "type": "lvm", "mountpoints": ["/"]},
                                     {"name": "vg-home", "type": "lvm", "mountpoints": ["/home"]}]}]}]},
    {"name": "nvme0n1", "path": "/dev/nvme0n1", "type": "disk", "size": "256060514304", "rota": "0",
     "tran": "nvme", "model": "Made-up NVMe", "pttype": "dos", "mountpoint": None,
     "children": [{"name": "nvme0n1p1", "type": "part", "size": 256_000_000_000, "fstype": "ext4",
                   "partlabel": "data", "mountpoint": "/data"}]},
    {"name": "loop0", "type": "loop", "size": 4096},
    {"name": "zram0", "type": "disk", "size": 4096},
    {"name": "sr0", "type": "rom", "size": 1024},
]})


def _plist(value) -> bytes:
    return plistlib.dumps(value)


_DISKUTIL_LIST = _plist({"AllDisksAndPartitions": [
    {"DeviceIdentifier": "disk0", "Content": "GUID_partition_scheme", "Size": 500_277_790_720, "Partitions": [
        {"DeviceIdentifier": "disk0s1", "Content": "EFI", "Size": 314_572_800, "VolumeName": "EFI"},
        {"DeviceIdentifier": "disk0s2", "Content": "Apple_APFS", "Size": 499_963_174_912}]},
    {"DeviceIdentifier": "disk3", "Content": "EF57347C-0000-11AA-AA11-00306543ECAC", "Size": 499_963_174_912,
     "APFSPhysicalStores": [{"DeviceIdentifier": "disk0s2"}], "Partitions": [],
     "APFSVolumes": [{"DeviceIdentifier": "disk3s1", "MountPoint": "/", "VolumeName": "Owned HD"},
                     {"DeviceIdentifier": "disk3s5", "MountPoint": "/System/Volumes/Data"},
                     {"DeviceIdentifier": "disk3s6"}]},
    {"DeviceIdentifier": "disk4", "Content": "FDisk_partition_scheme", "Size": 64_000_000_000, "Partitions": [
        {"DeviceIdentifier": "disk4s1", "Content": "DOS_FAT_32", "Size": 63_000_000_000,
         "VolumeName": "STICK", "MountPoint": "/Volumes/STICK"}]},
    {"DeviceIdentifier": "disk5", "Content": "GUID_partition_scheme", "Size": 1_000_000, "Partitions": []},
    {"DeviceIdentifier": "disk6; rm -rf /", "Size": 1},
]})

_DISKUTIL_INFO = {
    "disk0": _plist({"DeviceNode": "/dev/disk0", "MediaName": "Made-up SSD", "BusProtocol": "PCI-Express",
                     "SolidState": True, "SMARTStatus": "Verified", "TotalSize": 500_277_790_720,
                     "VirtualOrPhysical": "Physical"}),
    "disk4": _plist({"DeviceNode": "/dev/disk4", "MediaName": "Made-up stick", "BusProtocol": "USB",
                     "SMARTStatus": "Not Supported", "VirtualOrPhysical": "Physical"}),
    "disk5": _plist({"DeviceNode": "/dev/disk5", "VirtualOrPhysical": "Virtual"}),
}


def test_windows_json_maps_every_field_and_keeps_unknowns_unknown() -> None:
    first, second, third = disks.parse_windows(_WINDOWS_SAMPLE)
    assert first.identifier == "\\\\.\\PhysicalDrive0" and first.model == "Made-up NVMe 512GB"
    assert (first.bus, first.media, first.health, first.style) == ("NVMe", "ssd", "healthy", "GPT")
    assert (first.temperature, first.wear, first.power_on_hours, first.counters) == (41, 3, 1234, "reported")
    assert [part.mounts for part in first.partitions] == [(), (), ("C:\\", "D:\\Mounted\\")]
    assert first.partitions[2] == Partition(3, 122_683_392, 400_000_000_000, "Basic", "Owned",
                                            ("C:\\", "D:\\Mounted\\"), "NTFS")
    assert (second.bus, second.media, second.health, second.style) == ("SATA", "hdd", "warning", "MBR")
    assert second.counters == "denied" and second.temperature is None
    assert (third.bus, third.media, third.health, third.size) == ("", "unknown", "unhealthy", None)
    assert third.temperature is None and third.wear is None and third.counters == "missing"
    assert third.partitions == ()


@pytest.mark.parametrize("text", ["", "[]"])
def test_windows_empty_output_means_no_disks(text) -> None:
    assert disks.parse_windows(text) == ()


@pytest.mark.parametrize("text", ["not json", "42", '"text"'])
def test_windows_other_output_is_refused(text) -> None:
    with pytest.raises(ValueError, match="Disk query output"):
        disks.parse_windows(text)


def test_windows_single_object_and_unknown_reliability_errors() -> None:
    (disk,) = disks.parse_windows(json.dumps({"Id": "7", "Reliability": "NotImplemented", "Health": "Lost"}))
    assert disk.identifier == "\\\\.\\PhysicalDrive7" and disk.counters == "missing" and disk.health == "unknown"


def test_lsblk_whole_disks_with_stacked_mounts_and_no_serial() -> None:
    sda, nvme = disks.parse_lsblk(_LSBLK_SAMPLE)
    assert (sda.identifier, sda.model, sda.bus, sda.media, sda.style) == (
        "/dev/sda", "ATA Made-up HDD", "SATA", "hdd", "GPT")
    assert sda.health == "unknown" and sda.counters == "unsupported"
    assert "SHOULD-NOT-APPEAR" not in repr(sda)
    efi, data = sda.partitions
    assert (efi.index, efi.offset, efi.kind, efi.mounts, efi.filesystem) == (
        1, 2048 * 512, "EFI System", ("/boot/efi",), "vfat")
    assert (data.index, data.offset, data.size, data.mounts) == (2, 1_050_624 * 512, 999_000_000_000,
                                                                ("/", "/home"))
    assert (nvme.media, nvme.bus, nvme.style, nvme.size) == ("ssd", "NVMe", "MBR", 256_060_514_304)
    assert nvme.partitions[0].mounts == ("/data",) and nvme.partitions[0].kind == "data"
    assert nvme.partitions[0].offset is None and nvme.partitions[0].index == 1


@pytest.mark.parametrize("text", ["nope", "[]", '{"blockdevices": 3}'])
def test_lsblk_other_output_is_refused(text) -> None:
    with pytest.raises(ValueError, match="lsblk"):
        disks.parse_lsblk(text)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_sysfs_fallback_reads_made_up_tree(tmp_path) -> None:
    block = tmp_path / "block"
    _write(block / "sda" / "device" / "model", "Made-up SATA SSD\n")
    _write(block / "sda" / "size", "2000\n")
    _write(block / "sda" / "queue" / "rotational", "0\n")
    _write(block / "sda" / "device" / "hwmon" / "hwmon3" / "temp1_input", "38600\n")
    _write(block / "sda" / "sda1" / "partition", "1\n")
    _write(block / "sda" / "sda1" / "start", "2048\n")
    _write(block / "sda" / "sda1" / "size", "1000\n")
    _write(block / "sdb" / "device" / "model", "No size disk")
    _write(block / "loop0" / "size", "100")
    _write(block / "dm-0" / "device" / "model", "mapper")
    (disk, other) = disks.sysfs_disks(str(block))
    assert (disk.identifier, disk.model, disk.media, disk.size, disk.temperature) == (
        "/dev/sda", "Made-up SATA SSD", "ssd", 1_024_000, 39)
    assert disk.partitions == (Partition(1, 2048 * 512, 512_000, "", "", (), ""),)
    assert (other.identifier, other.size, other.media, other.partitions) == ("/dev/sdb", None, "unknown", ())
    assert disks.sysfs_disks(str(tmp_path / "missing")) == ()


def test_sysfs_temperature_from_nvme_controller_hwmon(tmp_path) -> None:
    _write(tmp_path / "nvme0n1" / "device" / "hwmon1" / "temp1_input", "0")
    _write(tmp_path / "nvme0n1" / "device" / "hwmon2" / "temp1_input", "44850")
    assert disks.sysfs_temperature(str(tmp_path / "nvme0n1")) == 45
    assert disks.sysfs_temperature(str(tmp_path / "absent")) is None


def test_macos_folds_apfs_containers_and_skips_virtual_and_invalid_names() -> None:
    assert disks.whole_disk_ids(_DISKUTIL_LIST) == ("disk0", "disk4", "disk5")
    internal, stick = disks.parse_macos(_DISKUTIL_LIST, _DISKUTIL_INFO)
    assert (internal.identifier, internal.model, internal.bus, internal.media, internal.health) == (
        "/dev/disk0", "Made-up SSD", "PCI-Express", "ssd", "healthy")
    assert internal.style == "GPT" and internal.counters == "unsupported"
    efi, apfs = internal.partitions
    assert (efi.index, efi.kind, efi.label, efi.mounts) == (1, "EFI", "EFI", ())
    assert (apfs.index, apfs.filesystem, apfs.mounts) == (2, "APFS", ("/", "/System/Volumes/Data"))
    assert (stick.media, stick.health, stick.style, stick.size) == ("unknown", "unknown", "MBR", 64_000_000_000)
    assert stick.partitions[0].mounts == ("/Volumes/STICK",)


def test_macos_missing_or_unreadable_info_keeps_listing_values() -> None:
    (disk0, disk4, disk5) = disks.parse_macos(_DISKUTIL_LIST, {"disk0": b"garbage"})
    assert disk0.identifier == "/dev/disk0" and disk0.model == "" and disk0.media == "unknown"
    assert disk0.size == 500_277_790_720 and disk4.size == 64_000_000_000 and disk5.size == 1_000_000
    with pytest.raises(ValueError, match="diskutil"):
        disks.parse_macos(b"not a plist", {})


def _disk(*parts: Partition, size: int | None = 1000) -> PhysicalDisk:
    return PhysicalDisk("d", "", "", "unknown", size, "unknown", "", None, None, None, "missing", parts)


def test_layout_places_partitions_by_offset_and_shows_real_gaps() -> None:
    disk = _disk(Partition(2, 600, 400, "", "", (), ""), Partition(1, 0, 300, "", "", (), ""))
    segments = disks.layout_segments(disk)
    assert [(round(s.start, 3), round(s.width, 3), s.partition) for s in segments] == [
        (0.0, 0.3, 1), (0.3, 0.3, None), (0.6, 0.4, 0)]


def test_layout_packs_partitions_without_offsets_and_tolerates_unknown_sizes() -> None:
    disk = _disk(Partition(1, None, 250, "", "", (), ""), Partition(2, 10, None, "", "", (), ""),
                 Partition(3, None, 250, "", "", (), ""), size=None)
    segments = disks.layout_segments(disk)
    assert [(s.start, s.width, s.partition) for s in segments] == [(0.0, 0.5, 0), (0.5, 0.5, 2)]
    assert disks.layout_segments(_disk(size=None)) == ()
    assert [s.partition for s in disks.layout_segments(_disk())] == [None]


def test_windows_command_is_fixed_and_cannot_be_requoted() -> None:
    command = disks.windows_command("C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe")
    assert command[1:5] == ["-NoLogo", "-NoProfile", "-NonInteractive", "-Command"] and len(command) == 6
    script = command[5]
    assert '"' not in script and "SerialNumber" not in script
    for verb in ("Set-", "Remove-", "Format-", "Clear-", "Initialize-", "New-", "Resize-", "Invoke-"):
        assert verb not in script


class _Process:
    def __init__(self, outputs, returncode=0):
        self._outputs = list(outputs)
        self.returncode = returncode
        self.killed = False

    def communicate(self, timeout=None):
        result = self._outputs.pop(0) if self._outputs else (b"", b"")
        if isinstance(result, BaseException):
            raise result
        return result

    def kill(self):
        self.killed = True


def test_run_returns_output_and_reports_failures(monkeypatch) -> None:
    calls = []
    def popen(command, **kwargs):
        calls.append((command, kwargs))
        return _Process([(b"[]", b"")])
    monkeypatch.setattr(disks.subprocess, "Popen", popen)
    assert disks._run(["/fixed/tool", "--json"], 5, None) == b"[]"
    command, options = calls[0]
    assert command == ["/fixed/tool", "--json"] and "shell" not in options
    monkeypatch.setattr(disks.subprocess, "Popen", lambda *_a, **_k: _Process([(b"", b"denied")], 1))
    with pytest.raises(disks._QueryError) as failed:
        disks._run(["/fixed/tool"], 5, None)
    assert failed.value.problem == "failed" and failed.value.detail == "denied"
    def missing(*_args, **_kwargs):
        raise FileNotFoundError("no tool")
    monkeypatch.setattr(disks.subprocess, "Popen", missing)
    with pytest.raises(disks._QueryError) as absent:
        disks._run(["/fixed/tool"], 5, None)
    assert absent.value.problem == "tool_missing"


def test_run_kills_on_cancel_and_timeout(monkeypatch) -> None:
    expired = subprocess.TimeoutExpired("tool", 0.1)
    process = _Process([expired, (b"", b"")])
    monkeypatch.setattr(disks.subprocess, "Popen", lambda *_a, **_k: process)
    cancel = threading.Event()
    cancel.set()
    assert disks._run(["/fixed/tool"], 5, cancel) is None and process.killed
    slow = _Process([expired, (b"", b"")])
    monkeypatch.setattr(disks.subprocess, "Popen", lambda *_a, **_k: slow)
    with pytest.raises(disks._QueryError) as timed_out:
        disks._run(["/fixed/tool"], -1, None)
    assert timed_out.value.problem == "timeout" and slow.killed


def test_survey_degrades_to_problem_codes(monkeypatch) -> None:
    monkeypatch.setattr(disks.sys, "platform", "sunos5")
    assert disks.physical_disks() == disks.DiskSurvey((), "unsupported", "sunos5")
    monkeypatch.setattr(disks.sys, "platform", "win32")
    def broken(_cancel):
        raise disks._QueryError("timeout")
    monkeypatch.setattr(disks, "_windows", broken)
    assert disks.physical_disks().problem == "timeout"
    def malformed(_cancel):
        raise ValueError("Disk query output is not JSON")
    monkeypatch.setattr(disks, "_windows", malformed)
    survey = disks.physical_disks()
    assert survey.problem == "malformed" and "JSON" in survey.detail
    monkeypatch.setattr(disks, "_windows", lambda _cancel: None)
    assert disks.physical_disks() is None
    monkeypatch.setattr(disks, "_windows", lambda _cancel: disks.parse_windows(_WINDOWS_SAMPLE))
    assert len(disks.physical_disks().disks) == 3


def test_windows_provider_uses_the_system_powershell(monkeypatch) -> None:
    seen = []
    monkeypatch.setattr(disks, "_windows_powershell", lambda: "C:\\Fixed\\powershell.exe")
    monkeypatch.setattr(disks.os.path, "isfile", lambda path: path == "C:\\Fixed\\powershell.exe")
    monkeypatch.setattr(disks, "_run", lambda command, timeout, cancel: seen.append(command)
                        or ("\ufeff" + _WINDOWS_SAMPLE).encode("utf-8"))
    assert len(disks._windows(None)) == 3 and seen[0][0] == "C:\\Fixed\\powershell.exe"
    monkeypatch.setattr(disks.os.path, "isfile", lambda _path: False)
    with pytest.raises(disks._QueryError, match="tool_missing"):
        disks._windows(None)


def test_linux_provider_prefers_lsblk_and_falls_back_to_sysfs(monkeypatch) -> None:
    seen = []
    monkeypatch.setattr(disks.os.path, "isfile", lambda path: path == "/usr/bin/lsblk")
    monkeypatch.setattr(disks, "_run", lambda command, timeout, cancel: seen.append(command)
                        or _LSBLK_SAMPLE.encode("utf-8"))
    monkeypatch.setattr(disks, "sysfs_temperature", lambda folder: 40 if folder.endswith("nvme0n1") else None)
    found = disks._linux(None)
    assert seen == [["/usr/bin/lsblk", "--json", "--bytes", "--output-all"]]
    assert [disk.temperature for disk in found] == [None, 40]
    fallback = (_disk(),)
    monkeypatch.setattr(disks, "sysfs_disks", lambda root="/sys/block": fallback)
    monkeypatch.setattr(disks, "_run", lambda *_args: b"old lsblk text")
    assert disks._linux(None) == fallback
    monkeypatch.setattr(disks.os.path, "isfile", lambda _path: False)
    assert disks._linux(None) == fallback


def test_macos_provider_queries_only_validated_whole_disks(monkeypatch) -> None:
    seen = []
    def run(command, timeout, cancel):
        seen.append(command)
        if command[1] == "list":
            return _DISKUTIL_LIST
        if command[-1] == "disk4":
            raise disks._QueryError("failed")
        return _DISKUTIL_INFO[command[-1]]
    monkeypatch.setattr(disks.os.path, "isfile", lambda path: path == "/usr/sbin/diskutil")
    monkeypatch.setattr(disks, "_run", run)
    found = disks._macos(None)
    assert seen[0] == ["/usr/sbin/diskutil", "list", "-plist"]
    assert [command[-1] for command in seen[1:]] == ["disk0", "disk4", "disk5"]
    assert [disk.identifier for disk in found] == ["/dev/disk0", "/dev/disk4"]
    monkeypatch.setattr(disks, "_run", lambda command, timeout, cancel: None)
    assert disks._macos(None) is None
