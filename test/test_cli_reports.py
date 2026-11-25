"""Console reports are read-only JSON: usable conditions first, complete counts, and no way to act on them."""

import argparse
import json
import os
import subprocess
import sys
import threading

import pytest

from je_file_tree import cli, cli_reports
from je_file_tree.cli_reports import budget_argument, days_argument, depth_argument, size_argument
from je_file_tree.core.cleanup_policy import CleanupPolicy
from je_file_tree.core.custom_rules import CustomRule


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "資料"
    (root / "a" / "b").mkdir(parents=True)
    (root / "a" / "one.bin").write_bytes(b"x" * 3000)
    (root / "a" / "b" / "two.bin").write_bytes(b"x" * 3000)
    (root / "a" / "b" / "note.txt").write_bytes(b"hello")
    old = root / "plan.bak"
    old.write_bytes(b"old")
    os.utime(old, (1_600_000_000, 1_600_000_000))
    return root


def _run(capsys, *args):
    code = cli.main([str(arg) for arg in args])
    captured = capsys.readouterr()
    return code, [json.loads(line) for line in captured.out.splitlines()], captured.err


@pytest.mark.parametrize("text, value", [("0", 0), ("500", 500), ("10K", 10240), ("1.5k", 1536), ("2MiB", 2 << 20),
                                         ("1g", 1 << 30), (" 3 b", 3)])
def test_sizes(text, value):
    assert size_argument(text) == value


@pytest.mark.parametrize("parse, texts", [
    (size_argument, ["", "x", "-1", "1.5", "1Z", "nan", "inf", "9" * 30, "1e400", "K"]),
    (days_argument, ["", "0", "-2", "nan", "inf", "x", "99999999"]),
    (depth_argument, ["0", "-1", "1.0", "x", "²"]),
    (budget_argument, ["", "x", "=5", "path", "path=", "path=big"]),
])
def test_unusable_arguments_are_refused(parse, texts):
    for text in texts:
        with pytest.raises(argparse.ArgumentTypeError):
            parse(text)


def test_search(source, capsys):
    code, documents, _err = _run(capsys, "search", source, "--name", "*.bin", "--min-size", "2K", "--limit", "1")
    assert code == cli.OK and documents[0]["kind"] == "scan"
    found = documents[1]
    assert found["kind"] == "search" and found["count"] == 2 and found["listed"] == 1 and found["bytes"] == 6000
    assert found["complete"] and set(found["matches"][0]) == {"path", "folder", "bytes", "allocated_estimate_bytes",
                                                              "modified"}
    _code, documents, _err = _run(capsys, "search", source, "--name", r"^(one|two)\.bin$", "--regex",
                                  "--exclude-names", "two*", "--max-depth", "2", "--kind", "files")
    assert [os.path.basename(match["path"]) for match in documents[1]["matches"]] == ["one.bin"]


@pytest.mark.parametrize("args", [(), ("--name", "(a+)+", "--regex"), ("--name", " ; ")])
def test_search_conditions_are_checked_before_scanning(source, capsys, monkeypatch, args):
    monkeypatch.setattr(cli, "scan", lambda *_args, **_kwargs: pytest.fail("nothing is scanned"))
    code, documents, err = _run(capsys, "search", source, *args)
    assert code == cli.INVALID_ARGUMENTS and not documents and json.loads(err)["kind"] == "error"


def test_owner_searches_record_owners(source, capsys, monkeypatch):
    seen = []
    real = cli.scan
    monkeypatch.setattr(cli, "scan", lambda root, **kwargs: seen.append(kwargs["options"]) or real(root, **kwargs))
    _run(capsys, "search", source, "--owner", "nobody-at-all")
    _run(capsys, "search", source, "--name", "x")
    assert [options.windows_owners for options in seen] == [True, False]


def test_duplicates(source, capsys):
    code, documents, _err = _run(capsys, "duplicates", source, "--min-size", "1")
    found = documents[1]
    assert code == cli.OK and found["groups"] == 1 and found["extra_bytes"] == 3000 and found["listed"] == 1
    assert sorted(os.path.basename(path) for path in found["entries"][0]["paths"]) == ["one.bin", "two.bin"]
    assert _run(capsys, "duplicates", source)[1][1]["groups"] == 0  # under 1 MiB by default


