"""Read-only physical-disk inventory: model, media, bus, health and partition layout.

Each platform has one fixed, shell-less query whose output is parsed by pure functions:

- Windows: System32 ``powershell.exe -NoProfile -NonInteractive -Command`` with a constant script
  (``Get-PhysicalDisk``/``Get-StorageReliabilityCounter``/``Get-Disk``/``Get-Partition``/``Get-Volume``);
  no user text reaches the command line. Measured on a one-NVMe laptop (2026-11-14): 6.0 s, most of it
  loading the Storage module, hence the generous timeout.
- Linux: ``lsblk --json --bytes --output-all`` when installed, otherwise ``/sys/block`` alone; NVMe and
  ``drivetemp`` temperatures come from the readable ``hwmon`` files. SMART health needs root tools that
  FileTree does not run, so it stays unknown.
- macOS: ``diskutil list -plist`` plus ``diskutil info -plist diskN`` for each validated whole disk.

Fields the system does not report stay unknown (``None``/``""``/``"unknown"``) instead of failing; a
failed query is returned as a :class:`DiskSurvey` problem code. Nothing here writes to a disk, asks for
elevation or runs anything but these fixed programs.
"""

from __future__ import annotations

import ctypes
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
import glob
import json
import os
import plistlib
import re
import subprocess  # nosec B404 - fixed absolute system programs, never a shell
import sys
import threading
import time
from typing import Any
from xml.parsers.expat import ExpatError

MEDIA_SSD, MEDIA_HDD, MEDIA_UNKNOWN = "ssd", "hdd", "unknown"
HEALTHY, WARNING, UNHEALTHY, HEALTH_UNKNOWN = "healthy", "warning", "unhealthy", "unknown"
COUNTERS_REPORTED, COUNTERS_DENIED, COUNTERS_MISSING, COUNTERS_UNSUPPORTED = (
    "reported", "denied", "missing", "unsupported")
PROBLEM_UNSUPPORTED, PROBLEM_TOOL_MISSING, PROBLEM_TIMEOUT, PROBLEM_FAILED, PROBLEM_MALFORMED = (
    "unsupported", "tool_missing", "timeout", "failed", "malformed")

_WINDOWS_TIMEOUT = 60.0
_POSIX_TIMEOUT = 20.0
_POLL = 0.1
_OUTPUT_LIMIT = 8 * 1024 * 1024
_DETAIL_LIMIT = 400
_DISK_LIMIT = 64
_SECTOR = 512
_MILLI = 1000
_PERCENT = 100
_LSBLK = ("/usr/bin/lsblk", "/bin/lsblk", "/usr/sbin/lsblk", "/sbin/lsblk")
_DISKUTIL = "/usr/sbin/diskutil"
_MAC_WHOLE_DISK = re.compile(r"disk\d{1,4}")
_SKIPPED_LINUX = ("loop", "ram", "zram", "dm-", "md", "sr", "fd", "nbd")
_VERBATIM_PATH = "\\\\?\\"

