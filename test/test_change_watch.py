"""Native metadata feeds never authorize operations; malformed/lost events require fresh scopes."""

import os
from pathlib import Path
import struct
import sys
import threading
from types import SimpleNamespace

import pytest

from je_file_tree.core import change_watch as change
from je_file_tree.core import linux_watch, mac_watch, windows_watch
from je_file_tree.core.scanner import scan


def _notify(name="資料\\file.bin", action=3, next_offset=0):
    encoded = name.encode("utf-16-le")
    return struct.pack("<III", next_offset, action, len(encoded)) + encoded


def _usn(*, inode=55, parent=22, reason=1, major=2, usn=100, name="資料.bin", directory=False):
    encoded = name.encode("utf-16-le")
    size = -(-(60 + len(encoded)) // 8) * 8
    row = windows_watch._USN.pack(size, major, 0, inode, parent, usn, 0, reason, 0, 0,
                                  0x10 if directory else 0, len(encoded), 60)
    return struct.pack("<q", usn + size) + row + encoded + bytes(size - 60 - len(encoded))


def test_captured_scope_is_physical_complete_and_retains_shared_parent_identity(tmp_path):
    source = tmp_path / "owned"
    source.mkdir()
    (source / "branch").mkdir()
    (source / "branch" / "file").write_bytes(b"kept")
    os.link(source / "branch" / "file", source / "alias")
    root = scan(source).root
    scope = change.captured_scope(root, threading.Event())
    assert scope.folders[0].path == str(source) and len(scope.folders) == 2
    assert len(scope.shared) == 1 and set(scope.shared[0].parents) == {str(source), str(source / "branch")}
    assert scope.shared[0].inode == (source / "alias").stat().st_ino
    root.error = "owned incomplete branch"
    with pytest.raises(ValueError, match="complete scan"):
        change.captured_scope(root, threading.Event())


def test_changed_folder_and_cancellation_never_start_native_feed(tmp_path, monkeypatch):
    root = scan(tmp_path).root
    scope = change.captured_scope(root, threading.Event())
    monkeypatch.setattr(change, "stat_snapshot", lambda _path: (_ for _ in ()).throw(FileNotFoundError("moved")))
    with pytest.raises(FileNotFoundError):
        change.check_folder(scope.folders[0])
    cancel = threading.Event()
    cancel.set()
    assert not change.captured_scope(root, cancel).folders


def test_inaccessible_file_and_virtual_root_cannot_enable_monitoring(tmp_path):
    (tmp_path / "file").write_bytes(b"kept")
    root = scan(tmp_path).root
    root.children[0].error = "unreadable payload metadata"
    with pytest.raises(ValueError, match="complete scan"):
        change.captured_scope(root, threading.Event())
    root.name = ""
    with pytest.raises(ValueError, match="physical folder"):
        change.captured_scope(root, threading.Event())


def test_usn_gap_requests_full_scan_closes_handle_and_only_queries_existing_journal(monkeypatch):
    calls, batches, backends = [], [], []
    folder = change.WatchFolder("C:\\owned", 7, 22)
    kernel = SimpleNamespace(CreateFileW=lambda *_args: 42, CloseHandle=calls.append)
    replies = iter((windows_watch._JOURNAL.pack(9, 0, 100, 0, 0, 4096, 1024),
                    windows_watch._JOURNAL.pack(9, 101, 110, 101, 0, 4096, 1024)))

    def control(_kernel, _handle, code, _data=b""):
        calls.append(code)
        return next(replies)

    monkeypatch.setattr(windows_watch, "_control", control)
    monkeypatch.setattr(windows_watch, "_volume", lambda _path: ("C:\\", "{owned}"))
    monkeypatch.setattr(windows_watch, "check_folder", lambda _folder: None)
    windows_watch._watch_usn(kernel, (folder,), batches.append, threading.Event(), backends.append, ())
    assert backends == ["usn"] and batches == [change.ChangeBatch(full=True, reason="journal_changed")]
    assert calls == [windows_watch._QUERY_USN, windows_watch._QUERY_USN, 42]


def test_initial_usn_denial_falls_back_without_triggering_repeated_full_rescans(monkeypatch):
    batches, backends = [], []

    def denied(*_args, **_kwargs):
        raise PermissionError("owned denied journal")

    def fallback(_kernel, _folders, _changed, _cancel, ready):
        ready("directory_changes")

    monkeypatch.setattr(windows_watch, "_apis", object)
    monkeypatch.setattr(windows_watch, "_watch_usn", denied)
    monkeypatch.setattr(windows_watch, "_watch_notifications", fallback)
    folders = (change.WatchFolder("C:\\owned", 7, 22),)
    windows_watch.watch_windows(folders, batches.append, threading.Event(), backends.append)
    assert not batches and backends == ["directory_changes"]
    monkeypatch.setattr(windows_watch, "_volume", lambda _path: ("C:\\", "{owned}"))
    shared = (change.WatchFile("C:\\owned\\file", 7, 55, ("C:\\owned",)),)
    with pytest.raises(ValueError, match="External hard-link"):
        windows_watch.watch_windows(folders, batches.append, threading.Event(), backends.append, shared)
    assert not batches and backends == ["directory_changes"]


def test_windows_notifications_name_the_folder_whose_entries_changed_even_when_it_is_new():
    root = "C:\\owned"
    scopes = {root, root + "\\資料"}
    assert windows_watch.parse_notifications(_notify(), root, scopes).folders == (root + "\\資料",)
    # The window reads the deepest folder it scanned there, whose listing reads the new ones whole.
    assert windows_watch.parse_notifications(_notify("new\\deep\\file"), root, scopes).folders == (
        root + "\\new\\deep",)
    assert windows_watch.parse_notifications(b"", root, scopes).full


def test_usn_feed_reads_on_from_a_handed_over_position_or_asks_for_the_whole_root(monkeypatch):
    folder = change.WatchFolder("C:\\owned", 7, 22)
    kernel = SimpleNamespace(CreateFileW=lambda *_args: 42, CloseHandle=lambda _handle: None)
    reads, batches, positions = [], [], []
    cancel = threading.Event()

    def control(_kernel, _handle, code, data=b""):
        if code == windows_watch._QUERY_USN:
            return windows_watch._JOURNAL.pack(9, 50, 300, 50, 0, 4096, 1024)
        reads.append(windows_watch._READ.unpack(data)[0])
        cancel.set()
        return struct.pack("<q", reads[-1])

    monkeypatch.setattr(windows_watch, "_control", control)
    monkeypatch.setattr(windows_watch, "_volume", lambda _path: ("C:\\", "{owned}"))
    monkeypatch.setattr(windows_watch, "check_folder", lambda _folder: None)
    windows_watch._watch_usn(kernel, (folder,), batches.append, cancel, None, (), since=(9, 120),
                             moved=positions.append)
    assert reads == [120] and positions == [(9, 120)] and not batches  # not from 300: nothing is skipped
    for gone in ((9, 10), (8, 120)):  # overwritten, or another journal: what happened since is unknown
        cancel.clear()
        windows_watch._watch_usn(kernel, (folder,), batches.append, cancel, None, (), since=gone)
    assert batches == [change.ChangeBatch(full=True, reason="journal_changed")] * 2 and reads == [120]


def test_too_many_changed_folders_become_their_parent_folders_read_whole(tmp_path):
    many = {str(tmp_path / f"d{number}" / "inner") for number in range(change.MAX_CHANGED + 1)}
    batch = change.changed(many)
    assert not batch.full and not batch.folders and batch.trees == (str(tmp_path),)
    few = change.changed({str(tmp_path / "a")}, trees={str(tmp_path / "b")})
    assert few.folders == (str(tmp_path / "a"),) and few.trees == (str(tmp_path / "b"),)
    both = change.merged(few, change.ChangeBatch(full=True, reason="notification_lost"))
    assert both.full and both.reason == "notification_lost"


def test_known_directory_metadata_refreshes_itself_but_namespace_changes_refresh_parent():
    root = "C:\\owned"
    branch = root + "\\資料"
    scopes = {root, branch}
    assert windows_watch.parse_notifications(_notify("資料"), root, scopes).folders == (branch,)
    assert windows_watch.parse_notifications(_notify("資料", action=2), root, scopes).folders == (root,)
    _, modified = windows_watch.parse_usn(_usn(inode=55, directory=True), {22: root, 55: branch}, root, 100)
    assert modified.folders == (branch,)
    _, renamed = windows_watch.parse_usn(_usn(inode=55, reason=0x1000, directory=True),
                                        {22: root, 55: branch}, root, 100)
    assert renamed.folders == (root,)


@pytest.mark.parametrize("name", ["..\\escape", "C:\\foreign", "\\foreign", "x\\..\\foreign", "a\0b"])
def test_windows_event_names_cannot_become_foreign_targets(name):
    with pytest.raises(ValueError, match="Unsafe"):
        windows_watch.parse_notifications(_notify(name), "C:\\owned", {"C:\\owned"})


@pytest.mark.parametrize("payload", [b"bad", _notify(action=9), _notify(next_offset=1), _notify()[:-1]])
def test_windows_malformed_records_are_not_partial_success(payload):
    with pytest.raises(ValueError):
        windows_watch.parse_notifications(payload, "C:\\owned", {"C:\\owned"})


def test_usn_uses_captured_ids_and_external_shared_alias_changes_refresh_known_parents():
    root = "C:\\owned"
    cursor, batch = windows_watch.parse_usn(_usn(), {22: root + "\\資料"}, root, 100)
    assert cursor > 100 and batch.folders == (root + "\\資料",)
    _, outside = windows_watch.parse_usn(_usn(parent=99), {22: root}, root, 100)
    assert not outside.folders and not outside.full
    _, shared = windows_watch.parse_usn(_usn(parent=99), {22: root}, root, 100, {55: (root,)})
    assert shared.folders == (root,)
    _, inside = windows_watch.parse_usn(_usn(reason=0x10000), {22: root}, root, 100)
    assert inside.folders == (root,) and not inside.full  # a name made inside: its folder
    _, aliases = windows_watch.parse_usn(_usn(reason=0x10000, parent=99), {22: root}, root, 100)
    assert aliases.full and aliases.reason == "hard_links_changed"  # elsewhere, and no way to look it up
    linked = set()
    _, looked_up = windows_watch.parse_usn(_usn(reason=0x10000, parent=99), {22: root}, root, 100, None, linked)
    assert linked == {55} and not looked_up.full and not looked_up.folders


def test_a_file_relinked_elsewhere_reads_only_the_folders_holding_its_names(monkeypatch):
    names = {1: ["\\owned\\資料\\file", "\\elsewhere\\alias"], 2: ["\\elsewhere\\only"]}

    def failure(code):
        error = OSError("owned lookup failure")
        error.winerror = code  # what ctypes.WinError sets; plain OSError has none outside Windows
        return error

    def names_of(_kernel, _volume, number):
        if number == 3:
            raise failure(2)  # the file is gone
        if number == 4:
            raise failure(5)  # access denied
        return names[number]

    monkeypatch.setattr(windows_watch, "_names_of", names_of)
    assert windows_watch._linked_folders(None, None, {1, 2, 3}, "C:\\", "C:\\owned") == {"C:\\owned\\資料"}
    assert windows_watch._linked_folders(None, None, {1, 4}, "C:\\", "C:\\owned") is None
    assert windows_watch._linked_folders(None, None, set(range(100)), "C:\\", "C:\\owned") is None


def test_a_busy_journal_is_read_on_at_once_and_notification_buffers_fit_the_drive(monkeypatch):
    folder = change.WatchFolder("C:\\owned", 7, 22)
    kernel = SimpleNamespace(CreateFileW=lambda *_args: 42, CloseHandle=lambda _handle: None)
    reads, waits = [], []

    def control(_kernel, _handle, code, data=b""):
        if code == windows_watch._QUERY_USN:
            return windows_watch._JOURNAL.pack(9, 50, 400, 50, 0, 4096, 1024)
        start = windows_watch._READ.unpack(data)[0]
        reads.append(start)
        if len(reads) == 3:
            cancel.set()
        return struct.pack("<q", min(start + 100, 400))  # a full buffer each time, until caught up

    class Wait(threading.Event):
        def wait(self, timeout=None):
            waits.append(timeout)
            return super().wait(0)

    cancel = Wait()
    monkeypatch.setattr(windows_watch, "_control", control)
    monkeypatch.setattr(windows_watch, "_volume", lambda _path: ("C:\\", "{owned}"))
    monkeypatch.setattr(windows_watch, "check_folder", lambda _folder: None)
    windows_watch._watch_usn(kernel, (folder,), lambda _batch: None, cancel, None, (), since=(9, 100))
    assert reads == [100, 200, 300] and waits == [windows_watch.POLL_SECONDS]  # no wait until caught up
    drives = SimpleNamespace(GetDriveTypeW=lambda _drive: 4)
    assert windows_watch._notify_size(drives, "Z:\\share") == windows_watch._NOTIFY_REMOTE
    assert windows_watch._notify_size(drives, "\\\\server\\share") == windows_watch._NOTIFY_REMOTE
    assert windows_watch._notify_size(SimpleNamespace(GetDriveTypeW=lambda _drive: 3), "C:\\owned") == (
        windows_watch._NOTIFY_LOCAL)


@pytest.mark.parametrize("payload", [b"bad", _usn(major=3), _usn(usn=90), _usn()[:-1], _usn(name="..")])
def test_corrupt_unsupported_or_old_usn_records_refuse_incremental_updates(payload):
    with pytest.raises(ValueError):
        windows_watch.parse_usn(payload, {22: "C:\\owned"}, "C:\\owned", 100)


def test_inotify_shared_inode_events_and_scope_loss():
    folders = {1: ("/owned",), 2: ("/owned/a", "/owned/b")}
    payload = struct.pack("iIII", 2, 2, 0, 0)
    assert linux_watch.parse_inotify(payload, folders).folders == ("/owned/a", "/owned/b")
    assert linux_watch.parse_inotify(struct.pack("iIII", -1, 0x4000, 0, 0), folders).full
    assert linux_watch.parse_inotify(struct.pack("iIII", 1, 0x8000, 0, 0), folders).full
    with pytest.raises(ValueError):
        linux_watch.parse_inotify(payload[:-1], folders)
    assert change.changed({str(number) for number in range(change.MAX_CHANGED + 1)}).full


def test_overlapped_buffer_is_copied_after_completion_and_kernel_io_is_joined(monkeypatch):
    payload, calls, buffers = _notify("file"), [], []

    def read(_handle, buffer, *_args):
        buffers.append(buffer)
        calls.append("read")
        return 1

    def complete(*_args):
        buffers[0][:len(payload)] = payload
        calls.append("complete")
        return len(payload)

    kernel = SimpleNamespace(ResetEvent=lambda _event: None, ReadDirectoryChangesW=read,
                             CancelIoEx=lambda *_args: calls.append("cancel"),
                             GetOverlappedResult=lambda *_args: calls.append("joined") or 1)
    monkeypatch.setattr(windows_watch, "_completion", complete)
    result = windows_watch._notification(kernel, 1, windows_watch._Overlapped(), threading.Event(),
                                         lambda: calls.append("armed"))
    assert result == payload and calls == ["read", "armed", "complete", "cancel", "joined"]


@pytest.mark.skipif(not (sys.platform in ("win32", "darwin") or sys.platform.startswith("linux")),
                    reason="native feed platform")
def test_native_owned_change_is_reported_and_cancellation_joins_without_source_mutation(tmp_path):
    source = tmp_path / "source"
    (source / "branch").mkdir(parents=True)
    (source / "kept").write_bytes(b"unchanged")
    root = scan(source).root
    _native_change(root, source / "branch", source / "branch" / "new", tmp_path)
    assert (source / "kept").read_bytes() == b"unchanged"


def _native_change(root, expected: Path, target: Path, scratch: Path):
    cancel, ready, arrived = threading.Event(), threading.Event(), threading.Event()
    errors, backends, batches = [], [], []

    def changed(batch):
        batches.append(batch)
        if str(expected) in batch.folders or batch.full:
            arrived.set()

    def initialized(backend):
        backends.append(backend)
        ready.set()

    def run():
        try:
            change.watch(root, changed, cancel, ready=initialized)
        except (OSError, ValueError) as error:
            errors.append(str(error))
            ready.set()

    worker = threading.Thread(target=run)
    worker.start()
    try:
        assert ready.wait(10) and not errors, errors
        assert backends
        with target.open("wb") as stream:
            stream.write(b"owned event bytes")
            stream.flush()
            os.fsync(stream.fileno())
        assert arrived.wait(10) and not errors, (batches, errors)
        assert target.resolve().is_relative_to(scratch.resolve())
        assert target.read_bytes() == b"owned event bytes"
    finally:
        cancel.set()
        worker.join(10)
        assert not worker.is_alive(), "native feed did not join"


@pytest.mark.skipif(sys.platform != "win32", reason="native NTFS change journal")
def test_native_hard_link_made_outside_reads_only_the_folder_of_its_name_inside(tmp_path):
    source = tmp_path / "source"
    (source / "a").mkdir(parents=True)
    (source / "a" / "file").write_bytes(b"owned bytes")
    root = scan(source).root
    cancel, ready, arrived = threading.Event(), threading.Event(), threading.Event()
    backends, batches, errors = [], [], []

    def changed(batch):
        batches.append(batch)
        if str(source / "a") in batch.folders or batch.full:
            arrived.set()

    def run():
        try:
            change.watch(root, changed, cancel, ready=lambda backend: (backends.append(backend), ready.set()))
        except (OSError, ValueError) as error:
            errors.append(str(error))
            ready.set()

    worker = threading.Thread(target=run)
    worker.start()
    try:
        assert ready.wait(10) and not errors, errors
        if backends != ["usn"]:
            pytest.skip("the NTFS change journal is not readable here")
        os.link(source / "a" / "file", tmp_path / "outside-alias")
        assert arrived.wait(10), batches
        assert not any(batch.full for batch in batches), batches
    finally:
        cancel.set()
        worker.join(10)
        assert not worker.is_alive(), "native feed did not join"
    assert (source / "a" / "file").read_bytes() == b"owned bytes"


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="native Linux external-alias feed")
def test_native_external_hard_link_write_refreshes_captured_source_parent(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "file").write_bytes(b"owned shared bytes")
    external = tmp_path / "outside-alias"
    os.link(source / "file", external)
    _native_change(scan(source).root, source, external, tmp_path)
    assert (source / "file").read_bytes() == b"owned event bytes"


