"""The optional native passes over a finished tree, or None to take the same steps in Python.

``je_file_tree._native`` (Windows, optional) can write the folder JSON, total the capacity ledger and
gather the summary of a scanned tree. Those loops run once per folder or per file, and after a scan of a
whole drive they took as long as the scan itself (measured 2026-11-15, 1.1 million files: 5.6 s to save
the history, 3.3 s for the ledger, 1.8 s for the summary). Every native pass has the Python code it
stands in for next to its caller; that code is what runs on other systems, without the module, with a
module built before the pass existed, or with ``FILE_TREE_NATIVE_TREE=0``, and the tests compare the two.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from typing import Any

DISABLE_VARIABLE = "FILE_TREE_NATIVE_TREE"  # set to 0 to take every pass in Python
BATCH = 2000  # items per call: about a millisecond of work between two looks at cancel and the window


def function(name: str) -> Callable[..., Any] | None:
    """The native function ``name``, or None when the pass is to be taken in Python."""
    if sys.platform != "win32" or os.environ.get(DISABLE_VARIABLE, "1") == "0":
        return None
    try:
        from je_file_tree import _native  # noqa: PLC0415 - optional: absent without a compiler or on other systems
    except ImportError:
        return None
    return getattr(_native, name, None)
