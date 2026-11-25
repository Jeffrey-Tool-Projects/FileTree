"""Remote scans only list folders, keep no secret and never become entries the window could act on."""

import inspect
import json
import os
import random
import socket
import struct
import sys
import threading
from contextlib import suppress

import pytest

from test_gui import _wait, window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.core import remote_scan as module
from je_file_tree.core import sftp
from je_file_tree.core.remote_scan import (
    RemoteScan,
    RemoteScanError,
    RemoteScanStoppedError,
    RemoteTarget,
    scan_streams,
    ssh_command,
    ssh_program,
)
from je_file_tree.core.scan_overview import import_scan
from je_file_tree.gui import remote_scan as gui_module
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.remote_scan import REMOTE_KEY, RemoteScanDialog

TARGET = RemoteTarget("host.example", "/data")
FOLDER, FILE, LINK = 0o040755, 0o100644, 0o120777


def _string(data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + data


def _attributes(mode: int, size: int) -> bytes:
    return (struct.pack(">IQII", 1 | 2 | 4 | 8, size, 0, 0) + struct.pack(">III", mode, 5, 1000 + size)
            if mode else struct.pack(">I", 0))


class FakeServer(threading.Thread):
    """Speak SFTP 3 over a socket; folders are dicts, files are sizes, None cannot be opened."""

    def __init__(self, tree, *, break_at=None):
        super().__init__(daemon=True)
        self.tree, self.break_at = tree, break_at
        self.ours, theirs = socket.socketpair()
        self.reader, self.writer = theirs.makefile("rb"), theirs.makefile("wb")
        theirs.close()
        self.stream = self.ours.makefile("rwb")
        self.requests, self.handles = [], {}
        self.start()

    def run(self):
        try:
            while head := self.stream.read(4):
                data = self.stream.read(struct.unpack(">I", head)[0])
                self.requests.append(data[0])
                if self.break_at == len(self.requests):
                    break
                self.answer(data[0], data[1:])
        except (OSError, struct.error):
            pass
        finally:
            with suppress(OSError):
                self.stream.close()
            self.ours.close()

    def send(self, kind, body):
        self.stream.write(struct.pack(">IB", len(body) + 1, kind) + body)
        self.stream.flush()

    def find(self, path):
        node = self.tree
        for part in path.strip(b"/").split(b"/")[1:]:
            node = node[part]
        return node

    def answer(self, kind, body):
        if kind == sftp.INIT:
            self.send(sftp.VERSION, struct.pack(">I", 3))
            return
        reply, data = self.reply(kind, body[8:])
        self.send(reply, body[:4] + data)

    def reply(self, kind, value):
        reply, data = sftp.STATUS, self.status(sftp.OK)
        if kind == sftp.REALPATH:
            reply, data = sftp.NAME, struct.pack(">I", 1) + _string(b"/data") * 2 + _attributes(0, 0)
        elif kind == sftp.LSTAT:
            reply, data = sftp.ATTRS, _attributes(FOLDER if isinstance(self.tree, dict) else FILE, 0)
        elif kind == sftp.OPENDIR:
            node = self.find(value)
            if node is None:
                data = self.status(sftp.DENIED)
            else:
                handle = str(len(self.handles)).encode()
                self.handles[handle] = list(node.items())
                reply, data = sftp.HANDLE, _string(handle)
        elif kind == sftp.READDIR:
            rows, self.handles[value] = self.handles[value][:3], self.handles[value][3:]
            data = self.status(sftp.EOF)
            if rows:
                reply = sftp.NAME
                data = struct.pack(">I", len(rows))
                data += b"".join(_string(name) + _string(b"-rw") + self.kind(node) for name, node in rows)
        return reply, data

    def end(self):
        for stream in (self.writer, self.reader):
            with suppress(OSError):
                stream.close()
        self.join(5)

    @staticmethod
    def status(code):
        return struct.pack(">I", code) + _string(b"") * 2

    @staticmethod
    def kind(node):
        if node == "link":
            return _attributes(LINK, 99)
        return _attributes(FILE, node) if isinstance(node, int) else _attributes(FOLDER, 4096)


TREE = {b".": {}, b"..": {}, b"a": {b"one.bin": 100, b"deep": {b"two.bin": 200, "資料".encode(): 5}},
        b"closed": None, b"empty": {}, b"top.bin": 50, b"away": "link", b"bad/name": 7, b"z\0": 7}


def _scan(tree=TREE, **options):
    server = FakeServer(tree)
    try:
        return scan_streams(server.reader, server.writer, TARGET, **options), server
    finally:
        server.end()


def test_a_tree_is_added_up_without_following_links(tmp_path):
    told = []
    result, server = _scan(progress=told.append)
    counts = result.progress
    assert (counts.folders, counts.files, counts.bytes, counts.unread) == (4, 4, 355, 1)
    assert [(file.path, file.size) for file in result.largest] == [
        ("/data/a/deep/two.bin", 200), ("/data/a/one.bin", 100), ("/data/top.bin", 50), ("/data/a/deep/資料", 5)]
    assert result.label == "sftp://host.example/data" and told
    target = tmp_path / "remote.json"
    result.save(str(target))
    saved = json.loads(target.read_text(encoding="utf-8"))
    root = saved["root"]
    assert root["size"] == 355 and root["files"] == 4 and root["folders"] == 4
    assert import_scan(target).label
    assert set(server.requests) <= {sftp.INIT, sftp.REALPATH, sftp.LSTAT, sftp.OPENDIR, sftp.READDIR, sftp.CLOSE}


def test_no_request_that_could_open_or_change_a_file_exists():
    # SFTP 3: open 3, read 5, write 6, setstat 9/10, remove 13, mkdir 14, rmdir 15, rename 18, symlink 20, extended 200
    sent = {value for name, value in vars(sftp).items() if name.isupper() and isinstance(value, int)}
    requests = {sftp.INIT, sftp.CLOSE, sftp.LSTAT, sftp.OPENDIR, sftp.READDIR, sftp.REALPATH}
    assert not {5, 6, 9, 10, 13, 14, 15, 18, 20, 200} & sent
    public = {name for name, _ in inspect.getmembers(sftp.SftpClient, inspect.isfunction) if not name.startswith("_")}
    assert public == {"start", "realpath", "lstat", "opendir", "readdir", "close", "reply"} and len(requests) == 6


def test_the_largest_files_are_bounded(monkeypatch):
    monkeypatch.setattr(module, "LARGEST", 2)
    result, _server = _scan()
    assert [file.size for file in result.largest] == [200, 100]


def test_limits_and_a_path_that_is_no_folder(monkeypatch):
    with pytest.raises(RemoteScanError):
        _scan(5)
    monkeypatch.setattr(module, "MAX_DEPTH", 1)
    result, _server = _scan()
    assert result.progress.unread == 2 and result.progress.bytes == 150
    monkeypatch.setattr(module, "MAX_ENTRIES", 2)
    with pytest.raises(RemoteScanError):
        _scan()


def test_stopping_ends_the_walk():
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(RemoteScanStoppedError):
        _scan(cancel=cancel)


@pytest.mark.parametrize("break_at", range(1, 9))
def test_a_connection_that_ends_is_an_error(break_at):
    server = FakeServer(TREE, break_at=break_at)
    with pytest.raises(sftp.SftpError):
        scan_streams(server.reader, server.writer, TARGET)
    server.end()


class Scripted:
    """Answer with fixed bytes, whatever is asked."""

    def __init__(self, data):
        self.data, self.sent = data, b""

    def read(self, count):
        part, self.data = self.data[:count], self.data[count:]
        return part

    def write(self, data):
        self.sent += data

    def flush(self):
        pass


def test_damaged_answers_are_refused():
    seed = random.Random(7)  # noqa: S311 - reproducible damage, not security
    hello = struct.pack(">IBI", 5, sftp.VERSION, 3)
    for _ in range(500):
        packets = b"".join(struct.pack(">I", 12) + bytes(seed.choices((0, 1, 2, 101, 102, 104, 105, 255), k=12))
                           for _ in range(4))
        stream = Scripted(hello + packets)
        with pytest.raises((sftp.SftpError, RemoteScanError)):
            scan_streams(stream, stream, TARGET)
    for data in (b"", struct.pack(">IBI", 5, sftp.VERSION, 2), struct.pack(">I", 1 << 30), struct.pack(">I", 0)):
        stream = Scripted(data)
        with pytest.raises(sftp.SftpError):
            scan_streams(stream, stream, TARGET)


@pytest.mark.parametrize("name, usable", [(b"a", True), (b"", False), (b".", False), (b"..", False), (b"a/b", False),
                                          (b"a\0", False), (b"x" * 1025, False), (b"-rf", True)])
def test_listed_names_are_single_names(name, usable):
    assert sftp.usable_name(name) is usable


@pytest.mark.parametrize("fields", [
    {"host": ""}, {"host": "-oProxyCommand=x"}, {"host": "a b"}, {"host": "a;b"}, {"host": "$(x)"}, {"host": "a\n"},
    {"host": "a", "user": "-l"}, {"host": "a", "user": "x y"}, {"host": "a", "user": "x`y`"},
    {"host": "a", "user": "x" + chr(92)}, {"host": "a", "port": 0}, {"host": "a", "port": 65536},
    {"host": "a", "port": True}, {"host": "a", "path": ""}, {"host": "a", "path": "x\0"}, {"host": "a", "path": "x\ny"},
    {"host": "a", "path": "x" * 5000}, {"host": 5},
])
def test_targets_a_command_line_could_misread_are_refused(fields):
    with pytest.raises(ValueError):
        RemoteTarget(**fields)


def test_the_command_is_fixed_and_asks_for_nothing():
    command = ssh_command("/usr/bin/ssh", RemoteTarget("[::1]", "/x y", "DOM" + chr(92) + "me", 2222))
    assert command[0] == "/usr/bin/ssh" and command[-5:] == ["DOM" + chr(92) + "me", "-s", "--", "::1", "sftp"]
    assert {"BatchMode=yes", "StrictHostKeyChecking=yes", "ForwardAgent=no", "ClearAllForwardings=yes",
            "PermitLocalCommand=no"} <= set(command)
    assert "/x y" not in command and command[command.index("-p") + 1] == "2222"


def test_only_the_system_client_at_its_fixed_place_is_used(monkeypatch, tmp_path):
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    (tmp_path / "ssh.exe").write_bytes(b"")
    (tmp_path / "ssh").write_bytes(b"")
    found = ssh_program()
    assert found is None or (os.path.isabs(found) and not found.startswith(str(tmp_path)))
    monkeypatch.setattr(module.os.path, "isfile", lambda _path: False)
    assert ssh_program() is None
    with pytest.raises(RemoteScanError):
        RemoteScan(TARGET).run()


def test_what_the_client_says_explains_a_failure():
    scan = RemoteScan(TARGET, sys.executable)  # Python refuses the options and says so on its error stream
    with pytest.raises(RemoteScanError) as caught:
        scan.run()
    assert len(str(caught.value)) > 10 and scan._process is None


def test_a_stopped_scan_never_connects(monkeypatch):
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_args, **_options: pytest.fail("connected"))
    scan = RemoteScan(TARGET, sys.executable)
    scan.stop()
    with pytest.raises(RemoteScanStoppedError):
        scan.run()


