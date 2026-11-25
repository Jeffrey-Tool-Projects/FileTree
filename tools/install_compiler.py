"""Install the shared pinned desktop compiler/runtime tools without release credentials."""

from __future__ import annotations

from pathlib import Path
import subprocess  # nosec B404 - fixed pip arguments through this interpreter
import sys

_ROOT = Path(__file__).resolve().parents[1]
_LOCKED = ("--require-hashes", "--only-binary", ":all:")
_INSTALLS = (
    *((*_LOCKED, "-r", f".github/requirements/{name}.txt") for name in ("compiler", "reports", "archives", "photos")),
    # Nuitka is an sdist: built with the locked setuptools and wheel just installed, never with whatever is newest.
    (*_LOCKED, "--no-binary", "nuitka", "--no-build-isolation", "--no-deps", "-r", ".github/requirements/nuitka.txt"),
)


def install() -> None:
    """Install wheels at locked hashes only; Nuitka alone is an sdist, at a locked hash and with a locked backend."""
    for arguments in _INSTALLS:
        subprocess.run([sys.executable, "-m", "pip", "install", *arguments], cwd=_ROOT,  # noqa: S603 # nosec B603
                       check=True, timeout=900)


if __name__ == "__main__":
    install()
