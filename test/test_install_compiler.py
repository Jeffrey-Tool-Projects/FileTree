"""Compiler installation preserves the existing wheel/hash restrictions and fails visibly."""

import subprocess
import sys
from unittest.mock import Mock

import pytest

from tools import install_compiler as compiler


def test_shared_compiler_installs_from_current_interpreter_without_credentials(monkeypatch):
    run = Mock()
    monkeypatch.setattr(compiler.subprocess, "run", run)
    compiler.install()
    commands = [call.args[0] for call in run.call_args_list]
    assert len(commands) == 5
    assert all(command[:4] == [sys.executable, "-m", "pip", "install"] for command in commands)
    assert all("--only-binary" in command and ":all:" in command for command in commands)
    assert all(call.kwargs["check"] and call.kwargs["timeout"] == 900 for call in run.call_args_list)
    source = [command for command in commands if "--no-binary" in command]
    assert len(source) == 1 and source[0][source[0].index("--no-binary") + 1] == "nuitka"
    assert "--no-build-isolation" in source[0] and "--no-deps" in source[0] and source[0] == commands[-1]
    assert all("--require-hashes" in command for command in commands)
    assert [command[-1] for command in commands] == [
        f".github/requirements/{name}.txt" for name in ("compiler", "reports", "archives", "photos", "nuitka")]


def test_the_locks_hold_the_backend_the_compiler_is_built_with():
    folder = compiler._ROOT / ".github" / "requirements"
    locked = (folder / "compiler.txt").read_text(encoding="utf-8")
    for name in ("pip", "setuptools", "wheel", "pyside6", "ordered-set", "zstandard"):
        assert f"\n{name}==" in locked
    assert all("--hash=sha256:" in block for block in locked.split("==")[1:])
    native = (folder / "native.txt").read_text(encoding="utf-8")
    setuptools = next(line for line in locked.splitlines() if line.startswith("setuptools=="))
    assert setuptools in native, "the native reader and Nuitka are built with one setuptools"
    assert "nuitka==4.2.2" in (folder / "nuitka.txt").read_text(encoding="utf-8")


def test_failed_install_stops_before_other_tools(monkeypatch):
    run = Mock(side_effect=subprocess.CalledProcessError(1, "pip"))
    monkeypatch.setattr(compiler.subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        compiler.install()
    assert run.call_count == 1