def _dialog(window, monkeypatch, run):
    monkeypatch.setattr(gui_module.RemoteScan, "run", run)
    return RemoteScanDialog(window.settings, "auto", window)


def test_the_dialog_connects_only_on_request_and_saves(window, qapp, monkeypatch, tmp_path):
    result, _server = _scan()
    dialog = _dialog(window, monkeypatch, lambda self, progress=None: result)
    assert not dialog.running and dialog.start.isEnabled() and not dialog.save.isEnabled()
    dialog.begin()
    assert dialog.status.text() == tr("remote_invalid") and not dialog.running
    dialog.host.setText("host.example")
    dialog.path.setText("/data")
    dialog.begin()
    assert not dialog.host.isEnabled() and dialog.stop.isEnabled()
    _wait(qapp, lambda: not dialog.running)
    assert dialog.table.rowCount() == 4 and dialog.table.item(0, 0).text() == "/data/a/deep/two.bin"
    assert "sftp://host.example/data" in dialog.status.text() and not dialog.compare.isEnabled()
    assert json.loads(window.settings.value(REMOTE_KEY)) == {"host": "host.example", "user": "", "port": 22,
                                                             "path": "/data"}
    target = tmp_path / "saved.json"
    monkeypatch.setattr(gui_module.QFileDialog, "getSaveFileName", lambda *_args: (str(target), ""))
    dialog.save.click()
    asked = []
    dialog.compare_requested.connect(asked.append)
    assert target.exists() and dialog.compare.isEnabled()
    dialog.compare.click()
    assert asked == [str(target)]
    again = RemoteScanDialog(window.settings, "auto", window)
    assert again.host.text() == "host.example" and again.path.text() == "/data"
    again.shutdown()