def test_cleanup_lists_candidates_and_changes_nothing(source, capsys, tmp_path):
    before = sorted(path.name for path in source.rglob("*"))
    policy = tmp_path / "policy.json"
    policy.write_text(CleanupPolicy(custom=(CustomRule("Mine", files=("*.bak",)),)).dumps(), encoding="utf-8")
    code, documents, _err = _run(capsys, "cleanup", source, "--policy", policy)
    groups = {group["rule"]: group for group in documents[1]["groups"]}
    assert code == cli.OK and groups["custom:Mine"]["risk"] == "manual" and groups["custom:Mine"]["count"] == 1
    assert sorted(path.name for path in source.rglob("*")) == before
    policy.write_text("{}", encoding="utf-8")
    assert _run(capsys, "cleanup", source, "--policy", policy)[0] == cli.INVALID_ARGUMENTS
    assert _run(capsys, "cleanup", source, "--policy", tmp_path / "missing.json")[0] == cli.IO_ERROR


def test_budgets_tell_over_within_and_unknown_apart(source, capsys, tmp_path):
    code, documents, _err = _run(capsys, "budget", source, "--budget", f"{source / 'a'}=1K", "--budget", f"{source}=1M")
    rows = documents[1]["budgets"]
    assert code == cli_reports.OVER_BUDGET and documents[1]["over"]
    assert [(row["bytes"], row["over_by"]) for row in rows] == [(6005, 6005 - 1024), (6008, 0)]
    code, documents, _err = _run(capsys, "budget", source, "--budget", f"{source}=1M")
    assert code == cli.OK and not documents[1]["over"] and not documents[1]["unknown"]
    code, documents, _err = _run(capsys, "budget", source, "--budget", f"{source / 'gone'}=1M",
                                 "--budget", f"{tmp_path / 'elsewhere'}=1M")
    assert code == cli.INCOMPLETE and documents[1]["unknown"]
    assert [(row["bytes"], row["reason"], row["over_by"]) for row in documents[1]["budgets"]] == [
        (None, "missing", None), (None, "outside_scan", None)]


def test_incomplete_scans_say_so(source, capsys):
    code, documents, _err = _run(capsys, "search", source, "--name", "bin", "--exclude", "b")
    assert code == cli.INCOMPLETE and documents[1]["complete"] is False


@pytest.mark.parametrize("report, args", [("search", ("--name", "x")), ("duplicates", ()), ("cleanup", ())])
def test_a_stopped_report_prints_nothing_and_returns_130(source, capsys, monkeypatch, report, args):
    real = cli.scan

    def stop_after(root, **kwargs):
        result = real(root, **kwargs)
        kwargs["cancel"].set()
        return result
    monkeypatch.setattr(cli, "scan", stop_after)
    code, documents, _err = _run(capsys, report, source, *args)
    assert code == cli.INTERRUPTED and len(documents) == 1


def test_a_stopped_budget_returns_nothing(source):
    cancel = threading.Event()
    cancel.set()
    root = cli.scan(source).root
    args = argparse.Namespace(budget=[(str(source), 1)])
    assert cli_reports.report_budget(args, root, cli.coverage_of(root), cancel) == ({}, None)


def test_no_option_moves_or_deletes_and_qt_is_never_imported(source):
    help_text = ""
    for command in (*cli_reports.REPORTS, "scan"):
        shown = subprocess.run([sys.executable, "-m", "je_file_tree.cli", command, "--help"],  # noqa: S603
                               capture_output=True, text=True, encoding="utf-8", check=True).stdout.lower()
        help_text += shown
    assert not any(f"--{word}" in help_text for word in ("delete", "remove", "trash", "move", "clean", "apply", "fix"))
    code = ("from je_file_tree.cli import main; import sys; code = main(sys.argv[1:]); "
            "assert not any(m.startswith(('PySide6', 'je_file_tree.gui')) for m in sys.modules); sys.exit(code)")
    for args in (("search", "--name", "bin"), ("duplicates",), ("cleanup",), ("budget", "--budget", f"{source}=1G")):
        result = subprocess.run([sys.executable, "-c", code, args[0], str(source), *args[1:]],  # noqa: S603
                                capture_output=True, text=True, encoding="utf-8", check=False)
        assert result.returncode == 0, result.stderr
