"""Free-space forecast math on synthetic series, and the bounded observation store (all under tmp_path)."""

from __future__ import annotations

import json
import os
import random
from pathlib import Path

import pytest

from je_file_tree.core import forecast as fc
from je_file_tree.core.forecast import Forecast, ForecastState, ForecastStore, Sample, forecast, recent_series, thin

GIB = 1024 ** 3
DAY = fc.DAY
NOW = 1_800_000_000.0


def _series(days: float, per_day: float, *, start_used: int = 50 * GIB, total: int = 100 * GIB,
            every_hours: float = 6, noise: int = 0, seed: int = 7) -> list[Sample]:
    """Samples ending at NOW, ``every_hours`` apart, growing ``per_day`` bytes a day."""
    rng = random.Random(seed)  # noqa: S311 - reproducible synthetic noise
    count = int(days * 24 / every_hours) + 1
    samples = []
    for index in range(count):
        when = NOW - (count - 1 - index) * every_hours * 3600
        elapsed = (when - (NOW - days * DAY)) / DAY
        used = start_used + round(per_day * elapsed) + (rng.randint(-noise, noise) if noise else 0)
        samples.append(Sample(when, max(0, min(total, used)), total))
    return samples


def test_linear_growth_gives_rate_and_full_date():
    samples = _series(10, GIB)
    result = forecast(samples, NOW)
    assert result.state is ForecastState.GROWING
    assert result.bytes_per_day == pytest.approx(GIB, rel=1e-3)
    newest = samples[-1]
    assert result.full_at == pytest.approx(NOW + (newest.total - newest.used) / GIB * DAY, rel=1e-6)
    assert result.samples == len(samples) and result.span_days == pytest.approx(10, abs=0.01)
    assert not result.not_soon


