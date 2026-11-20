"""One FSEvents stream over the scanned folder, reporting the folders whose entries changed and every loss.

FSEvents reports directories, not files: each path is a folder whose own entries changed, which is
what the window reads again. The stream says when it could not keep up (``MustScanSubDirs``: that
folder is read whole), when events were dropped or their numbers wrapped (the whole root is read),
and when the scanned folder itself was moved or a volume was mounted or unmounted inside it.
Read-only: no file is opened and nothing is changed. Called through ``change_watch.watch_scope``.
"""

from collections.abc import Callable
import ctypes
import ctypes.util
import os
import posixpath
import threading

from je_file_tree.core.change_watch import ChangeBatch, POLL_SECONDS, WatchFile, WatchFolder, changed, check_folder

_MUST_SCAN_SUBDIRS = 0x1
_LOST = 0x2 | 0x4 | 0x8  # user dropped, kernel dropped, event numbers wrapped
_SCOPE = 0x20 | 0x40 | 0x80  # root changed, mount, unmount
_NO_DEFER, _WATCH_ROOT = 0x2, 0x4
_SINCE_NOW = 0xFFFFFFFFFFFFFFFF
_UTF8 = 0x08000100
_LATENCY = 0.2  # s FSEvents gathers events for; the window coalesces them further
_DATA_VOLUME = "/System/Volumes/Data"  # where FSEvents may report the paths of the data volume

_Callback = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                             ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_uint32),
                             ctypes.POINTER(ctypes.c_uint64))


def spellings(root: str) -> tuple[str, ...]:
    """The forms FSEvents may report ``root`` in: as scanned, resolved, and on the data volume."""
    real = os.path.realpath(root)
    forms = [root, real]
    if not real.startswith(_DATA_VOLUME + "/"):
        forms.append(_DATA_VOLUME + real)
    return tuple(dict.fromkeys(form.rstrip("/") or "/" for form in forms))


def _inside(path: str, root: str, forms: tuple[str, ...]) -> str | None:
    path = path.rstrip("/") or "/"
    for form in forms:
        if path == form:
            return root
        base = "" if form == "/" else form
        if path.startswith(base + "/"):
            return posixpath.join(root, path[len(base) + 1:])
    return None


def parse_fsevents(paths: list[str], flags: list[int], root: str, forms: tuple[str, ...]) -> ChangeBatch:
    """Map one delivery of directory events to folders inside ``root``; a loss asks for all of it."""
    folders, trees = set(), set()
    for path, flag in zip(paths, flags, strict=True):
        if flag & _LOST:
            return changed(set(), full=True, reason="notification_lost")
        inside = _inside(path, root, forms)
        if flag & _SCOPE and (inside is not None or flag & 0x20):
            return changed(set(), full=True, reason="scope_changed")
        if inside is not None:
            (trees if flag & _MUST_SCAN_SUBDIRS else folders).add(inside)
    return changed(folders, trees=trees)


def _libraries():
    core = ctypes.CDLL(ctypes.util.find_library("CoreFoundation"))
    services = ctypes.CDLL(ctypes.util.find_library("CoreServices"))
    core.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
    core.CFStringCreateWithCString.restype = ctypes.c_void_p
    core.CFArrayCreate.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_long, ctypes.c_void_p]
    core.CFArrayCreate.restype = ctypes.c_void_p
    core.CFRelease.argtypes = [ctypes.c_void_p]
    core.CFRunLoopGetCurrent.restype = ctypes.c_void_p
    core.CFRunLoopRunInMode.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_bool]
    core.CFRunLoopRunInMode.restype = ctypes.c_int32
    services.FSEventStreamCreate.argtypes = [ctypes.c_void_p, _Callback, ctypes.c_void_p, ctypes.c_void_p,
                                             ctypes.c_uint64, ctypes.c_double, ctypes.c_uint32]
    services.FSEventStreamCreate.restype = ctypes.c_void_p
    for name in ("FSEventStreamScheduleWithRunLoop",):
        getattr(services, name).argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    for name in ("FSEventStreamStop", "FSEventStreamInvalidate", "FSEventStreamRelease"):
        getattr(services, name).argtypes = [ctypes.c_void_p]
    services.FSEventStreamStart.argtypes = [ctypes.c_void_p]
    services.FSEventStreamStart.restype = ctypes.c_bool
    return core, services


def watch_mac(folders: tuple[WatchFolder, ...], on_change: Callable[[ChangeBatch], None],
              cancel: threading.Event, ready: Callable[[str], None] | None,
              shared: tuple[WatchFile, ...] = ()) -> None:
    """Run one stream on this thread's run loop until ``cancel``; native failures raise visibly."""
    root = folders[0].path
    if shared and not os.path.ismount(root):
        raise ValueError("External hard-link changes are not reported on macOS; scan the whole volume")
    core, services = _libraries()
    forms = spellings(root)
    failures: list[BaseException] = []

    def delivered(_stream, _info, count, paths, flags, _numbers) -> None:
        try:
            names = [os.fsdecode(paths[index]) for index in range(count)]
            batch = parse_fsevents(names, [flags[index] for index in range(count)], root, forms)
            if (batch.folders or batch.trees or batch.full) and not cancel.is_set():
                on_change(batch)
        except (ValueError, UnicodeError) as error:  # handed to this thread's loop, which raises it
            failures.append(error)

    callback = _Callback(delivered)  # kept alive for as long as the stream may call it
    text = core.CFStringCreateWithCString(None, os.fsencode(root), _UTF8)
    if not text:
        raise OSError("FSEvents could not name the scanned folder")
    array = core.CFArrayCreate(None, (ctypes.c_void_p * 1)(text), 1,
                               ctypes.addressof(ctypes.c_void_p.in_dll(core, "kCFTypeArrayCallBacks")))
    stream = services.FSEventStreamCreate(None, callback, None, array, _SINCE_NOW, _LATENCY, _NO_DEFER | _WATCH_ROOT)
    if not stream:
        core.CFRelease(array)
        core.CFRelease(text)
        raise OSError("FSEvents stream unavailable")
    mode = ctypes.c_void_p.in_dll(core, "kCFRunLoopDefaultMode").value
    try:
        services.FSEventStreamScheduleWithRunLoop(stream, core.CFRunLoopGetCurrent(), mode)
        if not services.FSEventStreamStart(stream):
            raise OSError("FSEvents stream did not start")
        if ready:
            ready("fsevents")
        try:
            while not cancel.is_set() and not failures:
                check_folder(folders[0])
                core.CFRunLoopRunInMode(mode, POLL_SECONDS, False)
        finally:
            services.FSEventStreamStop(stream)
        if failures:
            raise failures[0]
    finally:
        services.FSEventStreamInvalidate(stream)
        services.FSEventStreamRelease(stream)
        core.CFRelease(array)
        core.CFRelease(text)