# The script contains no double quotes, so the Windows command-line quoting cannot alter it, and no value
# from FileTree or the user is ever inserted. Reliability counters can need administrator rights: the
# error category is recorded instead of asking for elevation.
_WINDOWS_SCRIPT = "; ".join((
    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8",
    "$ErrorActionPreference = 'Stop'",
    "$rows = foreach ($d in @(Get-PhysicalDisk)) { $rel = $null; $relCat = ''"
    "; try { $rel = Get-StorageReliabilityCounter -PhysicalDisk $d }"
    " catch { $relCat = [string]$_.CategoryInfo.Category }"
    "; $style = ''; $parts = @()"
    "; try { $disk = Get-Disk -Number ([int]$d.DeviceId); $style = [string]$disk.PartitionStyle"
    "; $parts = @(foreach ($p in @(Get-Partition -DiskNumber $disk.Number)) { $v = $null"
    "; try { $v = Get-Volume -Partition $p } catch { }"
    "; [pscustomobject]@{ Number = $p.PartitionNumber; Offset = $p.Offset; Size = $p.Size"
    "; Type = [string]$p.Type; Letter = [string]$p.DriveLetter; Paths = @($p.AccessPaths)"
    "; FileSystem = [string]$v.FileSystem; Label = [string]$v.FileSystemLabel } }) } catch { }"
    "; [pscustomobject]@{ Id = [string]$d.DeviceId; Model = [string]$d.FriendlyName; Bus = [string]$d.BusType"
    "; Media = [string]$d.MediaType; Size = $d.Size; Health = [string]$d.HealthStatus; Style = $style"
    "; Temperature = $rel.Temperature; Wear = $rel.Wear; Hours = $rel.PowerOnHours; Reliability = $relCat"
    "; Partitions = $parts } }",
    "ConvertTo-Json -InputObject @($rows) -Depth 4 -Compress",
))

_WINDOWS_BUS = {1: "SCSI", 2: "ATAPI", 3: "ATA", 4: "1394", 5: "SSA", 6: "Fibre Channel", 7: "USB", 8: "RAID",
                9: "iSCSI", 10: "SAS", 11: "SATA", 12: "SD", 13: "MMC", 14: "Virtual", 15: "File Backed Virtual",
                16: "Storage Spaces", 17: "NVMe"}
_MEDIA = {"ssd": MEDIA_SSD, "4": MEDIA_SSD, "scm": MEDIA_SSD, "5": MEDIA_SSD, "hdd": MEDIA_HDD, "3": MEDIA_HDD}
_HEALTH = {"healthy": HEALTHY, "0": HEALTHY, "warning": WARNING, "1": WARNING, "unhealthy": UNHEALTHY,
           "2": UNHEALTHY, "verified": HEALTHY, "failing": UNHEALTHY}
_STYLE = {"gpt": "GPT", "2": "GPT", "mbr": "MBR", "1": "MBR", "dos": "MBR", "raw": "RAW", "0": "RAW",
          "guid_partition_scheme": "GPT", "fdisk_partition_scheme": "MBR", "apple_partition_scheme": "APM"}
_LINUX_BUS = {"sata": "SATA", "ata": "ATA", "nvme": "NVMe", "usb": "USB", "sas": "SAS", "scsi": "SCSI",
              "mmc": "MMC", "virtio": "Virtio", "spi": "SPI", "fc": "Fibre Channel", "iscsi": "iSCSI"}


@dataclass(frozen=True, slots=True)
class Partition:
    """One partition as the system reports it; unknown values are ``None`` or empty."""

    index: int | None
    offset: int | None
    size: int | None
    kind: str
    label: str
    mounts: tuple[str, ...]
    filesystem: str


@dataclass(frozen=True, slots=True)
class PhysicalDisk:
    """One physical drive without its serial number.

    ``identifier`` is the system's device name (``\\\\.\\PhysicalDrive0``, ``/dev/sda``, ``/dev/disk0``).
    ``media`` is ``ssd``/``hdd``/``unknown``; ``health`` is ``healthy``/``warning``/``unhealthy``/``unknown``;
    ``counters`` says why temperature/wear/power-on hours may be missing (``reported``, ``denied``,
    ``missing`` or ``unsupported``). ``wear`` is the percentage of rated endurance used.
    """

    identifier: str
    model: str
    bus: str
    media: str
    size: int | None
    health: str
    style: str
    temperature: int | None
    wear: int | None
    power_on_hours: int | None
    counters: str
    partitions: tuple[Partition, ...]


@dataclass(frozen=True, slots=True)
class DiskSurvey:
    """The disks found, or a problem code (see ``PROBLEM_*``) with the system's own message."""

    disks: tuple[PhysicalDisk, ...]
    problem: str | None = None
    detail: str = ""


