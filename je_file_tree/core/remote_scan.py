"""Measure the folders of another computer over SSH and save them as a scan; nothing there is changed or opened.

The system's OpenSSH client makes the connection: keys or an agent only (it may not ask for a password), the
host's key has to be known already, and every kind of forwarding is off. FileTree never sees or keeps a credential.
The server's SFTP subsystem is asked to list folders and describe entries; no remote command is run.

The result is a saved scan (folder sizes) and the largest files as text. It deliberately never becomes a scanned
tree in the window: a remote path must not be mistaken for a local one by anything that opens or moves entries.
"""

from __future__ import annotations

import ctypes
import heapq
import os
import re
import subprocess  # nosec B404 - the fixed system OpenSSH client, without a shell
import sys
import threading
import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

from je_file_tree.core import sftp
from je_file_tree.core.export import export_json
from je_file_tree.core.node import Node
from je_file_tree.core.pacing import give_way

MAX_PENDING = 32
MAX_ENTRIES = 20_000_000
MAX_DEPTH = 2000
LARGEST = 200
_MAX_PATH = 4096
_MAX_REMOTE_PATH = 64 << 10
_MAX_ERROR = 4000
_PORTS = range(1, 65536)
_HOST = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,251}[A-Za-z0-9])?|\[?[0-9A-Fa-f:]{2,45}\]?")
_USER = re.compile(r"[A-Za-z0-9_](?:[A-Za-z0-9._@\\-]{0,62}[A-Za-z0-9._@-])?")
_OPTIONS = ("BatchMode=yes", "StrictHostKeyChecking=yes", "ForwardAgent=no", "ForwardX11=no",
            "ClearAllForwardings=yes", "PermitLocalCommand=no", "RequestTTY=no", "ConnectTimeout=20",
            "ServerAliveInterval=15", "ServerAliveCountMax=3", "ControlMaster=no")
_PROGRESS = .25


class RemoteScanError(Exception):
    """The scan could not be made; the message says why."""


class RemoteScanStoppedError(Exception):
    """Stopped on request."""


@dataclass(frozen=True, slots=True)
class RemoteTarget:
    """Which folder of which computer; anything a command line could misread is refused."""

    host: str
    path: str = "."
    user: str = ""
    port: int = 22

    def __post_init__(self) -> None:
        if not isinstance(self.host, str) or not _HOST.fullmatch(self.host):
            raise ValueError("unusable host")
        if not isinstance(self.user, str) or (self.user and not _USER.fullmatch(self.user)):
            raise ValueError("unusable user")
        if type(self.port) is not int or self.port not in _PORTS:
            raise ValueError("unusable port")
        if not isinstance(self.path, str) or not 0 < len(self.path) <= _MAX_PATH or set("\0\n\r") & set(self.path):
            raise ValueError("unusable path")

    def label(self, path: str) -> str:
        """How the scanned folder is named in the saved scan."""
        user = f"{self.user}@" if self.user else ""
        port = "" if self.port == 22 else f":{self.port}"  # noqa: PLR2004 - SSH's own port
        return f"sftp://{user}{self.host}{port}/{path.lstrip('/')}"


@dataclass(frozen=True, slots=True)
class RemoteFile:
    """One large file, as text."""

    path: str
    size: int
    modified: float


@dataclass(slots=True)
class RemoteProgress:
    """Counts so far."""

    folders: int = 0
    files: int = 0
    bytes: int = 0
    unread: int = 0


@dataclass(slots=True)
class RemoteResult:
    """What was measured. ``_root`` only writes the saved scan; it is not handed to the window."""

    label: str
    progress: RemoteProgress
    largest: list[RemoteFile]
    seconds: float
    _root: Node = field(repr=False)

    def save(self, target: str) -> None:
        """Write the folder tree as a saved scan, atomically."""
        export_json(self._root, target)


def _system_directory() -> str:
    buffer = ctypes.create_unicode_buffer(32768)
    length = ctypes.WinDLL("kernel32", use_last_error=True).GetSystemDirectoryW(buffer, len(buffer))
    if not 0 < length < len(buffer):
        raise RemoteScanError("the Windows system directory is unavailable")
    return buffer.value


def ssh_program() -> str | None:
    """The system's own OpenSSH client, at its fixed place; None when it is not installed."""
    if sys.platform == "win32":
        places = (os.path.join(_system_directory(), "OpenSSH", "ssh.exe"),)
    else:
        places = ("/usr/bin/ssh", "/bin/ssh", "/usr/local/bin/ssh")
    return next((place for place in places if os.path.isfile(place)), None)


