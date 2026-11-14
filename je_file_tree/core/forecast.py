"""Per-volume used-space observations and a robust free-space forecast.

The store is one small application-owned JSON file: per volume identity, timestamped ``(used, total)``
samples, at most one every few hours and a bounded count, the oldest thinned first. A corrupt or unreadable
file is treated as empty and replaced; a file saved by a newer format version is left untouched. Nothing
outside that one file (and its temporary sibling) is ever written or removed.

The forecast is pure: it takes the samples and the current time and returns the recent growth rate
(Theil–Sen median of pairwise slopes, which ignores single outliers such as a download deleted the next
day) and the date at which that rate would reach the total size.
"""

from __future__ import annotations

import json
import math
import os
import statistics
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

FORMAT = "file-tree-forecast"
VERSION = 1
DAY = 86400.0
MIN_INTERVAL = 3 * 3600.0
"""Seconds between two recorded samples of one volume; more frequent readings are not stored."""
MAX_SAMPLES = 400
"""Samples kept per volume; beyond it the older half is thinned to every second sample."""
MAX_VOLUMES = 256
"""Volume identities kept; the ones observed longest ago are dropped first."""
MAX_FILE_BYTES = 8 * 1024 * 1024
"""A larger file is not read (treated as corrupt); a full store is about 256 × 400 × 40 bytes ≈ 4 MiB."""
WINDOW_DAYS = 30.0
"""The forecast uses the samples of the last 30 days before the newest one."""
MIN_SAMPLES = 3
MIN_SPAN_DAYS = 2.0
"""Fewer samples, or a shorter span, is "not enough history yet"."""
HORIZON_DAYS = 5 * 365.0
"""A volume that would fill later than this is reported as "not soon" rather than with an absurd date."""
GROWTH_FLOOR = 1024 * 1024
"""Bytes per day below which a volume counts as not growing."""
RESIZE_TOLERANCE = 0.01
"""A total that changes by more than 1 % starts a new series (the volume was resized or replaced)."""
MAX_FIT = 80
"""Samples entering the pairwise fit (evenly chosen); 80 samples are 3,160 pairs.

Measured 2026-11-14 on the development machine (Windows, CPython 3.14): 256 volumes with 400 in-window
samples each forecast in 0.48 s in total with this cap; without it (79,800 pairs per volume) the same run took
10.4 s. A typical store has a few volumes of a few dozen samples.
"""
_SAMPLE_FIELDS = 3


class ForecastState(Enum):
    """How much a forecast can say."""

    NOT_ENOUGH_DATA = "not_enough_data"
    STABLE_OR_SHRINKING = "stable_or_shrinking"
    GROWING = "growing"


@dataclass(frozen=True, slots=True)
class Sample:
    """One observation of a volume: POSIX time, used bytes and total bytes."""

    when: float
    used: int
    total: int


@dataclass(frozen=True, slots=True)
class Forecast:
    """The recent growth of one volume.

    ``bytes_per_day`` is the robust recent rate (negative when shrinking, 0 without enough data);
    ``full_at`` is the estimated POSIX time the volume is full, or None when it is not growing or would
    fill only beyond ``HORIZON_DAYS``. ``samples`` and ``span_days`` describe the data the estimate used.
    """

    state: ForecastState
    bytes_per_day: float
    full_at: float | None
    samples: int
    span_days: float

    @property
    def not_soon(self) -> bool:
        """Growing, but too slowly to fill within the forecast horizon."""
        return self.state is ForecastState.GROWING and self.full_at is None


def _same_total(first: int, second: int) -> bool:
    return abs(first - second) <= RESIZE_TOLERANCE * max(first, second)


def _current_series(samples: Sequence[Sample]) -> list[Sample]:
    """The newest run of samples whose total matches the newest total, in time order."""
    ordered = sorted(samples, key=lambda sample: sample.when)
    if not ordered:
        return []
    newest = ordered[-1].total
    start = len(ordered) - 1
    while start > 0 and _same_total(ordered[start - 1].total, newest):
        start -= 1
    return ordered[start:]


def _evenly(samples: list[Sample], limit: int) -> list[Sample]:
    if len(samples) <= limit:
        return samples
    step = (len(samples) - 1) / (limit - 1)
    return [samples[round(index * step)] for index in range(limit)]


def _theil_sen(samples: Sequence[Sample]) -> float | None:
    """Median pairwise slope in bytes per second (None when every sample has the same time)."""
    slopes = [(later.used - earlier.used) / (later.when - earlier.when)
              for index, earlier in enumerate(samples) for later in samples[index + 1:]
              if later.when > earlier.when]
    return statistics.median(slopes) if slopes else None


def forecast(samples: Sequence[Sample], now: float) -> Forecast:
    """Forecast one volume from its samples; ``now`` is the caller's clock (POSIX seconds).

    Only the newest series with an unchanged total is used, limited to the ``WINDOW_DAYS`` before the newest
    sample. The full date is extrapolated from the newest observation at the fitted rate.
    """
    series = _current_series([sample for sample in samples if sample.when <= now])
    if series:
        cutoff = series[-1].when - WINDOW_DAYS * DAY
        series = [sample for sample in series if sample.when >= cutoff]
    span = (series[-1].when - series[0].when) / DAY if series else 0.0
    if len(series) < MIN_SAMPLES or span < MIN_SPAN_DAYS:
        return Forecast(ForecastState.NOT_ENOUGH_DATA, 0.0, None, len(series), span)
    slope = _theil_sen(_evenly(series, MAX_FIT))
    if slope is None or not math.isfinite(slope):
        return Forecast(ForecastState.NOT_ENOUGH_DATA, 0.0, None, len(series), span)
    per_day = slope * DAY
    if per_day < GROWTH_FLOOR:
        return Forecast(ForecastState.STABLE_OR_SHRINKING, per_day, None, len(series), span)
    newest = series[-1]
    full_at = newest.when + max(0, newest.total - newest.used) / slope
    if full_at - now > HORIZON_DAYS * DAY:
        return Forecast(ForecastState.GROWING, per_day, None, len(series), span)
    return Forecast(ForecastState.GROWING, per_day, max(full_at, newest.when), len(series), span)


