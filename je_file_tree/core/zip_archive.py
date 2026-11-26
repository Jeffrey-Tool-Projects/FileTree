"""Pack a scanned folder into a new ZIP file and read every byte back before the file appears under its name.

The folder must be exactly as scanned, before and after packing: unchanged, complete, without links, files kept
only online, special files or named data streams (a ZIP would lose them). The archive is written to a temporary
sibling, each member is read back and compared by SHA-256 with what was read from its file, and only then is it
published, never over an existing file. A ZIP keeps names, contents and modification times to two seconds; it
does not keep owners, permissions or extended attributes. Nothing here moves or removes the folder.
"""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import threading
import time
import zipfile
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field

from je_file_tree.core.archives import opened
from je_file_tree.core.copy_platform import windows_streams
from je_file_tree.core.no_replace import anchored_directory, directory_stamps, rename_no_replace
from je_file_tree.core.node import Node
from je_file_tree.core.operations import revalidate
from je_file_tree.core.pacing import give_way
from je_file_tree.core.protected import protected_places, protection_of
from je_file_tree.core.snapshot import stable_snapshot, stat_snapshot
from je_file_tree.core.verified_copy import _readable

_CHUNK = 1 << 20
_FIRST_YEAR, _LAST_YEAR = 1980, 2107
_LARGE = 1 << 31
_DATA_STREAM = "::$DATA"
_FOLDER_ATTRIBUTES = 0o40755 << 16 | 0x10  # without a mode, unzip on POSIX makes folders nobody can open

Progress = Callable[[str, int, int], None]


class ArchiveRefusedError(Exception):
    """The folder or target cannot be archived; ``reason`` is a key the window explains."""

    def __init__(self, reason: str, path: str = "") -> None:
        super().__init__(reason)
        self.reason, self.path = reason, path


class ArchiveStoppedError(Exception):
    """Stopped on request; nothing was published."""


@dataclass(frozen=True, slots=True)
class ArchivePlan:
    """What will be packed, in order, with the name each entry gets."""

    root: Node
    node: Node
    target: str
    entries: tuple[tuple[Node, str], ...]
    files: int
    bytes: int


@dataclass(frozen=True, slots=True)
class ArchiveProof:
    """A published archive whose every member was read back; check it again before acting on it."""

    plan: ArchivePlan
    size: int
    snapshot: bytes = field(repr=False)

    def unchanged(self) -> bool:
        """Whether the archive is still the file that was verified."""
        try:
            return stable_snapshot(stat_snapshot(self.plan.target)) == self.snapshot
        except OSError:
            return False


def _stop(cancel: threading.Event | None) -> None:
    if cancel is not None and cancel.is_set():
        raise ArchiveStoppedError


def plan_archive(root: Node, node: Node, target: str, cancel: threading.Event | None = None) -> ArchivePlan:
    """Check the folder and the target and list what to pack; raises ``ArchiveRefusedError``."""
    target = os.path.abspath(target)
    _check_target(node, target)
    reason = _refusal(root, node, cancel)
    _stop(cancel)
    if reason:
        raise ArchiveRefusedError(reason, node.path or "")
    entries: list[tuple[Node, str]] = []
    files = size = 0
    stack = [(node, node.name)]
    while stack:
        _stop(cancel)
        give_way()
        entry, name = stack.pop()
        _check_name(entry)
        entries.append((entry, name + "/" if entry.is_dir else name))
        if entry.is_dir:
            stack.extend((child, f"{name}/{child.name}") for child in reversed(entry.children))
            continue
        _check_streams(entry)
        files += 1
        size += entry.size
    return ArchivePlan(root, node, target, tuple(entries), files, size)


def _refusal(root: Node, node: Node, cancel: threading.Event | None) -> str:
    try:
        return _readable(root, node, tuple(protected_places()), cancel)
    except InterruptedError as stopped:
        raise ArchiveStoppedError from stopped
    except (OSError, ValueError):
        if cancel is not None and cancel.is_set():
            raise ArchiveStoppedError from None
        return "changed"


def _check_target(node: Node, target: str) -> None:
    folder = os.path.dirname(target)
    source = os.path.normcase(os.path.normpath(node.path or ""))
    inside = os.path.normcase(os.path.normpath(folder))
    if not target.lower().endswith(".zip") or not os.path.isdir(folder):
        raise ArchiveRefusedError("target", target)
    if os.path.lexists(target):
        raise ArchiveRefusedError("exists", target)
    if inside == source or inside.startswith(source.rstrip(os.sep) + os.sep):
        raise ArchiveRefusedError("inside", target)


