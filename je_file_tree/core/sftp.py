"""The read-only part of the SFTP protocol (version 3): list folders and read metadata, nothing else.

Requests that could change anything are not implemented, so no code path can send one. File contents are never
requested. Every length a server sends is bounded before it is used.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import BinaryIO

INIT, VERSION, CLOSE, OPENDIR, READDIR, LSTAT, REALPATH = 1, 2, 4, 11, 12, 7, 16
STATUS, HANDLE, NAME, ATTRS = 101, 102, 104, 105
OK, EOF, NO_FILE, DENIED = 0, 1, 2, 3
PROTOCOL = 3
MAX_PACKET = 1 << 20
MAX_NAMES = 10_000
MAX_NAME = 1024
_MAX_HANDLE = 256
_SIZE, _OWNER, _PERMISSIONS, _TIMES, _EXTENDED = 1, 2, 4, 8, 0x80000000
_KIND, _FOLDER, _FILE, _LINK = 0o170000, 0o040000, 0o100000, 0o120000


class SftpError(OSError):
    """The server broke the protocol or ended the connection."""


@dataclass(frozen=True, slots=True)
class Attributes:
    """What a server says about an entry itself; links are not followed."""

    size: int = 0
    mode: int = 0
    modified: int = 0

    @property
    def is_folder(self) -> bool:
        """A real folder."""
        return self.mode & _KIND == _FOLDER

    @property
    def is_file(self) -> bool:
        """A regular file."""
        return self.mode & _KIND == _FILE

    @property
    def is_link(self) -> bool:
        """A symbolic link."""
        return self.mode & _KIND == _LINK


@dataclass(frozen=True, slots=True)
class Reply:
    """One server answer: its type, the request it belongs to and the rest of the packet."""

    kind: int
    request: int
    body: bytes


class _Body:
    def __init__(self, data: bytes) -> None:
        self.data, self.offset = data, 0

    def take(self, count: int) -> bytes:
        end = self.offset + count
        if count < 0 or end > len(self.data):
            raise SftpError("truncated packet")
        part, self.offset = self.data[self.offset:end], end
        return part

    def u32(self) -> int:
        return struct.unpack(">I", self.take(4))[0]

    def u64(self) -> int:
        return struct.unpack(">Q", self.take(8))[0]

    def text(self) -> bytes:
        return self.take(self.u32())

    def attributes(self) -> Attributes:
        flags = self.u32()
        size = self.u64() if flags & _SIZE else 0
        if flags & _OWNER:
            self.take(8)
        mode = self.u32() if flags & _PERMISSIONS else 0
        modified = 0
        if flags & _TIMES:
            self.u32()
            modified = self.u32()
        if flags & _EXTENDED:
            for _ in range(min(self.u32(), MAX_NAMES)):
                self.text()
                self.text()
        return Attributes(min(size, (1 << 63) - 1), mode, modified)


def _string(data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + data


class SftpClient:
    """Send read-only requests and read replies over a pair of pipes; the caller matches them by number."""

    def __init__(self, reader: BinaryIO, writer: BinaryIO) -> None:
        self._reader, self._writer = reader, writer
        self._next = 0

    def start(self) -> None:
        """Agree on the protocol version."""
        self._send(INIT, struct.pack(">I", PROTOCOL))
        kind, body = self._packet()
        if kind != VERSION or _Body(body).u32() < PROTOCOL:
            raise SftpError("the server does not speak SFTP 3")

    def realpath(self, path: bytes) -> int:
        """Ask for the absolute form of ``path``."""
        return self._request(REALPATH, _string(path))

    def lstat(self, path: bytes) -> int:
        """Ask what ``path`` itself is."""
        return self._request(LSTAT, _string(path))

    def opendir(self, path: bytes) -> int:
        """Ask to list a folder."""
        return self._request(OPENDIR, _string(path))

    def readdir(self, handle: bytes) -> int:
        """Ask for the next entries of an open folder."""
        return self._request(READDIR, _string(handle))

    def close(self, handle: bytes) -> int:
        """Give a folder handle back."""
        return self._request(CLOSE, _string(handle))

    def reply(self) -> Reply:
        """Wait for the next answer."""
        kind, data = self._packet()
        body = _Body(data)
        return Reply(kind, body.u32(), data[body.offset:])

    def _request(self, kind: int, body: bytes) -> int:
        self._next = (self._next + 1) & 0xFFFFFFFF
        self._send(kind, struct.pack(">I", self._next) + body)
        return self._next

    def _send(self, kind: int, body: bytes) -> None:
        try:
            self._writer.write(struct.pack(">IB", len(body) + 1, kind) + body)
            self._writer.flush()
        except (OSError, ValueError) as error:
            raise SftpError("the connection ended") from error

    def _packet(self) -> tuple[int, bytes]:
        length = struct.unpack(">I", self._exactly(4))[0]
        if not 1 <= length <= MAX_PACKET:
            raise SftpError("unusable packet")
        data = self._exactly(length)
        return data[0], data[1:]

    def _exactly(self, count: int) -> bytes:
        parts, missing = [], count
        while missing:
            try:
                part = self._reader.read(missing)
            except (OSError, ValueError) as error:
                raise SftpError("the connection ended") from error
            if not part:
                raise SftpError("the connection ended")
            parts.append(part)
            missing -= len(part)
        return b"".join(parts)


def status_of(reply: Reply) -> int:
    """The code of a status reply."""
    return _Body(reply.body).u32()


def handle_of(reply: Reply) -> bytes:
    """The handle of an opened folder."""
    handle = _Body(reply.body).text()
    if not 0 < len(handle) <= _MAX_HANDLE:
        raise SftpError("unusable handle")
    return handle


def attributes_of(reply: Reply) -> Attributes:
    """The attributes of one entry."""
    return _Body(reply.body).attributes()


def names_of(reply: Reply) -> list[tuple[bytes, Attributes]]:
    """Names with their attributes; ``.``, ``..`` and names that are no single name are dropped."""
    body = _Body(reply.body)
    count = body.u32()
    if count > MAX_NAMES:
        raise SftpError("too many names in one packet")
    found = []
    for _ in range(count):
        name = body.text()
        body.text()  # the long listing meant for people
        attributes = body.attributes()
        found.append((name, attributes))
    return found


def usable_name(name: bytes) -> bool:
    """Whether a listed name is one path component."""
    return name not in (b"", b".", b"..") and len(name) <= MAX_NAME and b"/" not in name and b"\0" not in name