@dataclass(frozen=True, slots=True)
class Segment:
    """A share of a disk's bar: ``start`` and ``width`` are fractions; ``partition`` is None for free space."""

    start: float
    width: float
    partition: int | None


class _QueryError(Exception):
    def __init__(self, problem: str, detail: str = "") -> None:
        super().__init__(problem)
        self.problem = problem
        self.detail = detail[:_DETAIL_LIMIT]


def _integer(value: Any) -> int | None:
    """A non-negative whole number from JSON/plist/sysfs values; anything else is unknown."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float) and value.is_integer():
        return _integer(int(value))
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _text(value: Any) -> str:
    return value.replace("\0", "").strip() if isinstance(value, str) else ""


def _lookup(table: Mapping[str, str], value: Any, default: str) -> str:
    return table.get(_text(str(value) if isinstance(value, int) else value).casefold(), default)


def _unique(paths: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(path for path in paths if path))


# Windows --------------------------------------------------------------------------------------------------


def _windows_bus(value: Any) -> str:
    number = _integer(value)
    if number is not None:
        return _WINDOWS_BUS.get(number, "")
    text = _text(value)
    return "" if text.casefold() in {"", "unknown"} else text


def _windows_partition(row: Mapping[str, Any]) -> Partition:
    letter = _text(row.get("Letter"))
    paths = row.get("Paths") if isinstance(row.get("Paths"), list) else []
    mounts = [f"{letter.upper()}:\\"] if len(letter) == 1 and letter.isalpha() else []
    mounts.extend(_text(path) for path in paths if _text(path) and not _text(path).startswith(_VERBATIM_PATH))
    return Partition(_integer(row.get("Number")), _integer(row.get("Offset")), _integer(row.get("Size")),
                     _text(row.get("Type")), _text(row.get("Label")), _unique(mounts), _text(row.get("FileSystem")))


def _windows_counters(row: Mapping[str, Any]) -> tuple[int | None, int | None, int | None, str]:
    temperature = _integer(row.get("Temperature")) or None  # 0 means "not reported" on many drives
    wear, hours = _integer(row.get("Wear")), _integer(row.get("Hours"))
    if wear is not None and wear > _PERCENT:
        wear = None
    category = _text(row.get("Reliability"))
    if category:
        state = COUNTERS_DENIED if category.casefold() == "permissiondenied" else COUNTERS_MISSING
    else:
        state = COUNTERS_REPORTED if (temperature, wear, hours) != (None, None, None) else COUNTERS_MISSING
    return temperature, wear, hours, state


def _windows_disk(row: Mapping[str, Any]) -> PhysicalDisk:
    number = _integer(row.get("Id"))
    identifier = f"\\\\.\\PhysicalDrive{number}" if number is not None else _text(row.get("Id"))
    parts = row.get("Partitions") if isinstance(row.get("Partitions"), list) else []
    temperature, wear, hours, counters = _windows_counters(row)
    return PhysicalDisk(identifier, _text(row.get("Model")), _windows_bus(row.get("Bus")),
                        _lookup(_MEDIA, row.get("Media"), MEDIA_UNKNOWN), _integer(row.get("Size")),
                        _lookup(_HEALTH, row.get("Health"), HEALTH_UNKNOWN), _lookup(_STYLE, row.get("Style"), ""),
                        temperature, wear, hours, counters,
                        tuple(_windows_partition(part) for part in parts if isinstance(part, dict)))


def parse_windows(text: str) -> tuple[PhysicalDisk, ...]:
    """Disks from the constant Windows script's JSON; raises ValueError when it is not that JSON."""
    try:
        data = json.loads(text) if text.strip() else []
    except json.JSONDecodeError as error:
        raise ValueError("Disk query output is not JSON") from error
    rows = [data] if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError("Disk query output is not a list")
    return tuple(_windows_disk(row) for row in rows if isinstance(row, dict))