def _check_name(entry: Node) -> None:
    """A ZIP separates folders with ``/`` and stores UTF-8: other names could come back as something else."""
    try:
        entry.name.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ArchiveRefusedError("name", entry.path or "") from error
    if "\\" in entry.name or "/" in entry.name or "\0" in entry.name or entry.name in (".", ".."):
        raise ArchiveRefusedError("name", entry.path or "")


def _check_streams(entry: Node) -> None:
    if sys.platform == "win32" and any(name != _DATA_STREAM for name, _size in windows_streams(entry.path or "")):
        raise ArchiveRefusedError("streams", entry.path or "")


def create_archive(plan: ArchivePlan, progress: Progress | None = None,
                   cancel: threading.Event | None = None) -> ArchiveProof:
    """Write, read back and publish the archive; on any failure or stop nothing is left under its name."""
    folder = os.path.dirname(plan.target)
    stamps = directory_stamps(folder)
    handle, temporary = tempfile.mkstemp(prefix=".file-tree-", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(handle, "w+b") as stream:
            digests = _write(plan, stream, progress, cancel)
            stream.flush()
            os.fsync(stream.fileno())
            stream.seek(0)
            _read_back(plan, stream, digests, progress, cancel)
        _stop(cancel)
        reason = revalidate(plan.node, plan.root, places=tuple(protected_places()),
                            approved=protection_of(plan.node.path or "", tuple(protected_places())), cancel=cancel)
        _stop(cancel)
        if reason:
            raise ArchiveRefusedError("changed", plan.node.path or "")
        with anchored_directory(stamps) as descriptor:
            rename_no_replace(temporary, plan.target, descriptor, descriptor)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(temporary)
        raise
    snapshot = stat_snapshot(plan.target)
    return ArchiveProof(plan, os.path.getsize(plan.target), stable_snapshot(snapshot))


def _write(plan: ArchivePlan, stream, progress: Progress | None, cancel: threading.Event | None) -> dict[str, bytes]:
    digests: dict[str, bytes] = {}
    done = 0
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        for entry, name in plan.entries:
            _stop(cancel)
            give_way()
            info = zipfile.ZipInfo(name, _date(entry.modified))
            if entry.is_dir:
                info.external_attr = _FOLDER_ATTRIBUTES
                archive.writestr(info, b"")
                continue
            info.compress_type = zipfile.ZIP_DEFLATED
            info.file_size = entry.size
            done = _pack(archive, info, entry, digests, (done, plan.bytes, progress), cancel)
    return digests


def _pack(archive: zipfile.ZipFile, info: zipfile.ZipInfo, entry: Node, digests: dict[str, bytes],
          state: tuple[int, int, Progress | None], cancel: threading.Event | None) -> int:
    done, total, progress = state
    digest = hashlib.sha256()
    with opened(entry) as source, archive.open(info, "w", force_zip64=entry.size >= _LARGE) as member:
        while block := source.read(_CHUNK):
            _stop(cancel)
            digest.update(block)
            member.write(block)
            done += len(block)
            if progress is not None:
                progress("pack", done, total)
    digests[info.filename] = digest.digest()
    return done


def _read_back(plan: ArchivePlan, stream, digests: dict[str, bytes], progress: Progress | None,
               cancel: threading.Event | None) -> None:
    done = 0
    try:
        with zipfile.ZipFile(stream) as archive:
            if [info.filename for info in archive.infolist()] != [name for _entry, name in plan.entries]:
                raise ArchiveRefusedError("verify", plan.target)
            for entry, name in plan.entries:
                if entry.is_dir:
                    continue
                digest = hashlib.sha256()
                with archive.open(name) as member:
                    while block := member.read(_CHUNK):
                        _stop(cancel)
                        digest.update(block)
                        done += len(block)
                        if progress is not None:
                            progress("verify", done, plan.bytes)
                if digest.digest() != digests[name]:
                    raise ArchiveRefusedError("verify", entry.path or "")
    except zipfile.BadZipFile as error:
        raise ArchiveRefusedError("verify", plan.target) from error


def _date(modified: float) -> tuple[int, int, int, int, int, int]:
    try:
        moment = time.localtime(modified)
    except (OverflowError, OSError, ValueError):
        return _FIRST_YEAR, 1, 1, 0, 0, 0
    if moment.tm_year < _FIRST_YEAR:
        return _FIRST_YEAR, 1, 1, 0, 0, 0
    if moment.tm_year > _LAST_YEAR:
        return _LAST_YEAR, 12, 31, 23, 59, 58
    return moment.tm_year, moment.tm_mon, moment.tm_mday, moment.tm_hour, moment.tm_min, moment.tm_sec
