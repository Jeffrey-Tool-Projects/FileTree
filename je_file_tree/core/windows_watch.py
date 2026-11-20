"""Existing read-only USN journals, with one recursive overlapped notification handle as fallback."""

from collections.abc import Callable
import ctypes
import logging
import ntpath
import struct
import threading

from je_file_tree.core.change_watch import (
    POLL_SECONDS, ChangeBatch, Position, WatchFile, WatchFolder, changed, check_folder,
)
from je_file_tree.core.compression_ops import _kernel
from je_file_tree.core.pacing import give_way
from je_file_tree.core.windows_allocation import _FileID, _Identity
from je_file_tree.core.windows_trash import _volume

_BUFFER = 32768
# ReadDirectoryChangesW keeps changes for its handle in a buffer this size; when a burst fills it, all
# of them are lost and the whole root is read again. Over a network it refuses more than 64 KiB.
_NOTIFY_LOCAL, _NOTIFY_REMOTE = 262144, 65536
_DRIVE_REMOTE = 4
_MAX_LINKED = 64  # files whose other names changed, resolved per journal read; past it, read the whole root
_GONE = (2, 3, 87)  # not found, path not found, invalid parameter (a file number no longer in use)
_NOTIFY = struct.Struct("III")
_USN = struct.Struct("<IHHQQqqIIIIHH")
_JOURNAL = struct.Struct("<QqqqqQQ")
_READ = struct.Struct("<qIIQQQ")
_QUERY_USN, _READ_USN = 0x900F4, 0x900BB
_PENDING, _CANCELED, _ENUM_LOST = 997, 995, 1022
_TIMEOUT, _WAIT_MS = 258, 250
_MAJOR_V2 = 2
_CURSOR_BYTES = 8
_HARD_LINK_CHANGE = 0x10000
_ACTION_MODIFIED = 3
_RENAME_DELETE = 0x200 | 0x1000 | 0x2000
_LOG = logging.getLogger(__name__)


class _Overlapped(ctypes.Structure):
    _fields_ = [("internal", ctypes.c_size_t), ("internal_high", ctypes.c_size_t),
                ("offset", ctypes.c_uint32), ("offset_high", ctypes.c_uint32), ("event", ctypes.c_void_p)]


def _parent(root: str, name: str) -> str:
    if (not name or ntpath.isabs(name) or ntpath.splitdrive(name)[0] or "\0" in name
            or any(part in ("", ".", "..") for part in name.replace("/", "\\").split("\\"))):
        raise ValueError("Unsafe Windows notification name")
    return ntpath.dirname(ntpath.join(root, name))


def parse_notifications(payload: bytes, root: str, scopes: set[str]) -> ChangeBatch:
    """Validate native chained records; each names the folder inside ``root`` whose entries changed.

    That folder may be newer than the scan: the window reads the deepest folder it scanned there, which
    lists the new one and reads it whole. ``scopes`` tells a scanned folder's own change from a file's.
    """
    if not payload:
        return changed(set(), full=True, reason="notification_lost")
    if len(payload) > _NOTIFY_LOCAL:
        raise ValueError("Oversized Windows notification buffer")
    offset, paths = 0, set()
    while offset < len(payload):
        if len(payload) - offset < _NOTIFY.size:
            raise ValueError("Truncated Windows notification")
        next_offset, action, length = _NOTIFY.unpack_from(payload, offset)
        end = offset + _NOTIFY.size + length
        if action not in (1, 2, 3, 4, 5) or length % 2 or not length or end > len(payload):
            raise ValueError("Invalid Windows notification record")
        name = payload[offset + _NOTIFY.size:end].decode("utf-16-le")
        parent = _parent(root, name)
        named = ntpath.normpath(ntpath.join(root, name))
        paths.add(named if action == _ACTION_MODIFIED and named in scopes else parent)
        if not next_offset:
            return changed(paths)
        if next_offset % 4 or next_offset < _NOTIFY.size + length or offset + next_offset >= len(payload):
            raise ValueError("Invalid Windows notification offset")
        offset += next_offset
    raise ValueError("Unterminated Windows notification chain")


