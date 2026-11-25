"""Read and write the portable settings as a file: validated value by value, all or nothing.

Only choices that mean the same on another computer are included. Window positions, recent folders, presets,
templates, budgets and background scans name local folders and stay out; the clean-up policy has an export of
its own, whose import is previewed.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QSettings

from je_file_tree.core.formatting import AUTO_UNIT, SIZE_UNITS
from je_file_tree.gui.i18n import LANGUAGES
from je_file_tree.gui.text_scale import DEFAULT_TEXT_SIZE, TEXT_SIZES
from je_file_tree.gui.themes import THEMES

FORMAT = "file-tree-settings/1"
MAX_BYTES = 1_000_000
UNITS = (AUTO_UNIT, *SIZE_UNITS[1:5])
_MAX_WORKERS = 32
_MAX_HISTORY_MIB = 16384
_MAX_PATTERNS, _MAX_PATTERN = 1000, 4096

Value = bool | int | str | list[str]


@dataclass(frozen=True, slots=True)
class Setting:
    """One portable setting: what it is when nothing is saved, and which values are accepted."""

    default: Value
    valid: Callable[[object], bool]


def _flag(default: bool) -> Setting:
    return Setting(default, lambda value: type(value) is bool)


def _choice(options: tuple, default: Value) -> Setting:
    return Setting(default, lambda value: any(type(value) is type(option) and value == option for option in options))


def _number(low: int, high: int, default: int) -> Setting:
    return Setting(default, lambda value: type(value) is int and low <= value <= high)


def _patterns(value: object) -> bool:
    return (isinstance(value, list) and len(value) <= _MAX_PATTERNS
            and all(isinstance(item, str) and item.strip() and "\0" not in item and len(item) <= _MAX_PATTERN
                    for item in value))


SETTINGS: dict[str, Setting] = {
    "language": _choice(tuple(LANGUAGES), "en"),
    "theme": _choice(THEMES, "system"),
    "text_size": _choice(TEXT_SIZES, DEFAULT_TEXT_SIZE),
    "unit": _choice(UNITS, AUTO_UNIT),
    "include_hidden": _flag(True),
    "gentle_scan": _flag(False),
    "auto_cpu": _flag(True),
    "mft_scan": _flag(True),
    "capture_file_times": _flag(False),
    "capture_owners": _flag(False),
    "exact_allocation": _flag(False),
    "count_hard_links": _flag(False),
    "follow_changes": _flag(False),
    "check_updates": _flag(True),
    "ask_admin_at_start": _flag(True),
    "scan_workers": _number(1, _MAX_WORKERS, min(4, os.cpu_count() or 1)),
    "history_enabled": _flag(True),
    "history_limit_mib": _number(1, _MAX_HISTORY_MIB, 1024),
    "exclusions": Setting([], _patterns),
}


def _stored(key: str, value: object) -> object:
    """A value as ``QSettings`` returns it (the registry keeps text) in the type the file uses."""
    default = SETTINGS[key].default
    if isinstance(default, bool):
        return value if isinstance(value, bool) else str(value).lower() == "true"
    if isinstance(default, int):
        text = str(value)
        return int(text) if text.isascii() and text.isdigit() else default
    if isinstance(default, list):
        return [value] if isinstance(value, str) and value else [str(item) for item in value or []]
    return str(value)


def current(settings: QSettings, language: str) -> dict[str, Value]:
    """Every portable setting in use; an unset or unusable one counts as its default."""
    values: dict[str, Value] = {}
    for key, setting in SETTINGS.items():
        value = language if key == "language" else _stored(key, settings.value(key, setting.default))
        values[key] = value if setting.valid(value) else setting.default
    return values


def dumps(values: Mapping[str, Value]) -> str:
    """The file's text."""
    return json.dumps({"format": FORMAT, "values": dict(values)}, ensure_ascii=False, indent=2) + "\n"


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    document = dict(pairs)
    if len(document) != len(pairs):
        raise ValueError("repeated key")
    return document


def loads(text: str) -> dict[str, Value]:
    """The settings a file holds; anything unknown, invalid or repeated refuses the whole file."""
    document = json.loads(text, object_pairs_hook=_unique)
    if not isinstance(document, dict) or set(document) != {"format", "values"} or document["format"] != FORMAT:
        raise ValueError("not a FileTree settings file")
    values = document["values"]
    if not isinstance(values, dict):
        raise ValueError("no settings")
    for key, value in values.items():
        if key not in SETTINGS or not SETTINGS[key].valid(value):
            raise ValueError(f"unusable setting: {key}")
    return values


def read(path: str) -> dict[str, Value]:
    """Read a bounded settings file."""
    with Path(path).open(encoding="utf-8") as stream:
        text = stream.read(MAX_BYTES + 1)
    if len(text) > MAX_BYTES:
        raise ValueError("the file is too large")
    return loads(text)


def write(path: str, values: Mapping[str, Value]) -> None:
    """Write a settings file through a temporary sibling, so a failure leaves any earlier file as it was."""
    handle, temporary = tempfile.mkstemp(prefix=".file-tree-", suffix=".json",
                                         dir=os.path.dirname(os.path.abspath(path)))
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(dumps(values))
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def changes(before: Mapping[str, Value], after: Mapping[str, Value]) -> dict[str, Value]:
    """The settings of ``after`` that differ from ``before``."""
    return {key: value for key, value in after.items() if before.get(key) != value}