def ssh_command(program: str, target: RemoteTarget) -> list[str]:
    """The fixed command line; the host is an operand after ``--`` and can never be an option."""
    command = [program, "-T"]
    for option in _OPTIONS:
        command += ["-o", option]
    command += ["-p", str(target.port)]
    if target.user:
        command += ["-l", target.user]
    return [*command, "-s", "--", target.host.strip("[]"), "sftp"]


@dataclass(slots=True)
class _Folder:
    path: bytes
    node: Node
    depth: int
    handle: bytes = b""


class RemoteWalk:
    """List a tree over one SFTP connection with several requests under way, never following a link."""

    def __init__(self, client: sftp.SftpClient, target: RemoteTarget, *,
                 progress: Callable[[RemoteProgress], None] | None = None,
                 cancel: threading.Event | None = None) -> None:
        self.client, self.target = client, target
        self.counts = RemoteProgress()
        self._report, self._cancel = progress, cancel
        self._told = 0.0
        self._largest: list[tuple[int, int, RemoteFile]] = []
        self._waiting: dict[int, tuple[str, _Folder]] = {}
        self._todo: list[_Folder] = []
        self._entries = 0

    def run(self) -> tuple[Node, str]:
        """The measured root and its absolute remote path."""
        self.client.start()
        path = self._absolute()
        reply = self._answer(self.client.lstat(path))
        if reply.kind != sftp.ATTRS or not sftp.attributes_of(reply).is_folder:
            raise RemoteScanError("the remote path is not a folder")
        text = path.decode("utf-8", "replace")
        root = Node(self.target.label(text), True, children=[])
        self._todo.append(_Folder(path, root, 0))
        while self._todo or self._waiting:
            self._stop()
            give_way()
            while self._todo and len(self._waiting) < MAX_PENDING:
                folder = self._todo.pop()
                self._waiting[self.client.opendir(folder.path)] = ("open", folder)
            self._handle(self.client.reply())
        _total(root)
        return root, text

    def largest(self) -> list[RemoteFile]:
        """The largest files, the largest first."""
        return [file for _size, _order, file in sorted(self._largest, reverse=True)]

    def _absolute(self) -> bytes:
        reply = self._answer(self.client.realpath(self.target.path.encode("utf-8")))
        names = sftp.names_of(reply) if reply.kind == sftp.NAME else []
        if len(names) != 1 or not names[0][0].startswith(b"/"):
            raise RemoteScanError("the remote path was not found")
        return names[0][0]

    def _answer(self, request: int) -> sftp.Reply:
        self._stop()
        reply = self.client.reply()
        if reply.request != request:
            raise sftp.SftpError("an answer to another request")
        return reply

    def _stop(self) -> None:
        if self._cancel is not None and self._cancel.is_set():
            raise RemoteScanStoppedError

    def _handle(self, reply: sftp.Reply) -> None:
        if reply.request not in self._waiting:
            raise sftp.SftpError("an answer nobody asked for")
        phase, folder = self._waiting.pop(reply.request)
        if phase == "close":
            return
        if phase == "open":
            if reply.kind != sftp.HANDLE:
                self._unreadable(folder)
                return
            folder.handle = sftp.handle_of(reply)
            self.counts.folders += 1
            self._waiting[self.client.readdir(folder.handle)] = ("read", folder)
            return
        if reply.kind == sftp.NAME:
            self._list(folder, sftp.names_of(reply))
            self._waiting[self.client.readdir(folder.handle)] = ("read", folder)
            return
        if reply.kind != sftp.STATUS or sftp.status_of(reply) != sftp.EOF:
            self._unreadable(folder)
        self._waiting[self.client.close(folder.handle)] = ("close", folder)

    def _unreadable(self, folder: _Folder) -> None:
        folder.node.error = "access denied"
        self.counts.unread += 1

    def _list(self, folder: _Folder, entries: list[tuple[bytes, sftp.Attributes]]) -> None:
        for name, attributes in entries:
            if not sftp.usable_name(name):
                continue
            self._entries += 1
            if self._entries > MAX_ENTRIES:
                raise RemoteScanError("there are too many entries")
            if attributes.is_folder:
                self._found_folder(folder, name)
            elif attributes.is_file:
                self._found_file(folder, name, attributes)
        self._tell()

    def _found_folder(self, folder: _Folder, name: bytes) -> None:
        node = Node(name.decode("utf-8", "replace"), True, children=[], parent=folder.node)
        folder.node.children.append(node)
        path = folder.path.rstrip(b"/") + b"/" + name
        if folder.depth >= MAX_DEPTH or len(path) > _MAX_REMOTE_PATH:
            node.error = "nested too deeply"
            self.counts.unread += 1
            return
        self._todo.append(_Folder(path, node, folder.depth + 1))

    def _found_file(self, folder: _Folder, name: bytes, attributes: sftp.Attributes) -> None:
        node = folder.node
        node.size += attributes.size
        node.allocated += attributes.size  # SFTP does not say what a file takes on disk
        node.file_count += 1
        node.modified = max(node.modified, float(attributes.modified))
        self.counts.files += 1
        self.counts.bytes += attributes.size
        if len(self._largest) < LARGEST or attributes.size > self._largest[0][0]:
            path = (folder.path.rstrip(b"/") + b"/" + name).decode("utf-8", "replace")
            item = (attributes.size, self._entries, RemoteFile(path, attributes.size, float(attributes.modified)))
            (heapq.heappush if len(self._largest) < LARGEST else heapq.heapreplace)(self._largest, item)

    def _tell(self) -> None:
        now = time.monotonic()
        if self._report is not None and now - self._told >= _PROGRESS:
            self._told = now
            self._report(RemoteProgress(self.counts.folders, self.counts.files, self.counts.bytes, self.counts.unread))