def recent_series(samples: Sequence[Sample], now: float) -> tuple[Sample, ...]:
    """The samples a forecast at ``now`` would look at, oldest first (for a small used-space chart)."""
    series = _current_series([sample for sample in samples if sample.when <= now])
    if not series:
        return ()
    cutoff = series[-1].when - WINDOW_DAYS * DAY
    return tuple(sample for sample in series if sample.when >= cutoff)


def thin(samples: Sequence[Sample], limit: int = MAX_SAMPLES) -> tuple[Sample, ...]:
    """Keep at most ``limit`` samples: the older half drops every second sample until they fit.

    Recent samples stay dense and older ones become progressively sparser; a store at the cap shrinks
    to about three quarters of it, so thinning happens once per many recordings rather than every time.
    """
    kept = sorted(samples, key=lambda sample: sample.when)
    while len(kept) > limit:
        half = len(kept) // 2
        thinned = kept[:half:2] + kept[half:]
        kept = thinned if len(thinned) < len(kept) else kept[len(kept) - limit:]
    return tuple(kept)


@dataclass(frozen=True, slots=True)
class RecordOutcome:
    """The volumes after recording, and why nothing was saved (``error``) or may not be (``newer``)."""

    volumes: Mapping[str, tuple[Sample, ...]]
    error: str | None = None
    newer: bool = False


def _sample(value: Any) -> Sample | None:
    if not isinstance(value, list) or len(value) != _SAMPLE_FIELDS:
        return None
    when, used, total = value
    numbers = all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value)
    if not numbers or not isinstance(used, int) or not isinstance(total, int) or not math.isfinite(when):
        return None
    if when <= 0 or total <= 0 or not 0 <= used <= total:
        return None
    return Sample(float(when), used, total)


def _parse(document: Any) -> dict[str, tuple[Sample, ...]] | None:
    """Volumes of a document of this format, or None when it is not one."""
    if not isinstance(document, dict) or document.get("format") != FORMAT:
        return None
    volumes = document.get("volumes")
    if not isinstance(volumes, dict):
        return None
    result: dict[str, tuple[Sample, ...]] = {}
    for key, values in volumes.items():
        if not isinstance(key, str) or not isinstance(values, list):
            continue
        samples = [sample for sample in map(_sample, values) if sample is not None]
        if samples:
            result[key] = thin(samples)
    return result


class ForecastStore:
    """The observation file at ``path`` (application-owned; created with its folder on first save)."""

    def __init__(self, path: Path, *, min_interval: float = MIN_INTERVAL, max_samples: int = MAX_SAMPLES,
                 max_volumes: int = MAX_VOLUMES) -> None:
        self.path = Path(path)
        self.min_interval = min_interval
        self.max_samples = max_samples
        self.max_volumes = max_volumes

    def load(self) -> tuple[dict[str, tuple[Sample, ...]], bool]:
        """The stored volumes and whether this version may replace the file.

        A missing, unreadable, oversized or corrupt file reads as empty and may be replaced; a file of a newer
        format version reads as empty and is kept as it is.
        """
        try:
            if self.path.stat().st_size > MAX_FILE_BYTES:
                return {}, True
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError, RecursionError):
            return {}, True
        version = document.get("version") if isinstance(document, dict) else None
        if isinstance(version, int) and not isinstance(version, bool) and version > VERSION:
            return {}, False
        if version != VERSION:
            return {}, True
        return _parse(document) or {}, True

    def record(self, observations: Iterable[tuple[str, Sample]]) -> RecordOutcome:
        """Add each observation unless its volume has a sample within ``min_interval``, then save atomically.

        Samples dated after the new observation (a clock set back) are dropped from that volume. A save that
        fails leaves the previous file in place and reports its reason; the returned volumes include the new
        observations either way, so the caller can still forecast from them.
        """
        volumes, writable = self.load()
        changed = False
        for key, sample in observations:
            history = [old for old in volumes.get(key, ()) if old.when <= sample.when]
            if history and sample.when - history[-1].when < self.min_interval:
                continue
            volumes[key] = thin([*history, sample], self.max_samples)
            changed = True
        if len(volumes) > self.max_volumes:
            newest = sorted(volumes, key=lambda key: volumes[key][-1].when, reverse=True)
            volumes = {key: volumes[key] for key in newest[:self.max_volumes]}
        if not writable:
            return RecordOutcome(volumes, newer=True)
        if not changed:
            return RecordOutcome(volumes)
        try:
            self._save(volumes)
        except OSError as error:
            return RecordOutcome(volumes, error=error.strerror or str(error))
        return RecordOutcome(volumes)

    def _save(self, volumes: Mapping[str, Sequence[Sample]]) -> None:
        document = {"format": FORMAT, "version": VERSION,
                    "volumes": {key: [[sample.when, sample.used, sample.total] for sample in samples]
                                for key, samples in volumes.items()}}
        text = json.dumps(document, ensure_ascii=False, separators=(",", ":"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(prefix=".forecast-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise
