"""The optional native folder reader is really built and tested on Windows CI, from locked tooling.

The module is optional everywhere: a failed build leaves a working Python scanner and skips
``test_native_scan.py``. The Windows test jobs therefore build it and stop when it is not in use,
and the build backend they install is hash-locked like every other CI install.
"""

from __future__ import annotations

import importlib
import re
import zipfile
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
    assert tool.main([]) == 1
    assert capsys.readouterr().err


def _job(workflow: str, name: str) -> str:
    text = (_ROOT / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
    job = re.search(rf"^  {re.escape(name)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:\s*$|\Z)", text, re.MULTILINE | re.DOTALL)
    assert job is not None, name
    return job.group(1)


def _in_order(body: str, *parts: str) -> None:
    places = [body.index(part) for part in parts]
    assert places == sorted(places), parts


def test_compiled_programs_build_require_and_then_carry_the_reader() -> None:
    # Nuitka copies a built module and says nothing when there is none.
    for workflow, job in (("release.yml", "build-exe"), ("build.yml", "windows")):
        body = _job(workflow, job)
        _in_order(body, "tools/install_compiler.py", _INSTALL, "python setup.py build_ext --inplace",
                  "python -m tools.require_native_reader\n", "python tools/build_nuitka.py",
                  "python -m tools.require_native_reader --compiled build/standalone/start_file_tree.dist",
                  "tools/package_standalone.py")
        assert "continue-on-error" not in body


def test_the_release_builds_checks_and_uploads_the_windows_wheel_without_the_token() -> None:
    body = _job("release.yml", "build-windows-wheel")
    assert "needs: release" in body and "runs-on: windows-latest" in body
    assert "ref: v${{ needs.release.outputs.new }}" in body and "persist-credentials: false" in body
    _in_order(body, _INSTALL, "python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist",
              'python tools/check_native_wheel.py dist --version "$env:NEW"', "name: pypi-dist-windows")
    assert "secrets." not in body and "id-token" not in body and "contents: write" not in body
    assert "continue-on-error" not in body and "if-no-files-found: error" in body
    publisher = _job("release.yml", "publish-pypi")
    _in_order(publisher, "name: pypi-dist\n", "name: pypi-dist-windows\n", "python -m twine upload dist/*")
    # The GitHub release keeps listing the producer's two files (tools/publish_release.py).
    assert "pypi-dist-windows" not in _job("release.yml", "publish-release")


def test_the_wheel_check_names_a_wrong_tag_a_missing_module_and_shipped_source(tmp_path) -> None:
    tool = importlib.import_module("tools.check_native_wheel")
    assert tool.wheel_problems(tmp_path, "1.2.3")  # no wheel at all
    pure = tmp_path / "je_file_tree-1.2.3-py3-none-any.whl"
    zipfile.ZipFile(pure, "w").close()
    assert "expected exactly" in tool.wheel_problems(tmp_path, "1.2.3")[0]
    pure.unlink()
    wheel = tmp_path / f"je_file_tree-1.2.3-{tool.TAG}.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("je_file_tree/__init__.py", "")
        archive.writestr("je_file_tree/_native.cpp", "// source")
    problems = tool.wheel_problems(tmp_path, "1.2.3")
    assert len(problems) == 2 and "missing" in problems[0] and "source" in problems[1]
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(tool.MODULE, b"built")
    assert tool.wheel_problems(tmp_path, "1.2.3") == []
    assert tool.wheel_problems(tmp_path, "1.2.4") != []
    assert tool.main([str(tmp_path / "empty"), "--version", "1.2.3"]) == 1


def test_the_compiled_folder_check_names_what_is_missing(tmp_path, capsys) -> None:
    tool = importlib.import_module("tools.require_native_reader")
    assert tool.main(["--compiled", str(tmp_path)]) == 1
    assert "_native.pyd" in capsys.readouterr().err
    (tmp_path / "je_file_tree").mkdir()
    (tmp_path / "je_file_tree" / "_native.pyd").write_bytes(b"module")
    (tmp_path / "python3.dll").write_bytes(b"")
    assert tool.missing_from(tmp_path) == ["python3.dll"]  # an empty file is not the library
    (tmp_path / "python3.dll").write_bytes(b"library")
    assert tool.main(["--compiled", str(tmp_path)]) == 0