def _total(root: Node) -> None:
    """Add every folder's own files up to its ancestors, deepest first."""
    order, stack = [], [root]
    while stack:
        give_way()
        node = stack.pop()
        order.append(node)
        stack.extend(node.children)
    for node in reversed(order):
        give_way()
        for child in node.children:
            node.size += child.size
            node.allocated += child.allocated
            node.file_count += child.file_count
            node.dir_count += child.dir_count + 1
            node.modified = max(node.modified, child.modified)
        node.children.sort(key=lambda child: -child.size)


def scan_streams(reader: BinaryIO, writer: BinaryIO, target: RemoteTarget, *,
                 progress: Callable[[RemoteProgress], None] | None = None,
                 cancel: threading.Event | None = None) -> RemoteResult:
    """Measure over an open SFTP connection."""
    started = time.monotonic()
    walk = RemoteWalk(sftp.SftpClient(reader, writer), target, progress=progress, cancel=cancel)
    root, _path = walk.run()
    return RemoteResult(root.name, walk.counts, walk.largest(), time.monotonic() - started, root)


class RemoteScan:
    """One connection: ``run`` on a worker, ``stop`` from anywhere."""

    def __init__(self, target: RemoteTarget, program: str | None = None) -> None:
        self.target, self.program = target, program
        self.cancel = threading.Event()
        self._process: subprocess.Popen[bytes] | None = None
        self._lock = threading.Lock()

    def stop(self) -> None:
        """Give up and end the connection."""
        self.cancel.set()
        with self._lock:
            if self._process is not None:
                with suppress(OSError):
                    self._process.kill()

    def run(self, progress: Callable[[RemoteProgress], None] | None = None) -> RemoteResult:
        """Connect and measure; raises ``RemoteScanError`` with the client's own explanation."""
        program = self.program or ssh_program()
        if program is None:
            raise RemoteScanError("OpenSSH is not installed")
        with self._lock:
            if self.cancel.is_set():
                raise RemoteScanStoppedError
            process = subprocess.Popen(  # noqa: S603 # nosec B603 - fixed program, validated operands, no shell
                ssh_command(program, self.target), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, cwd=str(Path(program).parent),
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            self._process = process
        said: list[bytes] = []
        listener = threading.Thread(target=_drain, args=(process.stderr, said), daemon=True)
        listener.start()
        try:
            return scan_streams(process.stdout, process.stdin, self.target, progress=progress, cancel=self.cancel)
        except sftp.SftpError as error:
            if self.cancel.is_set():
                raise RemoteScanStoppedError from error
            process.kill()
            listener.join(5)
            text = b"".join(said).decode("utf-8", "replace").strip()
            raise RemoteScanError(text or str(error)) from error
        finally:
            self._end(process, listener)

    def _end(self, process: subprocess.Popen[bytes], listener: threading.Thread) -> None:
        with suppress(OSError):
            process.kill()
        process.wait()
        listener.join(5)
        for stream in (process.stdin, process.stdout, process.stderr):
            with suppress(OSError):
                stream.close()
        with self._lock:
            self._process = None


def _drain(stream: BinaryIO, said: list[bytes]) -> None:
    """Keep the beginning of what the client says, and keep reading so it never blocks."""
    kept = 0
    with suppress(OSError, ValueError):
        while data := stream.read1(4096):
            if kept < _MAX_ERROR:
                said.append(data[:_MAX_ERROR - kept])
                kept += len(data)
