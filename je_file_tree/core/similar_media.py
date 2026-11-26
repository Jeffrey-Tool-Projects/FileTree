"""Group audio and video files whose headers suggest the same recording: candidates to compare, never proof."""

from __future__ import annotations

import re
import threading
from collections.abc import Callable

from je_file_tree.core.archives import opened
from je_file_tree.core.media_info import AUDIO, SUFFIXES, VIDEO, MediaInfo, MediaError, read_media
from je_file_tree.core.node import Node
from je_file_tree.core.pacing import give_way
from je_file_tree.core.preview import suffix_of
from je_file_tree.core.similar_photos import SimilarPhotoGroup, SimilarPhotoResult, check_cancel
from je_file_tree.core.snapshot import unpack_snapshot

DEFAULT_SECONDS = 1
MAX_SECONDS = 16
MAX_FILES = 100_000
_LONG_VIDEO = 60.0  # seconds: a longer video's exact length says something by itself
_EXACT = .5
_RATIO = .02
_MIN_NAME = 3
_NOISE = re.compile(r"\([^)]*\)|\[[^]]*\]|(?:19|20)\d\d|\b\d{3,4}[pi]\b|\b(?:x|h)\.?26[45]\b|^\d{1,3}\b",
                    re.IGNORECASE)
_PUNCTUATION = re.compile(r"[\W_]+")

MediaProgress = Callable[[int, int], None]


def plain_name(text: str) -> str:
    """A title or file name without numbering, brackets, years, resolutions and punctuation."""
    return " ".join(_PUNCTUATION.sub(" ", _NOISE.sub(" ", text.replace("_", " "))).casefold().split())


def _words(node: Node, info: MediaInfo) -> str:
    title = f"{info.artist} {info.title}" if info.title else node.name.rsplit(".", 1)[0]
    return plain_name(title)


def _same_shape(first: MediaInfo, second: MediaInfo) -> bool:
    if not (first.width and first.height and second.width and second.height):
        return False
    one, two = first.width / first.height, second.width / second.height
    return abs(one - two) <= _RATIO * max(one, two)


def alike(first: tuple[Node, MediaInfo], second: tuple[Node, MediaInfo], seconds: float) -> bool:
    """Whether two files may be the same recording.

    Lengths must agree within ``seconds``; then either the titles (or plain file names) are the same, or both are
    long videos of one shape whose lengths agree to half a second.
    """
    one, two = first[1], second[1]
    apart = abs(one.duration - two.duration)
    if one.kind != two.kind or apart > seconds:
        return False
    name = _words(*first)
    if len(name) >= _MIN_NAME and name == _words(*second):
        return True
    return (one.kind == VIDEO and min(one.duration, two.duration) >= _LONG_VIDEO and apart <= _EXACT
            and _same_shape(one, two))


def group_media(files: list[tuple[Node, MediaInfo]], seconds: float,
                cancel: threading.Event | None = None) -> list[SimilarPhotoGroup]:
    """Groups around their first (shortest) file; a file joins the first group whose first file it is alike."""
    groups: list[SimilarPhotoGroup] = []
    for kind in (VIDEO, AUDIO):
        ordered = sorted((item for item in files if item[1].kind == kind), key=lambda item: item[1].duration)
        used: set[int] = set()
        for index, first in enumerate(ordered):
            check_cancel(cancel)
            give_way()
            if index in used:
                continue
            members, distances = [first[0]], [0]
            for other in range(index + 1, len(ordered)):
                apart = ordered[other][1].duration - first[1].duration
                if apart > seconds:
                    break
                if other not in used and alike(first, ordered[other], seconds):
                    used.add(other)
                    members.append(ordered[other][0])
                    distances.append(round(apart * 1000))
            if len(members) > 1:
                groups.append(SimilarPhotoGroup(members, distances))
    groups.sort(key=lambda group: -sum(node.size for node in group.files))
    return groups


def find_similar_media(root: Node, *, min_size: int = 1 << 20, seconds: int = DEFAULT_SECONDS,
                       cancel: threading.Event | None = None,
                       progress: MediaProgress | None = None) -> SimilarPhotoResult:
    """Read the headers of recorded audio and video files on a worker and group the candidates.

    Changed, linked and cloud files are refused, hard links are read once, and unreadable headers are counted.
    """
    if not 0 <= seconds <= MAX_SECONDS or min_size < 1:
        raise ValueError("unusable tolerance or size")
    files: list[tuple[Node, MediaInfo]] = []
    identities: set[tuple[int, int]] = set()
    skipped, limited = 0, False
    for node in root.iter_files():
        check_cancel(cancel)
        give_way()
        suffix = suffix_of(node.name)
        if node.size < min_size or suffix not in SUFFIXES:
            continue
        if len(files) == MAX_FILES:
            limited = True
            break
        identity = unpack_snapshot(node.snapshot).identity if node.snapshot is not None else (0, 0)
        if identity[1] and identity in identities:
            continue
        try:
            with opened(node) as stream:
                files.append((node, read_media(stream, node.size, suffix)))
        except (OSError, MediaError):
            skipped += 1
        else:
            identities.add(identity)
        if progress is not None:
            progress(len(files), skipped)
    return SimilarPhotoResult(group_media(files, seconds, cancel), len(files), skipped, seconds, {}, limited)
