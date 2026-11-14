"""Check the Windows wheel of a release: it must carry the native folder reader, and the reader must work.

    python tools/check_native_wheel.py dist --version 0.3.0

``setup.py`` declares the module optional, so a compile that fails still leaves a wheel, only without
the module. Before the release keeps the wheel for PyPI, this tool requires that the folder holds
exactly one wheel, named for this version with the stable-ABI Windows tag, that it contains the built
module and not its source, and that the module is in use after installing the wheel into a new virtual
environment (nothing is downloaded: ``--no-index --no-deps``). The environment is made in a new
temporary folder and removed with it.
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404 - this interpreter and the one of the new environment, no shell
import sys
import tempfile
import zipfile
from pathlib import Path

TAG = "cp311-abi3-win_amd64"
MODULE = "je_file_tree/_native.pyd"
_PROBE = ("import sys; from je_file_tree.core import native_scan; "
          "sys.exit(0 if native_scan.reader() is not None else 1)")
_TIMEOUT = 300


def wheel_problems(folder: Path, version: str) -> list[str]:
    """What is wrong with the wheel in ``folder``, without installing it; empty when nothing is."""
    wheels = sorted(folder.glob("*.whl"))
    expected = f"je_file_tree-{version}-{TAG}.whl"
    if [wheel.name for wheel in wheels] != [expected]:
        return [f"expected exactly {expected}, found {[wheel.name for wheel in wheels]}"]
    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()
        problems = []
        if MODULE not in names or archive.getinfo(MODULE).file_size == 0:
            problems.append(f"{MODULE} is missing: the compile failed and was skipped")
        sources = [name for name in names if name.endswith(".cpp")]
        if sources:
            problems.append(f"the wheel carries source files: {sources}")
    return problems


def reader_in_use(wheel: Path) -> bool:
    """Whether the scanner uses the native reader after installing ``wheel`` into a new environment."""
    with tempfile.TemporaryDirectory() as scratch:
        environment = Path(scratch) / "environment"
        python = environment / "Scripts" / "python.exe"
        commands = [
            [sys.executable, "-m", "venv", str(environment)],
            [str(python), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel.resolve())],
            [str(python), "-I", "-c", _PROBE],
        ]
        for command in commands:
            # cwd is the scratch folder so the installed package is imported, not this checkout.
            done = subprocess.run(command, cwd=scratch, check=False, timeout=_TIMEOUT)  # noqa: S603 # nosec B603
            if done.returncode != 0:
                return False
    return True


def main(argv: list[str] | None = None) -> int:
    """Return 0 when the wheel may be published, 1 after naming what is wrong."""
    parser = argparse.ArgumentParser(description="Check the Windows wheel of a FileTree release.")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--version", required=True)
    options = parser.parse_args(argv)
    problems = wheel_problems(options.folder, options.version)
    if not problems and not reader_in_use(next(options.folder.glob("*.whl"))):
        problems.append("the installed wheel does not use the native folder reader")
    for problem in problems:
        sys.stderr.write(problem + "\n")
    if not problems:
        sys.stdout.write(f"The {TAG} wheel carries a working native folder reader.\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
