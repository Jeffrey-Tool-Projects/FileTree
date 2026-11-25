"""Optional third-party archive metadata adapters; no extraction or subprocess invocation."""

from __future__ import annotations

import shutil
import io
import struct
from collections.abc import Iterable, Iterator
from contextlib import contextmanager

from je_file_tree.core.archives import (
    MAX_METADATA_BYTES,
    ArchiveCancelledError,
    ArchiveError,
    ArchiveMember,
    MetadataReader,
)

_SEVEN_ZIP_SIGNATURE = b"7z\xbc\xaf'\x1c"
_ENCODED_HEADER = 0x17
_SIGNATURE_SIZE = 32


@contextmanager
def _decoding() -> Iterator[None]:
    """Report whatever a decoder raises over a damaged archive as one archive error, so no worker dies of it."""
    try:
        yield
    except (OSError, ImportError, ArchiveCancelledError):
        raise
    except Exception as exc:  # noqa: BLE001 - every codec has errors of its own (LZMAError is a plain Exception)
        raise ArchiveError(str(exc) or type(exc).__name__) from exc


def _guard_seven_zip_header(stream: MetadataReader) -> None:
    from py7zr.archiveinfo import HeaderStreamsInfo  # noqa: PLC0415 - lazy decoder metadata

    header = stream.read(_SIGNATURE_SIZE)
    if len(header) != _SIGNATURE_SIZE or not header.startswith(_SEVEN_ZIP_SIGNATURE):
        raise ArchiveError("Invalid 7z signature")
    offset, size = struct.unpack_from("<QQ", header, 12)
    stream.seek(_SIGNATURE_SIZE + offset)
    data = stream.read(size)
    if data and data[0] == _ENCODED_HEADER:
        streams = HeaderStreamsInfo.retrieve(io.BytesIO(data[1:]))
        total = sum(sum(folder.unpacksizes) for folder in streams.unpackinfo.folders)
        if total > MAX_METADATA_BYTES:
            raise ArchiveError("Decoded 7z header exceeds the 32 MiB metadata limit")
    stream.seek(0)


def seven_zip_members(stream: MetadataReader) -> Iterable[ArchiveMember]:
    """Read a 7z header through py7zr, never extract or test member contents."""
    import py7zr  # noqa: PLC0415 - only load the decoder after archive expansion

    with _decoding():
        _guard_seven_zip_header(stream)
        with py7zr.SevenZipFile(stream, mode="r") as archive:
            for info in archive.list():
                yield ArchiveMember(info.filename, info.uncompressed or 0, info.is_directory,
                                    getattr(info, "is_symlink", False)
                                    or not (info.is_directory or getattr(info, "is_file", True)))


def rar_members(stream: MetadataReader) -> Iterable[ArchiveMember]:
    """Read RAR headers only when unrar/bsdtar is available; never run that program."""
    import rarfile  # noqa: PLC0415 - only load the parser after archive expansion

    if not any(shutil.which(program) for program in ("unrar", "bsdtar")):
        raise ArchiveError("RAR preview requires unrar or bsdtar on PATH")
    with _decoding(), rarfile.RarFile(stream, mode="r") as archive:
        for info in archive.infolist():
            yield ArchiveMember(info.filename, info.file_size, info.isdir(),
                                info.is_symlink() or bool(info.file_redir))