def _relinked(inode: int, parent: int, scopes: dict[int, str], shared: dict[int, tuple[str, ...]] | None,
              linked: set[int] | None) -> bool:
    """Note a file whose names changed; True when, unable to look its names up, the whole root is needed."""
    if shared is not None and inode in shared:
        return False  # its captured names' folders are read
    if linked is not None:
        linked.add(inode)  # its other names, in the scan or not, are looked up
        return False
    return parent not in scopes


def parse_usn(payload: bytes, scopes: dict[int, str], root: str, start: int,  # noqa: PLR0913
              shared: dict[int, tuple[str, ...]] | None = None, linked: set[int] | None = None
              ) -> tuple[int, ChangeBatch]:
    """Accept bounded V2 records/cursors; unknown volume parents are outside the captured map.

    A file that gained or lost a name outside the scan may still have one inside it. With ``linked``,
    such files are collected there for the caller to look up (``_linked_folders``); without it, the
    whole root is asked for.
    """
    if not _CURSOR_BYTES <= len(payload) <= _BUFFER:
        raise ValueError("Invalid USN reply size")
    next_usn, = struct.unpack_from("<q", payload)
    if next_usn < start:
        raise ValueError("USN cursor moved backwards")
    offset, paths = _CURSOR_BYTES, set()
    while offset < len(payload):
        if len(payload) - offset < _USN.size:
            raise ValueError("Truncated USN record")
        size, major, _minor, inode, parent, usn, _time, reason, _source, _security, attributes, length, name_at = (
            _USN.unpack_from(payload, offset))
        if (major != _MAJOR_V2 or size < _USN.size or size % 8 or offset + size > len(payload)
                or not start <= usn < next_usn or length % 2 or not length or name_at < _USN.size
                or name_at + length > size):
            raise ValueError("Unsupported or corrupt USN record")
        name = payload[offset + name_at:offset + name_at + length].decode("utf-16-le")
        if "\0" in name or "/" in name or "\\" in name or name in (".", ".."):
            raise ValueError("Invalid USN filename")
        if reason & _HARD_LINK_CHANGE and _relinked(inode, parent, scopes, shared, linked):
            return next_usn, changed(set(), full=True, reason="hard_links_changed")
        known_folder = inode in scopes and attributes & 0x10
        if parent in scopes and (not known_folder or reason & _RENAME_DELETE):
            paths.add(scopes[parent])
        if shared is not None and inode in shared:
            paths.update(shared[inode])
        if known_folder:
            path = scopes[inode]
            if path == root and reason & _RENAME_DELETE:
                return next_usn, changed(set(), full=True, reason="root_changed")
            paths.add(ntpath.dirname(path) if reason & _RENAME_DELETE else path)
        offset += size
    return next_usn, changed(paths)


class _FileIdDescriptor(ctypes.Structure):
    _fields_ = [("size", ctypes.c_uint32), ("kind", ctypes.c_int), ("file_id", ctypes.c_uint64),
                ("high", ctypes.c_uint64)]


def _apis():
    kernel = _kernel()
    kernel.OpenFileById.argtypes = [ctypes.c_void_p, ctypes.POINTER(_FileIdDescriptor), ctypes.c_uint32,
                                    ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32]
    kernel.OpenFileById.restype = ctypes.c_void_p
    kernel.GetFinalPathNameByHandleW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32]
    kernel.GetFinalPathNameByHandleW.restype = ctypes.c_uint32
    kernel.FindFirstFileNameW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32),
                                          ctypes.c_wchar_p]
    kernel.FindFirstFileNameW.restype = ctypes.c_void_p
    kernel.FindNextFileNameW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_wchar_p]
    kernel.FindNextFileNameW.restype = ctypes.c_int
    kernel.FindClose.argtypes = [ctypes.c_void_p]
    kernel.GetDriveTypeW.argtypes = [ctypes.c_wchar_p]
    kernel.GetDriveTypeW.restype = ctypes.c_uint32
    kernel.DeviceIoControl.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32,
                                       ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p]
    kernel.DeviceIoControl.restype = ctypes.c_int
    kernel.GetFileInformationByHandle.argtypes = [ctypes.c_void_p, ctypes.POINTER(_Identity)]
    kernel.GetFileInformationByHandleEx.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    kernel.CreateEventW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p]
    kernel.CreateEventW.restype = ctypes.c_void_p
    kernel.ReadDirectoryChangesW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32,
                                            ctypes.c_int, ctypes.c_uint32, ctypes.c_void_p,
                                            ctypes.POINTER(_Overlapped), ctypes.c_void_p]
    kernel.ReadDirectoryChangesW.restype = ctypes.c_int
    kernel.GetOverlappedResult.argtypes = [ctypes.c_void_p, ctypes.POINTER(_Overlapped), ctypes.c_void_p, ctypes.c_int]
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel.WaitForSingleObject.restype = ctypes.c_uint32
    kernel.CancelIoEx.argtypes = [ctypes.c_void_p, ctypes.POINTER(_Overlapped)]
    kernel.ResetEvent.argtypes = [ctypes.c_void_p]
    return kernel


