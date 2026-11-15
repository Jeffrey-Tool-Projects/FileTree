"""The quicker forms used after a scan give exactly what the plain forms give."""

import os
import random
from datetime import UTC, datetime

import pytest

from je_file_tree.core import export
from je_file_tree.core.scanner import scan
from je_file_tree.core.snapshot import NO_FILE_NUMBER, link_identity, pack_snapshot, unpack_snapshot


def _plain_iso_time(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).astimezone().isoformat(timespec="seconds")


def test_local_time_text_equals_the_datetime_form():
    chosen = random.Random(20261115)  # noqa: S311 - made-up sample times, not a secret
    samples = [chosen.uniform(86400 * 366, 4_000_000_000) for _ in range(20_000)]
    samples += [1_700_000_000, 1_700_000_000.9999996, 1_700_000_000.4999995, 86400 * 400 + 0.5, 1_711_846_800.25]
    assert [export._iso_time(value) for value in samples] == [_plain_iso_time(value) for value in samples]


@pytest.mark.parametrize("value", [0, -1.0, float("inf"), float("nan"), 1e30])
def test_unusable_times_stay_empty(value):
    assert export._iso_time(value) == ""


def test_link_identity_reads_the_same_fields_as_the_whole_snapshot(tmp_path):
    (tmp_path / "one").write_bytes(b"1")
    os.link(tmp_path / "one", tmp_path / "two")
    for path in (tmp_path, tmp_path / "one"):
        for file_times in (False, True):
            packed = pack_snapshot(os.lstat(path), file_times=file_times)
            whole = unpack_snapshot(packed)
            device, number, links = link_identity(packed)
            assert (device, int.from_bytes(number, "little"), links) == (whole.device, whole.inode, whole.links)
            assert (number == NO_FILE_NUMBER) == (whole.inode == 0)
    assert link_identity(pack_snapshot(os.lstat(tmp_path / "one")))[2] == 2
    with pytest.raises(ValueError):
        link_identity(b"short")


def test_saved_folders_mark_only_a_virtual_root(tmp_path):
    (tmp_path / "inner").mkdir()
    root = scan(tmp_path).root
    text = "".join(export._folder_json(root, None))
    assert '"virtual"' not in text and '"name": "inner"' in text
    root.name = ""  # what a root over several scanned folders looks like
    assert root.path is None and '"virtual": true' in "".join(export._folder_json(root, None))
