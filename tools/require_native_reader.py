"""Fail unless the optional native folder reader is built and agrees with this Python.

    python -m tools.require_native_reader
    python -m tools.require_native_reader --compiled build/standalone/start_file_tree.dist

``je_file_tree._native`` is optional: without it, or when its snapshots differ from ``os.lstat``,
FileTree reads folders in Python and ``test/test_native_scan.py`` is skipped. A job that means to
test or ship the module runs this first, so a build that silently produced nothing stops the job.
It only reads the metadata of this interpreter and of the package's own files.

With ``--compiled`` it checks instead that a stand-alone folder made by Nuitka carries the module and
the ``python3.dll`` it is linked against; Nuitka copies a built module but does not complain when
there is none.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from je_file_tree.core import native_scan  # noqa: E402

COMPILED_FILES = ("je_file_tree/_native.pyd", "python3.dll")


def missing_from(folder: Path) -> list[str]:
    """The files of ``COMPILED_FILES`` that the stand-alone ``folder`` lacks or holds empty."""
    return [name for name in COMPILED_FILES
            if not (folder / name).is_file() or (folder / name).stat().st_size == 0]


def in_use() -> int:
    """Return 0 when the scanner would use the native reader here, 1 with the reason otherwise."""
    if sys.platform != "win32":
        sys.stderr.write("The native folder reader is built on Windows only.\n")
        return 1
    try:
        from je_file_tree import _native  # noqa: PLC0415 - the optional module this tool reports on
    except ImportError as error:
        sys.stderr.write(f"je_file_tree._native is not built or cannot be loaded: {error}\n")
        return 1
    native_scan.reset()
    if native_scan.reader() is None:
        sys.stderr.write("je_file_tree._native disagrees with os.lstat or is switched off; "
                         "the scanner would read folders in Python.\n")
        return 1
    query = "one call per entry by name" if _native.by_name_available() else "one handle per entry"
    sys.stdout.write(f"The native folder reader is in use ({query} available).\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Check this interpreter, or with ``--compiled`` a stand-alone folder; 0 means the reader is there."""
    parser = argparse.ArgumentParser(description="Require FileTree's native folder reader.")
    parser.add_argument("--compiled", type=Path, metavar="FOLDER", help="a stand-alone folder made by Nuitka")
    options = parser.parse_args(argv)
    if options.compiled is None:
        return in_use()
    missing = missing_from(options.compiled)
    if missing:
        sys.stderr.write(f"{options.compiled} lacks {', '.join(missing)}: the program would scan in Python.\n")
        return 1
    sys.stdout.write(f"{options.compiled} carries the native folder reader.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