def _control(kernel, handle, code: int, data: bytes = b"") -> bytes:
    output, length = ctypes.create_string_buffer(_BUFFER), ctypes.c_uint32()
    request = ctypes.create_string_buffer(data) if data else None
    if not kernel.DeviceIoControl(handle, code, request, len(data), output, len(output), ctypes.byref(length), None):
        raise ctypes.WinError(ctypes.get_last_error())
    return output.raw[:length.value]


def _journal(kernel, handle) -> tuple[int, int, int]:
    data = _control(kernel, handle, _QUERY_USN)
    if len(data) < _JOURNAL.size:
        raise ValueError("Incomplete USN journal metadata")
    identifier, first, next_usn, lowest, _max, _capacity, _delta = _JOURNAL.unpack_from(data)
    if not identifier or min(first, next_usn, lowest) < 0 or next_usn < max(first, lowest):
        raise ValueError("Invalid USN journal metadata")
    return identifier, max(first, lowest), next_usn


def _start(journal: int, first: int, next_usn: int, since: Position | None) -> int | None:
    """Where to read from: on from ``since`` while the same journal still holds it, else None."""
    if since is None:
        return next_usn
    if since[0] == journal and first <= since[1] <= next_usn:
        return since[1]
    return None


def _names_of(kernel, volume, number: int) -> list[str]:
    """Every name of file ``number`` on ``volume``, relative to the volume's root (metadata only)."""
    descriptor = _FileIdDescriptor(ctypes.sizeof(_FileIdDescriptor), 0, number, 0)
    handle = kernel.OpenFileById(volume, ctypes.byref(descriptor), 0x80, 7, None, 0x02200000)
    if handle in (None, ctypes.c_void_p(-1).value):
        raise ctypes.WinError(ctypes.get_last_error())
    text = ctypes.create_unicode_buffer(32768)
    try:
        length = kernel.GetFinalPathNameByHandleW(handle, text, len(text), 0)
        if not length or length >= len(text):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel.CloseHandle(handle)
    names, size = [], ctypes.c_uint32(len(text))
    found = kernel.FindFirstFileNameW(text.value, 0, ctypes.byref(size), text)
    if found in (None, ctypes.c_void_p(-1).value):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        names.append(text.value)
        while True:
            size = ctypes.c_uint32(len(text))
            if not kernel.FindNextFileNameW(found, ctypes.byref(size), text):
                break
            names.append(text.value)
    finally:
        kernel.FindClose(found)
    return names


def _linked_folders(kernel, volume, numbers: set[int], drive: str, root: str) -> set[str] | None:
    """The folders inside ``root`` holding a name of each file in ``numbers``; None when one cannot be told.

    A hard link made or removed anywhere on the volume used to read the whole scan again (Windows
    servicing makes many); now only a file with a name inside the scan reads that name's folder.
    """
    if len(numbers) > _MAX_LINKED:
        return None
    base = ntpath.normcase(root.rstrip("\\"))
    found = set()
    for number in numbers:
        try:
            names = _names_of(kernel, volume, number)
        except OSError as error:
            if getattr(error, "winerror", None) in _GONE:
                continue  # no name left: those in the scan went with records of their own folders
            return None
        for name in names:
            path = ntpath.join(drive, name.lstrip("\\"))
            folder = ntpath.normcase(path)
            if folder.startswith(base + "\\"):
                found.add(ntpath.dirname(path))
    return found


