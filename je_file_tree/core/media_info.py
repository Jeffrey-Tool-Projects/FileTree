"""Duration, picture size, title and artist from the headers of audio and video files, with the standard library.

Only container metadata is read, a few megabytes at most per file; no frame is decoded and no codec is loaded.
PyAV (28 MB), numpy (12.7 MB) or Qt's bundled FFmpeg (about 20 MB in the stand-alone program) would be the
alternatives, and would decode untrusted media in this process (measured 2026-11-26).
"""

from __future__ import annotations

import struct
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import BinaryIO

VIDEO, AUDIO = "video", "audio"
_HEAD = 4 << 20
_TAIL = 64 << 10
_MAX_BOXES = 20_000
_MAX_TEXT = 300
_MAX_SECONDS = 30 * 86400.0
_MAX_SIDE = 1 << 20  # pixels


class MediaError(ValueError):
    """The headers are damaged, unknown or say nothing useful."""


@dataclass(frozen=True, slots=True)
class MediaInfo:
    """What the headers say; 0 or empty means they do not."""

    kind: str
    duration: float
    width: int = 0
    height: int = 0
    title: str = ""
    artist: str = ""


def read_media(stream: BinaryIO, size: int, suffix: str) -> MediaInfo:
    """Parse the headers of an open file by its lower-case extension; raises ``MediaError``."""
    reader = _READERS.get(suffix)
    if reader is None:
        raise MediaError("unknown extension")
    try:
        info = reader(stream, size)
    except (struct.error, IndexError, KeyError, OverflowError, ZeroDivisionError, UnicodeDecodeError) as error:
        raise MediaError("damaged headers") from error
    if not 0 < info.duration <= _MAX_SECONDS:
        raise MediaError("no duration")
    if max(info.width, info.height) > _MAX_SIDE:
        raise MediaError("no picture size")
    return info


def _at(stream: BinaryIO, offset: int, count: int) -> bytes:
    stream.seek(offset)
    return stream.read(count)


def _text(data: bytes) -> str:
    return " ".join(data.decode("utf-8", "replace").replace("\0", " ").split())[:_MAX_TEXT]


# --- MP4, MOV, M4A, 3GP -----------------------------------------------------


def _boxes(data: bytes) -> Iterator[tuple[bytes, bytes]]:
    offset = count = 0
    while offset + 8 <= len(data) and count < _MAX_BOXES:
        count += 1
        size, kind = struct.unpack_from(">I4s", data, offset)
        header = 8
        if size == 1:
            size, header = struct.unpack_from(">Q", data, offset + 8)[0], 16
        elif size == 0:
            size = len(data) - offset
        if size < header:
            raise MediaError("damaged box")
        yield kind, data[offset + header:offset + size]
        offset += size


def _movie(stream: BinaryIO, size: int) -> bytes:
    offset = count = 0
    while offset + 8 <= size and count < _MAX_BOXES:
        count += 1
        head = _at(stream, offset, 16)
        length, kind = struct.unpack_from(">I4s", head)
        header = 8
        if length == 1:
            length, header = struct.unpack_from(">Q", head, 8)[0], 16
        elif length == 0:
            length = size - offset
        if length < header:
            raise MediaError("damaged box")
        if kind == b"moov":
            if length > _HEAD:
                raise MediaError("the header is too large")
            return _at(stream, offset + header, length - header)
        offset += length
    raise MediaError("no movie header")


def _mp4(stream: BinaryIO, size: int) -> MediaInfo:
    duration, width, height, tags = 0.0, 0, 0, {}
    for kind, body in _boxes(_movie(stream, size)):
        if kind == b"mvhd":
            duration = _scaled(body)
        elif kind == b"trak":
            for inner, track in _boxes(body):
                if inner == b"tkhd":
                    place = 88 if track[0] == 1 else 76
                    wide, high = struct.unpack_from(">II", track, place)
                    if (wide >> 16) * (high >> 16) > width * height:
                        width, height = wide >> 16, high >> 16
        elif kind == b"udta":
            tags |= _mp4_tags(body)
    return MediaInfo(VIDEO if width and height else AUDIO, duration, width, height, tags.get(b"\xa9nam", ""),
                     tags.get(b"\xa9ART", ""))


def _scaled(body: bytes) -> float:
    if body[0] == 1:
        scale, length = struct.unpack_from(">IQ", body, 20)
    else:
        scale, length = struct.unpack_from(">II", body, 12)
    return length / scale


def _mp4_tags(user: bytes) -> dict[bytes, str]:
    tags = {}
    for kind, meta in _boxes(user):
        if kind != b"meta":
            continue
        for inner, items in _boxes(meta[4:]):
            if inner == b"ilst":
                for name, item in _boxes(items):
                    tags[name] = next((_text(data[8:]) for part, data in _boxes(item) if part == b"data"), "")
    return tags


# --- Matroska, WebM -----------------------------------------------------------