# Linux ----------------------------------------------------------------------------------------------------


def _flag(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = _text(str(value) if isinstance(value, int) else value)
    return {"1": True, "0": False, "true": True, "false": False}.get(text.casefold())


def _linux_media(rotational: Any) -> str:
    flag = _flag(rotational)
    return MEDIA_UNKNOWN if flag is None else MEDIA_HDD if flag else MEDIA_SSD


def _lsblk_mounts(row: Mapping[str, Any]) -> list[str]:
    mounts = row.get("mountpoints")
    found = list(mounts) if isinstance(mounts, list) else [row.get("mountpoint")]
    return [_text(mount) for mount in found if _text(mount)]


def _descendant_mounts(row: Mapping[str, Any]) -> tuple[str, ...]:
    """Mount points of a partition and of everything stacked on it (LUKS, LVM), without recursion."""
    found: list[str] = []
    pending = [row]
    while pending:
        current = pending.pop()
        found.extend(_lsblk_mounts(current))
        children = current.get("children")
        if isinstance(children, list):
            pending.extend(child for child in reversed(children) if isinstance(child, dict))
    return _unique(found)


def _partition_number(row: Mapping[str, Any]) -> int | None:
    number = _integer(row.get("partn"))
    if number is not None:
        return number
    match = re.search(r"(\d+)$", _text(row.get("name")))
    return int(match.group(1)) if match else None


def _lsblk_partition(row: Mapping[str, Any]) -> Partition:
    start = _integer(row.get("start"))
    kind = _text(row.get("parttypename")) or _text(row.get("partlabel"))
    return Partition(_partition_number(row), None if start is None else start * _SECTOR, _integer(row.get("size")),
                     kind, _text(row.get("label")), _descendant_mounts(row), _text(row.get("fstype")))


def _lsblk_disk(row: Mapping[str, Any]) -> PhysicalDisk:
    name = _text(row.get("name"))
    children = row.get("children") if isinstance(row.get("children"), list) else []
    parts = tuple(_lsblk_partition(child) for child in children
                  if isinstance(child, dict) and _text(child.get("type")) == "part")
    transport = _text(row.get("tran"))
    model = " ".join(part for part in (_text(row.get("vendor")), _text(row.get("model"))) if part)
    return PhysicalDisk(_text(row.get("path")) or f"/dev/{name}", model,
                        _LINUX_BUS.get(transport.casefold(), transport), _linux_media(row.get("rota")),
                        _integer(row.get("size")), HEALTH_UNKNOWN, _lookup(_STYLE, row.get("pttype"), ""),
                        None, None, None, COUNTERS_UNSUPPORTED, parts)


def parse_lsblk(text: str) -> tuple[PhysicalDisk, ...]:
    """Whole disks from ``lsblk --json --bytes --output-all``; raises ValueError on other output."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError("lsblk output is not JSON") from error
    devices = data.get("blockdevices") if isinstance(data, dict) else None
    if not isinstance(devices, list):
        raise ValueError("lsblk output has no block devices")
    return tuple(_lsblk_disk(row) for row in devices
                 if isinstance(row, dict) and _text(row.get("type")) == "disk"
                 and not _text(row.get("name")).startswith(_SKIPPED_LINUX))


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read(4096).strip()
    except OSError:
        return ""


def _sysfs_partition(folder: str) -> Partition:
    start, sectors = _integer(_read(os.path.join(folder, "start"))), _integer(_read(os.path.join(folder, "size")))
    return Partition(_integer(_read(os.path.join(folder, "partition"))),
                     None if start is None else start * _SECTOR, None if sectors is None else sectors * _SECTOR,
                     "", "", (), "")


def sysfs_temperature(folder: str) -> int | None:
    """Whole degrees Celsius from a block device's readable ``hwmon`` files (NVMe, ``drivetemp``)."""
    for pattern in ("device/hwmon*/temp1_input", "device/hwmon/hwmon*/temp1_input"):
        for path in sorted(glob.glob(os.path.join(glob.escape(folder), pattern))):
            value = _integer(_read(path))
            if value:
                return round(value / _MILLI)
    return None


def sysfs_disks(root: str = "/sys/block") -> tuple[PhysicalDisk, ...]:
    """Whole physical disks from ``/sys/block`` when lsblk is missing; partitions lack file systems/mounts."""
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return ()
    disks = []
    for name in names[:_DISK_LIMIT * 4]:
        folder = os.path.join(root, name)
        if name.startswith(_SKIPPED_LINUX) or not os.path.exists(os.path.join(folder, "device")):
            continue
        sectors = _integer(_read(os.path.join(folder, "size")))
        parts = tuple(_sysfs_partition(os.path.join(folder, child)) for child in sorted(_children(folder))
                      if os.path.isfile(os.path.join(folder, child, "partition")))
        disks.append(PhysicalDisk(f"/dev/{name}", _read(os.path.join(folder, "device", "model")), "",
                                  _linux_media(_read(os.path.join(folder, "queue", "rotational"))),
                                  None if sectors is None else sectors * _SECTOR, HEALTH_UNKNOWN, "",
                                  sysfs_temperature(folder), None, None, COUNTERS_UNSUPPORTED, parts))
    return tuple(disks[:_DISK_LIMIT])


def _children(folder: str) -> list[str]:
    try:
        return os.listdir(folder)
    except OSError:
        return []


# macOS ----------------------------------------------------------------------------------------------------


def _plist(data: bytes) -> dict[str, Any]:
    try:
        value = plistlib.loads(data)
    except (plistlib.InvalidFileException, ExpatError, AttributeError, ValueError, TypeError) as error:
        raise ValueError("diskutil output is not a property list") from error
    if not isinstance(value, dict):
        raise ValueError("diskutil output is not a dictionary")
    return value


def _entries(listing: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = listing.get("AllDisksAndPartitions")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def whole_disk_ids(listing: bytes) -> tuple[str, ...]:
    """Validated ``diskN`` names of non-synthesized whole disks in ``diskutil list -plist`` output."""
    found = (_text(row.get("DeviceIdentifier")) for row in _entries(_plist(listing))
             if "APFSPhysicalStores" not in row)
    return tuple(name for name in found if _MAC_WHOLE_DISK.fullmatch(name))[:_DISK_LIMIT]


def _apfs_mounts(entries: Sequence[Mapping[str, Any]]) -> dict[str, tuple[str, ...]]:
    """Physical store partition -> mount points of the APFS volumes in its container."""
    mounts: dict[str, tuple[str, ...]] = {}
    for row in entries:
        stores, volumes = row.get("APFSPhysicalStores"), row.get("APFSVolumes")
        if not isinstance(stores, list) or not isinstance(volumes, list):
            continue
        points = _unique(_text(volume.get("MountPoint")) for volume in volumes if isinstance(volume, dict))
        for store in stores:
            if isinstance(store, dict):
                key = _text(store.get("DeviceIdentifier"))
                mounts[key] = _unique((*mounts.get(key, ()), *points))
    return mounts


def _mac_partition(row: Mapping[str, Any], apfs: Mapping[str, tuple[str, ...]]) -> Partition:
    name = _text(row.get("DeviceIdentifier"))
    match = re.search(r"s(\d+)$", name)
    content = _text(row.get("Content"))
    mounts = _unique((_text(row.get("MountPoint")), *apfs.get(name, ())))
    return Partition(int(match.group(1)) if match else None, None, _integer(row.get("Size")), content,
                     _text(row.get("VolumeName")), mounts, "APFS" if content == "Apple_APFS" else "")


def _mac_disk(row: Mapping[str, Any], info: Mapping[str, Any], apfs: Mapping[str, tuple[str, ...]]) -> PhysicalDisk:
    name = _text(row.get("DeviceIdentifier"))
    solid = info.get("SolidState")
    media = MEDIA_UNKNOWN if not isinstance(solid, bool) else MEDIA_SSD if solid else MEDIA_HDD
    parts = row.get("Partitions") if isinstance(row.get("Partitions"), list) else []
    return PhysicalDisk(_text(info.get("DeviceNode")) or f"/dev/{name}", _text(info.get("MediaName")),
                        _text(info.get("BusProtocol")), media,
                        _integer(info.get("TotalSize")) or _integer(row.get("Size")),
                        _lookup(_HEALTH, info.get("SMARTStatus"), HEALTH_UNKNOWN),
                        _lookup(_STYLE, row.get("Content"), ""), None, None, None, COUNTERS_UNSUPPORTED,
                        tuple(_mac_partition(part, apfs) for part in parts if isinstance(part, dict)))


def parse_macos(listing: bytes, infos: Mapping[str, bytes]) -> tuple[PhysicalDisk, ...]:
    """Physical whole disks from ``diskutil list -plist`` and each disk's ``diskutil info -plist``.

    Synthesized APFS containers are folded into the partition that stores them; virtual disks (disk images)
    are left out. A disk whose info is missing or unreadable keeps its listing values only.
    """
    entries = _entries(_plist(listing))
    apfs = _apfs_mounts(entries)
    disks = []
    for row in entries:
        name = _text(row.get("DeviceIdentifier"))
        if "APFSPhysicalStores" in row or not _MAC_WHOLE_DISK.fullmatch(name):
            continue
        try:
            info = _plist(infos[name]) if name in infos else {}
        except ValueError:
            info = {}
        if _text(info.get("VirtualOrPhysical")).casefold() == "virtual":
            continue
        disks.append(_mac_disk(row, info, apfs))
    return tuple(disks[:_DISK_LIMIT])


# Layout ---------------------------------------------------------------------------------------------------


def _placed(disk: PhysicalDisk) -> list[tuple[int, int, int]]:
    """(start, size, partition position) in bytes; packed in order when the offsets are not all known."""
    sized = [(position, part) for position, part in enumerate(disk.partitions) if part.size]
    if all(part.offset is not None for _position, part in sized):
        return sorted((part.offset or 0, part.size or 0, position) for position, part in sized)
    placed, start = [], 0
    for position, part in sized:
        placed.append((start, part.size or 0, position))
        start += part.size or 0
    return placed


def layout_segments(disk: PhysicalDisk) -> tuple[Segment, ...]:
    """Proportional bar segments for a disk's partitions, with unallocated gaps as ``partition=None``."""
    placed = _placed(disk)
    total = max(disk.size or 0, max((start + size for start, size, _position in placed), default=0))
    if total <= 0:
        return ()
    segments, cursor = [], 0
    for start, size, position in placed:
        if (start - cursor) / total >= 1 / _MILLI:  # alignment gaps are too thin to show
            segments.append(Segment(cursor / total, (start - cursor) / total, None))
        segments.append(Segment(start / total, size / total, position))
        cursor = max(cursor, start + size)
    if cursor < total and (total - cursor) / total >= 1 / _MILLI:
        segments.append(Segment(cursor / total, (total - cursor) / total, None))
    return tuple(segments)


# Providers ------------------------------------------------------------------------------------------------


def _run(command: Sequence[str], timeout: float, cancel: threading.Event | None) -> bytes | None:
    """Output of a fixed program; None when cancelled. Raises _QueryError on failure or timeout."""
    try:
        process = subprocess.Popen(  # noqa: S603 # nosec B603 - fixed absolute program, constant arguments
            list(command), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except OSError as error:
        raise _QueryError(PROBLEM_TOOL_MISSING, str(error)) from error
    deadline = time.monotonic() + timeout
    while True:
        try:
            output, errors = process.communicate(timeout=_POLL)
            break
        except subprocess.TimeoutExpired:
            stopped = cancel is not None and cancel.is_set()
            if stopped or time.monotonic() > deadline:
                process.kill()
                process.communicate()
                if stopped:
                    return None
                raise _QueryError(PROBLEM_TIMEOUT) from None
    if process.returncode:
        raise _QueryError(PROBLEM_FAILED, errors.decode("utf-8", "replace").strip())
    if len(output) > _OUTPUT_LIMIT:
        raise _QueryError(PROBLEM_MALFORMED, "Disk query output exceeds the review bound")
    return output


def _windows_powershell() -> str:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    buffer = ctypes.create_unicode_buffer(32768)
    length = kernel.GetSystemDirectoryW(buffer, len(buffer))
    if not 0 < length < len(buffer):
        raise _QueryError(PROBLEM_TOOL_MISSING, "Windows system directory unavailable")
    return os.path.join(buffer.value, "WindowsPowerShell", "v1.0", "powershell.exe")


def windows_command(program: str) -> list[str]:
    """The fixed Windows query: PowerShell without profile or prompts, running the constant script."""
    return [program, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", _WINDOWS_SCRIPT]


def _windows(cancel: threading.Event | None) -> tuple[PhysicalDisk, ...] | None:
    program = _windows_powershell()
    if not os.path.isfile(program):
        raise _QueryError(PROBLEM_TOOL_MISSING, program)
    output = _run(windows_command(program), _WINDOWS_TIMEOUT, cancel)
    return None if output is None else parse_windows(output.decode("utf-8-sig", "replace"))


def _linux(cancel: threading.Event | None) -> tuple[PhysicalDisk, ...] | None:
    program = next((path for path in _LSBLK if os.path.isfile(path)), None)
    if program is None:
        return sysfs_disks()
    try:
        output = _run([program, "--json", "--bytes", "--output-all"], _POSIX_TIMEOUT, cancel)
        if output is None:
            return None
        disks = parse_lsblk(output.decode("utf-8", "replace"))
    except (_QueryError, ValueError):
        return sysfs_disks()  # an old or broken lsblk: /sys/block still names the disks and partitions
    return tuple(replace(disk, temperature=sysfs_temperature(os.path.join("/sys/block", disk.identifier[5:])))
                 if disk.identifier.startswith("/dev/") else disk for disk in disks[:_DISK_LIMIT])


def _macos(cancel: threading.Event | None) -> tuple[PhysicalDisk, ...] | None:
    if not os.path.isfile(_DISKUTIL):
        raise _QueryError(PROBLEM_TOOL_MISSING, _DISKUTIL)
    listing = _run([_DISKUTIL, "list", "-plist"], _POSIX_TIMEOUT, cancel)
    if listing is None:
        return None
    infos: dict[str, bytes] = {}
    for name in whole_disk_ids(listing):
        try:
            info = _run([_DISKUTIL, "info", "-plist", name], _POSIX_TIMEOUT, cancel)
        except _QueryError:
            continue  # this disk keeps its listing values only
        if info is None:
            return None
        infos[name] = info
    return parse_macos(listing, infos)


def physical_disks(*, cancel: threading.Event | None = None) -> DiskSurvey | None:
    """Survey the machine's physical disks read-only; None when ``cancel`` is set during the query."""
    providers = {"win32": _windows, "linux": _linux, "darwin": _macos}
    provider = providers.get(sys.platform)
    if provider is None:
        return DiskSurvey((), PROBLEM_UNSUPPORTED, sys.platform)
    try:
        disks = provider(cancel)
    except _QueryError as error:
        return DiskSurvey((), error.problem, error.detail)
    except ValueError as error:
        return DiskSurvey((), PROBLEM_MALFORMED, str(error))
    return None if disks is None else DiskSurvey(disks)