def test_failures_and_stopping_are_shown(window, qapp, monkeypatch):
    def refuse(self, progress=None):
        raise RemoteScanError("Host key verification failed.")

    dialog = _dialog(window, monkeypatch, refuse)
    dialog.host.setText("host.example")
    dialog.begin()
    _wait(qapp, lambda: not dialog.running)
    assert "Host key verification failed." in dialog.status.text() and not dialog.save.isEnabled()

    def wait(self, progress=None):
        self.cancel.wait(10)
        raise RemoteScanStoppedError

    monkeypatch.setattr(gui_module.RemoteScan, "run", wait)
    dialog.begin()
    dialog.stop.click()
    _wait(qapp, lambda: not dialog.running)
    assert dialog.status.text() == tr("scan_cancelled")
    dialog.begin()
    dialog.reject()  # closing joins the worker
    _wait(qapp, lambda: not dialog.running)


@pytest.mark.parametrize("saved", ["{", "[]", "5", '{"host": "-o", "path": ".", "user": "", "port": 22}',
                                   '{"host": "a", "path": ".", "user": "", "port": "22"}'])
def test_damaged_settings_are_ignored(window, saved):
    window.settings.setValue(REMOTE_KEY, saved)
    dialog = RemoteScanDialog(window.settings, "auto", window)
    assert dialog.host.text() == "" and dialog.port.value() == 22
    dialog.shutdown()


def test_the_window_passes_a_saved_scan_on_to_the_comparison(window, monkeypatch):
    seen = []
    monkeypatch.setattr(RemoteScanDialog, "exec", lambda self: self.compare_requested.emit("saved.json"))
    monkeypatch.setattr(window, "show_scan_overview", lambda files=(): seen.append(files))
    window._actions["remote_scan"].trigger()
    assert seen == [["saved.json"]]