def _vint(data: bytes, offset: int, *, marker: bool) -> tuple[int, int]:
    first = data[offset]
    length = next((index for index in range(1, 9) if first & (0x80 >> (index - 1))), 0)
    if not length or offset + length > len(data):
        raise MediaError("damaged element")
    value = first if marker else first & (0xFF >> length)
    for byte in data[offset + 1:offset + length]:
        value = value << 8 | byte
    unknown = not marker and value == (1 << 7 * length) - 1
    return (-1 if unknown else value), offset + length


def _elements(data: bytes) -> Iterator[tuple[int, bytes]]:
    offset = count = 0
    while offset < len(data) and count < _MAX_BOXES:
        count += 1
        kind, offset = _vint(data, offset, marker=True)
        size, offset = _vint(data, offset, marker=False)
        end = len(data) if size < 0 else offset + size
        yield kind, data[offset:end]
        offset = end


def _matroska(stream: BinaryIO, size: int) -> MediaInfo:
    data = _at(stream, 0, min(size, _HEAD))
    scale, length, width, height, title = 1_000_000, 0.0, 0, 0, ""
    for kind, segment in _elements(data):
        if kind != 0x18538067:  # noqa: PLR2004 - element numbers are the format's own
            continue
        for part, body in _elements(segment):
            if part == 0x1549A966:  # noqa: PLR2004
                for name, value in _elements(body):
                    if name == 0x2AD7B1:  # noqa: PLR2004
                        scale = int.from_bytes(value, "big")
                    elif name == 0x4489:  # noqa: PLR2004
                        length = struct.unpack(">f" if len(value) == 4 else ">d", value)[0]  # noqa: PLR2004
                    elif name == 0x7BA9:  # noqa: PLR2004
                        title = _text(value)
            elif part == 0x1654AE6B:  # noqa: PLR2004
                width, height = _matroska_picture(body)
            elif part == 0x1F43B675:  # noqa: PLR2004 - the first cluster: the headers are over
                break
    return MediaInfo(VIDEO if width and height else AUDIO, length * scale / 1e9, width, height, title)


def _matroska_picture(tracks: bytes) -> tuple[int, int]:
    best = (0, 0)
    for _kind, track in _elements(tracks):
        for name, video in _elements(track):
            if name != 0xE0:  # noqa: PLR2004
                continue
            sizes = {part: int.from_bytes(value, "big") for part, value in _elements(video) if part in (0xB0, 0xBA)}
            found = sizes.get(0xB0, 0), sizes.get(0xBA, 0)
            best = max(best, found, key=lambda pair: pair[0] * pair[1])
    return best


# --- RIFF: AVI, WAV -------------------------------------------------------------


def _chunks(data: bytes) -> Iterator[tuple[bytes, int, bytes]]:
    offset = count = 0
    while offset + 8 <= len(data) and count < _MAX_BOXES:
        count += 1
        kind, size = struct.unpack_from("<4sI", data, offset)
        yield kind, size, data[offset + 8:offset + 8 + size]
        offset += 8 + size + (size & 1)


def _riff(data: bytes, kind: bytes) -> bytes:
    if data[:4] not in (b"RIFF", b"RF64") or data[8:12] != kind:
        raise MediaError("not this format")
    return data[12:]


def _avi(stream: BinaryIO, size: int) -> MediaInfo:
    for kind, _size, body in _chunks(_riff(_at(stream, 0, min(size, _HEAD)), b"AVI ")):
        if kind == b"LIST" and body[:4] == b"hdrl":
            for inner, _length, header in _chunks(body[4:]):
                if inner == b"avih":
                    frame, frames = struct.unpack_from("<I", header)[0], struct.unpack_from("<I", header, 16)[0]
                    width, height = struct.unpack_from("<II", header, 32)
                    return MediaInfo(VIDEO, frame * frames / 1e6, width, height)
    raise MediaError("no header")


def _wav(stream: BinaryIO, size: int) -> MediaInfo:
    rate = 0
    for kind, length, body in _chunks(_riff(_at(stream, 0, min(size, _HEAD)), b"WAVE")):
        if kind == b"fmt ":
            rate = struct.unpack_from("<I", body, 8)[0]
        elif kind == b"data":
            return MediaInfo(AUDIO, min(length, size) / rate)
    raise MediaError("no data")


# --- FLAC, Ogg, MP3 ---------------------------------------------------------------


def _comments(data: bytes) -> dict[str, str]:
    """The comments that were read whole: cover art among them can reach past what is read of an Ogg file."""
    offset = 4 + struct.unpack_from("<I", data)[0]
    if offset + 4 > len(data):
        return {}
    count = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    tags: dict[str, str] = {}
    for _ in range(min(count, 200)):
        if offset + 4 > len(data):
            break
        length = struct.unpack_from("<I", data, offset)[0]
        name, _separator, value = data[offset + 4:offset + 4 + length].partition(b"=")
        tags.setdefault(_text(name).lower(), _text(value))
        offset += 4 + length
    return tags