def test_noise_and_a_single_outlier_do_not_move_the_rate_much():
    samples = _series(20, 2 * GIB, noise=GIB // 2)
    spike = samples[len(samples) // 2]
    samples[len(samples) // 2] = Sample(spike.when, spike.used + 30 * GIB, spike.total)
    result = forecast(samples, NOW)
    assert result.state is ForecastState.GROWING
    assert result.bytes_per_day == pytest.approx(2 * GIB, rel=0.05)


def test_shrinking_and_flat_volumes_are_not_growing():
    shrinking = forecast(_series(10, -GIB), NOW)
    assert shrinking.state is ForecastState.STABLE_OR_SHRINKING
    assert shrinking.bytes_per_day < 0 and shrinking.full_at is None
    flat = forecast(_series(10, 0), NOW)
    assert flat.state is ForecastState.STABLE_OR_SHRINKING and flat.full_at is None
    tiny = forecast(_series(10, fc.GROWTH_FLOOR / 2), NOW)
    assert tiny.state is ForecastState.STABLE_OR_SHRINKING


def test_a_resize_starts_a_new_series():
    before = [Sample(sample.when - 10 * DAY, sample.used, sample.total) for sample in _series(9, 5 * GIB)]
    after = _series(5, 0, start_used=40 * GIB, total=200 * GIB)
    result = forecast(before + after, NOW)
    assert result.state is ForecastState.STABLE_OR_SHRINKING
    assert result.samples == len(after)
    assert all(sample.total == 200 * GIB for sample in recent_series(before + after, NOW))
    just_resized = forecast(before + after[-2:], NOW)
    assert just_resized.state is ForecastState.NOT_ENOUGH_DATA and just_resized.samples == 2


def test_small_total_changes_are_not_a_resize():
    samples = [Sample(sample.when, sample.used, sample.total + (index % 3) * 1024 * 1024)
               for index, sample in enumerate(_series(10, GIB))]
    assert forecast(samples, NOW).samples == len(samples)


@pytest.mark.parametrize("samples", [
    [],
    [Sample(NOW, GIB, 10 * GIB)],
    [Sample(NOW - 3 * DAY, GIB, 10 * GIB), Sample(NOW, 2 * GIB, 10 * GIB)],
    _series(1, GIB),
])
def test_too_little_history_is_reported(samples):
    result = forecast(samples, NOW)
    assert result.state is ForecastState.NOT_ENOUGH_DATA
    assert result.full_at is None and result.bytes_per_day == 0.0


def test_a_far_full_date_is_capped_as_not_soon():
    result = forecast(_series(10, 4 * 1024 * 1024, start_used=GIB, total=10_000 * GIB), NOW)
    assert result.state is ForecastState.GROWING and result.full_at is None and result.not_soon


def test_window_future_samples_and_full_volume():
    old = [Sample(NOW - 90 * DAY + index * DAY, 10 * GIB + index * 100 * GIB // 1000, 100 * GIB)
           for index in range(20)]
    recent = _series(10, GIB)
    assert forecast(old + recent, NOW).samples == len(recent)
    future = [Sample(NOW + DAY, 99 * GIB, 100 * GIB)]
    assert forecast(recent + future, NOW) == forecast(recent, NOW)
    full = _series(5, GIB, start_used=100 * GIB - 5 * GIB)
    result = forecast(full, NOW)
    assert result.full_at == pytest.approx(full[-1].when)


def test_forecast_is_deterministic():
    samples = _series(15, GIB, noise=GIB // 4)
    assert forecast(samples, NOW) == forecast(list(reversed(samples)), NOW)
    assert isinstance(forecast(samples, NOW), Forecast)


def test_thinning_keeps_recent_dense_and_bounds_the_count():
    samples = [Sample(float(index + 1), index, 1000) for index in range(401)]
    kept = thin(samples, 400)
    assert len(kept) == 301 and kept[-201:] == tuple(samples[-201:])
    assert kept[:100] == tuple(samples[:200:2])
    assert kept[0] == samples[0] and kept[-1] == samples[-1]
    assert list(kept) == sorted(kept, key=lambda sample: sample.when)
    assert len(thin(samples[:3], 2)) == 2 and thin(samples[:3], 2)[-1] == samples[2]
    assert thin(samples[:5], 10) == tuple(samples[:5])


def _store(tmp_path: Path, **options) -> ForecastStore:
    return ForecastStore(tmp_path / "app" / "forecast" / "volumes.json", **options)


def test_record_writes_a_versioned_file_and_respects_the_interval(tmp_path):
    store = _store(tmp_path)
    outcome = store.record([("C", Sample(NOW, GIB, 10 * GIB))])
    assert outcome.error is None and not outcome.newer
    document = json.loads(store.path.read_text(encoding="utf-8"))
    assert document["format"] == fc.FORMAT and document["version"] == fc.VERSION
    assert document["volumes"] == {"C": [[NOW, GIB, 10 * GIB]]}
    store.record([("C", Sample(NOW + fc.MIN_INTERVAL - 1, 2 * GIB, 10 * GIB))])
    assert len(store.load()[0]["C"]) == 1
    outcome = store.record([("C", Sample(NOW + fc.MIN_INTERVAL, 2 * GIB, 10 * GIB))])
    assert [sample.used for sample in outcome.volumes["C"]] == [GIB, 2 * GIB]
    assert store.load()[0] == dict(outcome.volumes)
    assert sorted(path.name for path in store.path.parent.iterdir()) == ["volumes.json"]


def test_store_bounds_samples_and_volumes(tmp_path):
    store = _store(tmp_path, min_interval=0, max_samples=10, max_volumes=3)
    for index in range(30):
        store.record([("C", Sample(NOW + index, index, 1000))])
    kept = store.load()[0]["C"]
    assert len(kept) <= 10 and kept[-1].used == 29 and kept[0].used == 0
    for index, key in enumerate("DEFG"):
        store.record([(key, Sample(NOW + 100 + index, 1, 1000))])
    assert sorted(store.load()[0]) == ["E", "F", "G"]


def test_a_clock_set_back_drops_later_samples_of_that_volume(tmp_path):
    store = _store(tmp_path)
    store.record([("C", Sample(NOW, GIB, 10 * GIB)), ("D", Sample(NOW, GIB, 10 * GIB))])
    outcome = store.record([("C", Sample(NOW - 10 * DAY, 3 * GIB, 10 * GIB))])
    assert [sample.used for sample in outcome.volumes["C"]] == [3 * GIB]
    assert len(outcome.volumes["D"]) == 1


@pytest.mark.parametrize("content", [b"{not json", b"\xff\xfe\x00", b"[]", b'{"format": "other", "version": 1}',
                                     b'{"format": "file-tree-forecast", "version": 0, "volumes": {}}',
                                     b'{"format": "file-tree-forecast", "version": 1, "volumes": []}'])
def test_a_corrupt_file_reads_as_empty_and_is_replaced(tmp_path, content):
    store = _store(tmp_path)
    store.path.parent.mkdir(parents=True)
    store.path.write_bytes(content)
    assert store.load() == ({}, True)
    outcome = store.record([("C", Sample(NOW, GIB, 10 * GIB))])
    assert outcome.error is None and len(store.load()[0]["C"]) == 1


def test_invalid_samples_are_skipped_individually(tmp_path):
    store = _store(tmp_path)
    store.path.parent.mkdir(parents=True)
    store.path.write_text(json.dumps({"format": fc.FORMAT, "version": 1, "volumes": {
        "C": [[NOW, 1, 10], [NOW, 11, 10], [NOW, -1, 10], [0, 1, 10], [NOW, 1.5, 10], [NOW, True, 10], [NOW, 1],
              "x", [NOW + 1, 2, 10]],
        "D": "nope", "E": []}}), encoding="utf-8")
    volumes, writable = store.load()
    assert writable and list(volumes) == ["C"]
    assert [sample.used for sample in volumes["C"]] == [1, 2]


def test_a_newer_format_is_left_untouched(tmp_path):
    store = _store(tmp_path)
    store.path.parent.mkdir(parents=True)
    original = json.dumps({"format": fc.FORMAT, "version": fc.VERSION + 1, "volumes": {}}).encode()
    store.path.write_bytes(original)
    outcome = store.record([("C", Sample(NOW, GIB, 10 * GIB))])
    assert outcome.newer and outcome.volumes["C"][0].used == GIB
    assert store.path.read_bytes() == original


def test_an_oversized_file_is_not_read(tmp_path, monkeypatch):
    store = _store(tmp_path)
    store.record([("C", Sample(NOW, GIB, 10 * GIB))])
    monkeypatch.setattr(fc, "MAX_FILE_BYTES", 10)
    assert store.load() == ({}, True)


def test_a_failed_write_keeps_the_previous_file_and_leaves_no_temporary(tmp_path, monkeypatch):
    store = _store(tmp_path)
    store.record([("C", Sample(NOW, GIB, 10 * GIB))])
    before = store.path.read_bytes()
    def refuse(_source, _target):
        raise PermissionError(13, "denied")
    monkeypatch.setattr(fc.os, "replace", refuse)
    outcome = store.record([("C", Sample(NOW + DAY, 2 * GIB, 10 * GIB))])
    assert outcome.error == "denied" and len(outcome.volumes["C"]) == 2
    assert store.path.read_bytes() == before
    assert sorted(os.listdir(store.path.parent)) == ["volumes.json"]


def test_an_unwritable_location_is_reported_not_raised(tmp_path):
    blocker = tmp_path / "app"
    blocker.write_text("a file where the folder should be", encoding="utf-8")
    outcome = _store(tmp_path).record([("C", Sample(NOW, GIB, 10 * GIB))])
    assert outcome.error and outcome.volumes["C"][0].used == GIB
    assert blocker.read_text(encoding="utf-8") == "a file where the folder should be"
