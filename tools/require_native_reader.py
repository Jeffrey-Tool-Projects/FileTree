"""Fail unless the optional native folder reader is built and agrees with this Python.

    python -m tools.require_native_reader

``je_file_tree._native`` is optional: without it, or when its snapshots differ from ``os.lstat``,
FileTree reads folders in Python and ``test/test_native_scan.py`` is skipped. A job that means to
test or ship the module runs this first, so a build that silently produced nothing stops the job.
It only reads the metadata of this interpreter and of the package's own files.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from je_file_tree.core import native_scan  # noqa: E402


def main() -> int:
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


if __name__ == "__main__":
    sys.exit(main())