def _flac(stream: BinaryIO, size: int) -> MediaInfo:
    data = _at(stream, 0, min(size, _HEAD))
    if data[:4] != b"fLaC":
        raise MediaError("not FLAC")
    offset, duration, tags = 4, 0.0, {}
    while offset + 4 <= len(data):
        last, kind = data[offset] >> 7, data[offset] & 0x7F
        length = int.from_bytes(data[offset + 1:offset + 4], "big")
        body = data[offset + 4:offset + 4 + length]
        if kind == 0:
            packed = int.from_bytes(body[10:18], "big")
            duration = (packed & ((1 << 36) - 1)) / (packed >> 44)
        elif kind == 4:  # noqa: PLR2004 - the comment block
            tags = _comments(body)
        offset += 4 + length
        if last:
            break
    return MediaInfo(AUDIO, duration, title=tags.get("title", ""), artist=tags.get("artist", ""))


def _ogg(stream: BinaryIO, size: int) -> MediaInfo:
    head = _at(stream, 0, min(size, _TAIL))
    if head[:4] != b"OggS":
        raise MediaError("not Ogg")
    rate, skip, tags = 0, 0, {}
    if (place := head.find(b"\x01vorbis")) >= 0:
        rate = struct.unpack_from("<I", head, place + 12)[0]
        marker = head.find(b"\x03vorbis")
        tags = _comments(head[marker + 7:]) if marker >= 0 else {}
    elif (place := head.find(b"OpusHead")) >= 0:
        rate, skip = 48000, struct.unpack_from("<H", head, place + 10)[0]
        marker = head.find(b"OpusTags")
        tags = _comments(head[marker + 8:]) if marker >= 0 else {}
    else:
        raise MediaError("unknown Ogg stream")
    tail = _at(stream, max(0, size - _TAIL), _TAIL)
    last = tail.rfind(b"OggS")
    samples = struct.unpack_from("<q", tail, last + 6)[0]
    return MediaInfo(AUDIO, (samples - skip) / rate, title=tags.get("title", ""), artist=tags.get("artist", ""))


_MPEG1 = (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320)
_MPEG2 = (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160)
_RATES = {3: (44100, 48000, 32000), 2: (22050, 24000, 16000), 0: (11025, 12000, 8000)}


def _mp3(stream: BinaryIO, size: int) -> MediaInfo:
    head = _at(stream, 0, 10)
    start, tags = 0, {}
    if head[:3] == b"ID3":
        length = head[6] << 21 | head[7] << 14 | head[8] << 7 | head[9]
        start = 10 + length
        tags = _id3(_at(stream, 10, min(length, _HEAD)), head[3])
    data = _at(stream, start, _TAIL)
    for offset in range(len(data) - 4):
        if data[offset] == 0xFF and data[offset + 1] & 0xE6 == 0xE2:  # noqa: PLR2004 - sync, layer III
            duration = _mp3_length(data[offset:], size - start - offset)
            if duration:
                return MediaInfo(AUDIO, duration, title=tags.get("TIT2", ""), artist=tags.get("TPE1", ""))
    raise MediaError("no frame")


def _mp3_length(frame: bytes, rest: int) -> float:
    version, bitrate, rate = frame[1] >> 3 & 3, frame[2] >> 4, frame[2] >> 2 & 3
    if version not in _RATES or rate == 3 or bitrate in (0, 15):  # noqa: PLR2004 - reserved values
        return 0.0
    hertz, samples = _RATES[version][rate], 1152 if version == 3 else 576  # noqa: PLR2004 - MPEG 1 is 3
    for marker in (b"Xing", b"Info"):
        place = frame.find(marker, 0, 200)
        if place >= 0 and struct.unpack_from(">I", frame, place + 4)[0] & 1:
            return struct.unpack_from(">I", frame, place + 8)[0] * samples / hertz
    place = frame.find(b"VBRI", 0, 200)
    if place >= 0:
        return struct.unpack_from(">I", frame, place + 14)[0] * samples / hertz
    kilobits = (_MPEG1 if version == 3 else _MPEG2)[bitrate]  # noqa: PLR2004
    return rest * 8 / (kilobits * 1000)


def _id3(data: bytes, version: int) -> dict[str, str]:
    tags: dict[str, str] = {}
    offset = 0
    while offset + 10 <= len(data) and data[offset:offset + 4].isalnum():
        name = data[offset:offset + 4].decode("ascii")
        raw = data[offset + 4:offset + 8]
        size = (raw[0] << 21 | raw[1] << 14 | raw[2] << 7 | raw[3]) if version >= 4 else int.from_bytes(raw, "big")  # noqa: PLR2004
        body = data[offset + 10:offset + 10 + size]
        if name in ("TIT2", "TPE1") and body:
            encoding = {0: "latin-1", 1: "utf-16", 2: "utf-16-be"}.get(body[0], "utf-8")
            tags[name] = " ".join(body[1:].decode(encoding, "replace").replace("\0", " ").split())[:_MAX_TEXT]
        offset += 10 + size
    return tags


_READERS: dict[str, Callable[[BinaryIO, int], MediaInfo]] = {
    **dict.fromkeys((".mp4", ".m4v", ".mov", ".m4a", ".3gp"), _mp4), **dict.fromkeys((".mkv", ".webm"), _matroska),
    ".avi": _avi, ".wav": _wav, ".flac": _flac, ".mp3": _mp3, **dict.fromkeys((".ogg", ".opus", ".oga"), _ogg),
}
SUFFIXES = frozenset(_READERS)
