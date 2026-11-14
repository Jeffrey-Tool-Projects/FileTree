"""Build step for the optional native scanner module; everything else is declared in ``pyproject.toml``.

``je_file_tree._native`` (``je_file_tree/_native.cpp``) is built on Windows only and is optional: when
no compiler is available the build goes on without it and FileTree uses its Python scanner, with the
same results. It is linked against the stable ABI, so one wheel serves Python 3.11 and later, and
against the static C++ runtime, so it needs no Visual C++ redistributable on the user's machine.
"""

import sys

from setuptools import Extension, setup

STABLE_ABI = "cp311"

extensions = []
options = {}
if sys.platform == "win32":
    extensions.append(Extension(
        "je_file_tree._native",
        sources=["je_file_tree/_native.cpp"],
        define_macros=[("Py_LIMITED_API", "0x030B0000"), ("UNICODE", None), ("_UNICODE", None)],
        py_limited_api=True,
        optional=True,
        extra_compile_args=["/std:c++17", "/EHsc", "/O2", "/W4", "/MT"],
    ))
    options["bdist_wheel"] = {"py_limited_api": STABLE_ABI}

setup(ext_modules=extensions, options=options)