def test_fsevents_name_changed_folders_inside_the_scan_and_every_loss_reads_all_of_it():
    root, forms = "/Users/owner/來源", ("/Users/owner/來源", "/System/Volumes/Data/Users/owner/來源")
    batch = mac_watch.parse_fsevents(["/Users/owner/來源/a/", "/System/Volumes/Data/Users/owner/來源/b",
                                      "/Users/owner/other"], [0, 0, 0], root, forms)
    assert batch.folders == ("/Users/owner/來源/a", "/Users/owner/來源/b") and not batch.full
    behind = mac_watch.parse_fsevents(["/Users/owner/來源/a"], [0x1], root, forms)
    assert behind.trees == ("/Users/owner/來源/a",) and not behind.folders  # could not keep up: read it whole
    for flag in (0x2, 0x4, 0x8):  # dropped by the user's stream or the kernel, or the numbers wrapped
        assert mac_watch.parse_fsevents(["/Users/owner/other"], [flag], root, forms).full
    assert mac_watch.parse_fsevents(["/Users/owner/來源"], [0x20], root, forms).full  # the scan root moved
    assert mac_watch.parse_fsevents(["/Users/owner/來源/disk"], [0x40], root, forms).full  # mounted inside
    assert not mac_watch.parse_fsevents(["/Volumes/other"], [0x40], root, forms).full  # mounted elsewhere
