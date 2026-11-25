"""Media headers are parsed within bounds and only ever propose candidates."""

import io
import random
import struct
import threading

import pytest

from test_gui import _wait, window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.core import similar_media as module
from je_file_tree.core.media_info import AUDIO, SUFFIXES, VIDEO, MediaError, MediaInfo, read_media
from je_file_tree.core.node import Node
from je_file_tree.core.scanner import scan
from je_file_tree.core.similar_media import alike, find_similar_media, group_media, plain_name
from je_file_tree.core.similar_photos import PhotoSearchCancelledError, SimilarPhotoResult
from je_file_tree.gui import i18n
from je_file_tree.gui.scan_worker import analyse


def box(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I4s", len(body) + 8, kind) + body


def mp4(seconds: float, width=0, height=0, title="", artist="", *, late=False, wide=False) -> bytes:
    mvhd = (struct.pack(">IQQIQ", 1 << 24, 0, 0, 1000, round(seconds * 1000)) if wide else
            struct.pack(">IIIII", 0, 0, 0, 1000, round(seconds * 1000)))
    parts = box(b"mvhd", mvhd + bytes(80))
    tracks = [(0, 0)] + ([(width, height)] if width else [])
    for wide_track, high in tracks:
        parts += box(b"trak", box(b"tkhd", bytes(76) + struct.pack(">II", wide_track << 16, high << 16)))
    tags = b"".join(box(name, box(b"data", bytes(8) + text.encode())) for name, text in
                    ((b"\xa9nam", title), (b"\xa9ART", artist)) if text)
    parts += box(b"udta", box(b"meta", bytes(4) + box(b"ilst", tags)))
    media = box(b"mdat", b"\0" * 5000)
    movie = box(b"moov", parts)
    return box(b"ftyp", b"isom") + (media + movie if late else movie + media)


def ebml(kind: int, body: bytes, *, unknown=False) -> bytes:
    size = b"\x01" + b"\xff" * 7 if unknown else struct.pack(">Q", len(body) | 1 << 56)
    return kind.to_bytes((kind.bit_length() + 7) // 8, "big") + size + body


def mkv(seconds: float, width=0, height=0, title="", *, unknown=False) -> bytes:
    info = ebml(0x2AD7B1, (1_000_000).to_bytes(3, "big")) + ebml(0x4489, struct.pack(">d", seconds * 1000))
    info += ebml(0x7BA9, title.encode()) if title else b""
    video = ebml(0xE0, ebml(0xB0, width.to_bytes(2, "big")) + ebml(0xBA, height.to_bytes(2, "big"))) if width else b""
    body = ebml(0x1549A966, info) + ebml(0x1654AE6B, ebml(0xAE, video)) + ebml(0x1F43B675, b"\0" * 100)
    return ebml(0x1A45DFA3, b"") + ebml(0x18538067, body, unknown=unknown)


def avi(seconds: float, width: int, height: int) -> bytes:
    avih = struct.pack("<IIIIIIIIII", 40_000, 0, 0, 0, round(seconds * 25), 0, 1, 0, width, height)
    body = b"AVI " + b"LIST" + struct.pack("<I", 4 + 8 + len(avih)) + b"hdrl" + b"avih" + struct.pack("<I", 40) + avih
    return b"RIFF" + struct.pack("<I", len(body)) + body


def wav(seconds: int) -> bytes:
    body = b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 8000, 8000, 1, 8)
    body += b"data" + struct.pack("<I", 8000 * seconds)
    return b"RIFF" + struct.pack("<I", len(body)) + body + bytes(8000 * seconds)


def comments(**tags) -> bytes:
    rows = [f"{name}={value}".encode() for name, value in tags.items()]
    return struct.pack("<I", 4) + b"test" + struct.pack("<I", len(rows)) + b"".join(struct.pack("<I", len(row)) + row
                                                                                  for row in rows)


def flac(seconds: int, **tags) -> bytes:
    info = bytes(10) + ((44100 << 44) | 44100 * seconds).to_bytes(8, "big") + bytes(16)
    note = comments(**tags)
    return (b"fLaC" + b"\0" + len(info).to_bytes(3, "big") + info + b"\x84" + len(note).to_bytes(3, "big") + note)


def opus(seconds: int, **tags) -> bytes:
    head = b"OggS" + bytes(22) + b"OpusHead" + struct.pack("<BBHI", 1, 2, 312, 48000) + b"OpusTags" + comments(**tags)
    return head + bytes(1000) + b"OggS" + b"\0\4" + struct.pack("<q", 48000 * seconds + 312) + bytes(20)


def vorbis(seconds: int) -> bytes:
    head = b"OggS" + bytes(22) + b"\x01vorbis" + struct.pack("<IBI", 0, 2, 44100) + b"\x03vorbis" + comments(title="V")
    return head + b"OggS" + b"\0\4" + struct.pack("<q", 44100 * seconds) + bytes(20)


def mp3(seconds: int, title="", *, xing=True) -> bytes:
    text = b"\3" + title.encode()
    frames = b"TIT2" + struct.pack(">I", len(text)) + b"\0\0" + text if title else b""
    size = len(frames)
    tag = b"ID3\3\0\0" + bytes((size >> 21 & 127, size >> 14 & 127, size >> 7 & 127, size & 127)) + frames
    frame = b"\xff\xfb\x90\x00" + bytes(32)  # 128 kbit/s, 44.1 kHz
    if xing:
        return tag + frame + b"Xing" + struct.pack(">II", 1, round(seconds * 44100 / 1152)) + bytes(500)
    return tag + frame + bytes(16000 * seconds - len(frame))


def _read(data: bytes, suffix: str) -> MediaInfo:
    return read_media(io.BytesIO(data), len(data), suffix)


@pytest.mark.parametrize("data, suffix, expected", [
    (mp4(61.5, 1920, 1080, "Trip", "Me"), ".mp4", MediaInfo(VIDEO, 61.5, 1920, 1080, "Trip", "Me")),
    (mp4(61.5, 1920, 1080, late=True, wide=True), ".mov", MediaInfo(VIDEO, 61.5, 1920, 1080)),
    (mp4(200, title="Song", artist="Band"), ".m4a", MediaInfo(AUDIO, 200, title="Song", artist="Band")),
    (mkv(90, 1280, 720, "Film"), ".mkv", MediaInfo(VIDEO, 90, 1280, 720, "Film")),
    (mkv(90, unknown=True), ".webm", MediaInfo(AUDIO, 90)),
    (avi(30, 640, 480), ".avi", MediaInfo(VIDEO, 30, 640, 480)),
    (wav(3), ".wav", MediaInfo(AUDIO, 3)),
    (flac(120, TITLE="T", artist="A"), ".flac", MediaInfo(AUDIO, 120, title="T", artist="A")),
    (opus(75, title="O"), ".opus", MediaInfo(AUDIO, 75, title="O")),
    (vorbis(44), ".ogg", MediaInfo(AUDIO, 44, title="V")),
    (mp3(20, "歌", xing=False), ".mp3", MediaInfo(AUDIO, 20, title="歌")),
])
def test_headers(data, suffix, expected):
    info = _read(data, suffix)
    assert info.duration == pytest.approx(expected.duration, abs=.05)
    assert (info.kind, info.width, info.height, info.title, info.artist) == (
        expected.kind, expected.width, expected.height, expected.title, expected.artist)


def test_mp3_frame_counts():
    assert _read(mp3(180, "x"), ".mp3").duration == pytest.approx(180, abs=.1)


@pytest.mark.parametrize("suffix", sorted(SUFFIXES))
def test_damaged_files_are_refused_and_never_hang(suffix):
    seed = random.Random(suffix)  # noqa: S311 - reproducible damage, not security
    samples = {".avi": avi(5, 4, 4), ".wav": wav(1), ".flac": flac(5), ".mp3": mp3(5), ".ogg": vorbis(5),
               ".opus": opus(5), ".oga": opus(5), ".mkv": mkv(5, 4, 4), ".webm": mkv(5, 4, 4)}
    good = samples.get(suffix, mp4(5, 4, 4, "t"))
    cases = [b"", good[:20], bytes(300), b"\xff" * 4000]
    for _ in range(300):
        data = bytearray(good)
        for _ in range(seed.randint(1, 12)):
            data[seed.randrange(min(len(data), 600))] = seed.randrange(256)
        cases.append(bytes(data[:seed.randint(1, len(data))]))
    for data in cases:
        try:
            info = _read(data, suffix)
        except MediaError:
            continue
        assert 0 < info.duration <= 30 * 86400


def test_unknown_extensions_and_oversized_headers_are_refused():
    with pytest.raises(MediaError):
        _read(mp4(5), ".txt")
    huge = box(b"ftyp", b"isom") + struct.pack(">I4s", (5 << 20) + 8, b"moov") + bytes(5 << 20)
    with pytest.raises(MediaError):
        _read(huge, ".mp4")


@pytest.mark.parametrize("text, plain", [
    ("01 - My Song (Live) [2019]", "my song"), ("My.Song.1080p.x264", "my song"), ("my_song", "my song"),
    ("Holiday 2021", "holiday"), ("歌 名", "歌 名"), ("12", ""),
])
def test_plain_names(text, plain):
    assert plain_name(text) == plain


def _file(name, duration, kind=AUDIO, **fields):
    return Node(name, False, size=10), MediaInfo(kind, duration, **fields)


def test_what_counts_as_alike():
    song = _file("01 My Song.mp3", 200)
    assert alike(song, _file("my_song.flac", 200.8), 1) and not alike(song, _file("my_song.flac", 203), 1)
    assert not alike(song, _file("Other.mp3", 200), 1)  # the same length alone says nothing about a song
    assert alike(song, _file("track07.mp3", 200, title="My Song"), 1)
    assert not alike(song, _file("My Song.mp4", 200, VIDEO), 1)
    film = _file("a.mkv", 5400, VIDEO, width=1920, height=1080)
    assert alike(film, _file("b.mp4", 5400.2, VIDEO, width=1280, height=720), 1)
    assert not alike(film, _file("b.mp4", 5400.2, VIDEO, width=640, height=480), 1)  # another shape
    assert not alike(film, _file("b.mp4", 5400.8, VIDEO, width=1280, height=720), 1)
    clip = _file("c.mp4", 10, VIDEO, width=1920, height=1080)
    assert not alike(clip, _file("d.mp4", 10, VIDEO, width=1920, height=1080), 1)


def test_groups_form_around_their_first_file():
    files = [_file("song.mp3", 10), _file("song.flac", 10.9), _file("song.wav", 11.8), _file("other.mp3", 10)]
    groups = group_media(files, 1)
    assert [[node.name for node in group.files] for group in groups] == [["song.mp3", "song.flac"]]
    assert groups[0].distances == [0, 900]
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(PhotoSearchCancelledError):
        group_media(files, 1, cancel)


@pytest.fixture
def library(tmp_path):
    folder = tmp_path / "media"
    folder.mkdir()
    (folder / "01 Song.flac").write_bytes(flac(100, title="Song"))
    (folder / "Song (copy).mp3").write_bytes(mp3(100, "Song"))
    (folder / "Film.1080p.mkv").write_bytes(mkv(600, 1920, 1080))
    (folder / "Film.mp4").write_bytes(mp4(600.3, 1280, 720))
    (folder / "broken.mp4").write_bytes(b"not a movie")
    (folder / "notes.txt").write_bytes(b"x" * 100)
    return folder


def test_a_search_reads_only_media_and_counts_failures(library):
    seen = []
    root = scan(library).root
    result = find_similar_media(root, min_size=1, progress=lambda read, skipped: seen.append((read, skipped)))
    assert isinstance(result, SimilarPhotoResult) and result.files_read == 4 and result.skipped == 1
    assert sorted(sorted(node.name for node in group.files) for group in result.groups) == [
        ["01 Song.flac", "Song (copy).mp3"], ["Film.1080p.mkv", "Film.mp4"]]
    assert result.thumbnails == {} and seen[-1] == (4, 1)
    for bad in ({"seconds": -1}, {"seconds": 17}, {"min_size": 0}):
        with pytest.raises(ValueError):
            find_similar_media(scan(library).root, **bad)


def test_changed_files_limits_and_cancellation(library, monkeypatch):
    root = scan(library).root
    (library / "Film.mp4").write_bytes(mp4(1))
    assert find_similar_media(root, min_size=1).skipped == 2
    monkeypatch.setattr(module, "MAX_FILES", 1)
    assert find_similar_media(root, min_size=1).limited
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(PhotoSearchCancelledError):
        find_similar_media(root, min_size=1, cancel=cancel)


def test_the_panel_lists_candidates_without_any_selection_authority(window, qapp, library):
    window.results.show_outcome(analyse(scan(library)))
    panel = window.results.duplicates
    panel.kind.setCurrentIndex(panel.kind.findData("media"))
    assert panel.distance.value() == 1 and not panel.distance.isHidden()
    assert panel.start_button.text() == i18n.tr("media_find")
    panel.min_size.setCurrentIndex(panel.min_size.findText(i18n.tr("duplicates_any_size")))
    panel.start()
    _wait(qapp, lambda: not panel.running)
    assert panel.model.rowCount() == 2 and not panel.groups
    assert not any(button.isEnabled() for button in (panel.select_extra, panel.link_extra, panel.keep_selected))
    assert panel.estimate.isHidden() and i18n.tr("media_hint") in panel.status.text()
    window.change_language("zh-TW")
    assert i18n.tr("media_hint") in panel.status.text()
    window.change_language("en")
    panel.kind.setCurrentIndex(panel.kind.findData("photos"))
    assert panel.distance.value() == 4 and panel.model.rowCount() == 0
    panel.kind.setCurrentIndex(0)
    assert panel.distance.isHidden() and panel.start_button.text() == i18n.tr("duplicates_find")