def _with_linked(kernel, volume, batch: ChangeBatch, linked: set[int], drive: str, root: str  # noqa: PLR0913
                 ) -> ChangeBatch:
    """``batch`` with the folders holding a name of each file in ``linked`` (all of the root if unknown)."""
    if not linked or batch.full:
        return batch
    elsewhere = _linked_folders(kernel, volume, linked, drive, root)
    if elsewhere is None:
        return changed(set(), full=True, reason="hard_links_changed")
    return changed(set(batch.folders) | elsewhere, trees=set(batch.trees))


def _watch_usn(kernel, folders, on_change, cancel, ready, shared, *, since=None, moved=None) -> None:  # noqa: PLR0913
    moved = moved or (lambda _position: None)
    root, identifier = _volume(folders[0].path)
    scopes = {folder.inode: folder.path for folder in folders}
    aliases = {file.inode: file.parents for file in shared}
    if any(item.inode >= 1 << 64 for group in (folders, shared) for item in group):
        raise ValueError("USN V2 folder IDs unavailable")
    handle = kernel.CreateFileW("\\\\?\\Volume" + identifier, 0x80000000, 7, None, 3, 0, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        journal, first, cursor = _journal(kernel, handle)
        cursor = _start(journal, first, cursor, since)
        if cursor is None:
            on_change(changed(set(), full=True, reason="journal_changed"))
            return
        if ready:
            ready("usn")
        while not cancel.is_set():
            check_folder(folders[0])
            if _volume(folders[0].path) != (root, identifier):
                raise ValueError("Watched NTFS volume changed")
            current, first, next_usn = _journal(kernel, handle)
            if current != journal or not first <= cursor <= next_usn:
                on_change(changed(set(), full=True, reason="journal_changed"))
                return
            payload = _control(kernel, handle, _READ_USN, _READ.pack(cursor, 0xFFFFFFFF, 0, 0, 0, journal))
            started, linked = cursor, set()
            cursor, batch = parse_usn(payload, scopes, folders[0].path, cursor, aliases, linked)
            batch = _with_linked(kernel, handle, batch, linked, root, folders[0].path)
            moved((journal, cursor))
            if (batch.folders or batch.trees or batch.full) and not cancel.is_set():
                on_change(batch)
            if batch.full:
                return
            if started < cursor < next_usn:
                give_way()  # more records wait: read on now, so a busy volume never leaves the feed behind
                continue
            if cancel.wait(POLL_SECONDS):
                return
    finally:
        kernel.CloseHandle(handle)


def _checked_handle(kernel, folder: WatchFolder):
    check_folder(folder)
    handle = kernel.CreateFileW(folder.path, 1, 7, None, 3, 0x42200000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        identity, file_id = _Identity(), _FileID()
        if (not kernel.GetFileInformationByHandle(handle, ctypes.byref(identity))
                or not kernel.GetFileInformationByHandleEx(handle, 18, ctypes.byref(file_id), ctypes.sizeof(file_id))):
            raise ctypes.WinError(ctypes.get_last_error())
        legacy = (identity.device, (identity.inode_high << 32) | identity.inode_low)
        extended = (file_id.device, int.from_bytes(file_id.inode, "little"))
        if (not identity.attributes & 0x10 or identity.attributes & 0x400
                or (folder.device, folder.inode) not in (legacy, extended)):
            raise ValueError("Notification handle differs from captured ordinary folder")
        check_folder(folder)
        return handle
    except (OSError, ValueError):
        kernel.CloseHandle(handle)
        raise


def _completion(kernel, handle, overlap: _Overlapped, cancel: threading.Event) -> int:
    length = ctypes.c_uint32()
    while not cancel.is_set():
        state = kernel.WaitForSingleObject(overlap.event, _WAIT_MS)
        if state == _TIMEOUT:
            continue
        if state != 0:
            raise ctypes.WinError(ctypes.get_last_error())
        if not kernel.GetOverlappedResult(handle, ctypes.byref(overlap), ctypes.byref(length), False):
            raise ctypes.WinError(ctypes.get_last_error())
        return length.value
    return 0


def _notify_size(kernel, path: str) -> int:
    """The largest notification buffer ReadDirectoryChangesW takes for ``path``."""
    if path.startswith("\\\\"):
        return _NOTIFY_REMOTE
    drive = ntpath.splitdrive(path)[0] + "\\"
    return _NOTIFY_REMOTE if kernel.GetDriveTypeW(drive) == _DRIVE_REMOTE else _NOTIFY_LOCAL


def _notification(kernel, handle, overlap: _Overlapped, cancel: threading.Event,  # noqa: PLR0913
                  armed: Callable[[], None] | None = None, size: int = _NOTIFY_LOCAL) -> bytes:
    buffer = ctypes.create_string_buffer(size)
    kernel.ResetEvent(overlap.event)
    if (not kernel.ReadDirectoryChangesW(handle, buffer, len(buffer), True, 0x15F, None, ctypes.byref(overlap), None)
            and ctypes.get_last_error() != _PENDING):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if armed:
            armed()
        length = _completion(kernel, handle, overlap, cancel)
        return buffer.raw[:length]
    finally:
        # Buffer/OVERLAPPED storage must remain alive until kernel I/O has actually completed.
        kernel.CancelIoEx(handle, ctypes.byref(overlap))
        remaining = ctypes.c_uint32()
        if not kernel.GetOverlappedResult(handle, ctypes.byref(overlap), ctypes.byref(remaining), True):
            error = ctypes.get_last_error()
            if error not in (_CANCELED, _ENUM_LOST):
                raise ctypes.WinError(error)


def _watch_notifications(kernel, folders, on_change, cancel, ready) -> None:
    handle = _checked_handle(kernel, folders[0])
    event = kernel.CreateEventW(None, True, False, None)
    if not event:
        kernel.CloseHandle(handle)
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        overlap = _Overlapped(event=event)
        scopes = {folder.path for folder in folders}
        size = _notify_size(kernel, folders[0].path)
        first = True
        while not cancel.is_set():
            check_folder(folders[0])
            try:
                armed = (lambda: ready("directory_changes")) if first and ready else None
                payload = _notification(kernel, handle, overlap, cancel, armed, size)
                first = False
                batch = parse_notifications(payload, folders[0].path, scopes)
            except OSError as error:
                if error.winerror != _ENUM_LOST:
                    raise
                batch = changed(set(), full=True, reason="notification_lost")
            if not cancel.is_set():
                on_change(batch)
            if batch.full:
                return
    finally:
        kernel.CloseHandle(event)
        kernel.CloseHandle(handle)


def watch_windows(folders: tuple[WatchFolder, ...], on_change: Callable[[ChangeBatch], None],  # noqa: PLR0913
                  cancel: threading.Event, ready: Callable[[str], None] | None,
                  shared: tuple[WatchFile, ...] = (), *, since: Position | None = None,
                  moved: Callable[[Position], None] | None = None) -> None:
    """Use an existing journal when accessible; fallback is native, recursive, read-only and cancelable."""
    kernel = _apis()
    announced = False

    def initialized(backend: str) -> None:
        nonlocal announced
        announced = True
        if ready:
            ready(backend)

    try:
        _watch_usn(kernel, folders, on_change, cancel, initialized, shared, since=since, moved=moved)
    except (OSError, ValueError, UnicodeError) as error:
        _LOG.debug("USN feed unavailable; using recursive notifications: %s", error)
        if not cancel.is_set():
            if announced:
                on_change(changed(set(), full=True, reason="backend_changed"))
            if shared and _volume(folders[0].path)[0] != folders[0].path:
                raise ValueError("External hard-link changes require an accessible USN journal") from error
            _watch_notifications(kernel, folders, on_change, cancel, ready)
