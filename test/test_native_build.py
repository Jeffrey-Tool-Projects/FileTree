"""The optional native folder reader is really built and tested on Windows CI, from locked tooling.

The module is optional everywhere: a failed build leaves a working Python scanner and skips
``test_native_scan.py``. The Windows test jobs therefore build it and stop when it is not in use,
and the build backend they install is hash-locked like every other CI install.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

from packaging.requirements import Requirement  # pytest depends on packaging

_ROOT = Path(__file__).resolve().parents[1]
_LOCK = _ROOT / ".github" / "requirements" / "native.txt"
_INSTALL = "python -m pip install --require-hashes --only-binary :all: -r .github/requirements/native.txt"
_PIN = re.compile(r"^([A-Za-z0-9][\w.-]*)==(\S+)", re.MULTILINE)


def _pins(path: Path) -> dict[str, str]:
    return dict(_PIN.findall(path.read_text(encoding="utf-8")))


def _windows_steps() -> list[str]:
    """The steps of the Windows test matrix job, each starting at its ``name:`` or ``uses:``."""
    text = (_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
    job = re.search(r"^  windows:\n(.*?)(?=^  [A-Za-z0-9_-]+:\s*$|\Z)", text, re.MULTILINE | re.DOTALL)
    assert job is not None
    return re.split(r"^    - ", job.group(1), flags=re.MULTILINE)[1:]


def test_the_lock_holds_only_the_hashed_build_backend() -> None:
    text = _LOCK.read_text(encoding="utf-8")
    requirements = [line for line in text.splitlines() if line and not line.startswith(("#", " "))]
    assert [line.split("==")[0] for line in requirements] == ["setuptools"]
    assert len(re.findall(r"--hash=sha256:[0-9a-f]{64}", text)) >= 1


def test_the_locked_backend_satisfies_the_project_and_matches_the_release_lock() -> None:
    # Two setuptools versions would let the tested module differ from the one a release builds.
    pins = _pins(_LOCK)
    section = re.search(r"^requires\s*=\s*\[([^\]]*)\]", (_ROOT / "pyproject.toml").read_text(encoding="utf-8"),
                        re.MULTILINE)
    assert section is not None
    for item in re.findall(r"[\"']([^\"']+)[\"']", section.group(1)):
        requirement = Requirement(item)
        assert requirement.specifier.contains(pins[requirement.name])
    assert pins["setuptools"] == _pins(_LOCK.with_name("publish.txt"))["setuptools"]


def test_windows_jobs_build_and_require_the_reader_before_the_tests() -> None:
    steps = _windows_steps()
    names = [step.splitlines()[0] for step in steps]
    install = next(index for index, step in enumerate(steps) if _INSTALL in step)
    build = next(index for index, step in enumerate(steps) if "python setup.py build_ext --inplace" in step)
    require = next(index for index, step in enumerate(steps) if "python -m tools.require_native_reader" in step)
    tests = names.index("name: Run tests")
    assert install < build < require < tests
    # A step that may fail without failing the job would hide a module that was never built.
    assert all("continue-on-error" not in steps[index] for index in (install, build, require))


def test_the_source_distribution_carries_the_native_source() -> None:
    # setup.py declares the extension on Windows only and the release sdist is built on Linux.
    lines = (_ROOT / "MANIFEST.in").read_text(encoding="utf-8").splitlines()
    assert "include je_file_tree/_native.cpp" in lines
    assert (_ROOT / "je_file_tree" / "_native.cpp").is_file()


def test_the_requirement_tool_fails_when_the_scanner_would_read_in_python(capsys) -> None:
    # conftest keeps every other test module on the Python reader, which is exactly this case.
    tool = importlib.import_module("tools.require_native_reader")
    assert tool.main() == 1
    assert capsys.readouterr().err
