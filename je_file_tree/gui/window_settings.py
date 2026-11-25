"""Names and settings the parts of the main window share."""

from __future__ import annotations

import json

from PySide6.QtCore import QSettings

from je_file_tree.core.formatting import AUTO_UNIT, SIZE_UNITS
from je_file_tree.core.scanner import DEFAULT_WORKERS
from je_file_tree.gui.scan_preferences import MAX_SCAN_WORKERS as _MAX_SCAN_WORKERS

WELCOME_PAGE, RESULTS_PAGE = range(2)
UNITS = (AUTO_UNIT, *SIZE_UNITS[1:5])
STATUS_TIMEOUT_MS = 8000
ASK_ADMIN_KEY = "ask_admin_at_start"
EXCLUSIONS_KEY = "exclusions"
SEARCHES_KEY = "saved_searches"
CLEANUP_POLICY_KEY = "cleanup_policy"
SCAN_WORKERS_KEY = "scan_workers"
AUTO_CPU_KEY = "auto_cpu"
MFT_SCAN_KEY = "mft_scan"


def read_flag(settings: QSettings, key: str, default: bool) -> bool:
    """A yes/no setting (the registry keeps them as the strings \"true\" and \"false\")."""
    value = settings.value(key, default)
    return value if isinstance(value, bool) else str(value).lower() == "true"


def read_workers(settings: QSettings) -> int:
    """Validated user-selected concurrency; invalid persisted values retain the existing CPU-bounded default."""
    raw = settings.value(SCAN_WORKERS_KEY, DEFAULT_WORKERS)
    if not isinstance(raw, (int, str)) or isinstance(raw, bool):
        return DEFAULT_WORKERS
    try:
        value = int(raw)
    except (ValueError, TypeError):
        return DEFAULT_WORKERS
    return value if 1 <= value <= _MAX_SCAN_WORKERS else DEFAULT_WORKERS


def saved_searches(settings: QSettings) -> dict[str, object]:
    """The saved searches kept in the settings as JSON; anything unreadable counts as none."""
    try:
        searches = json.loads(str(settings.value(SEARCHES_KEY, "{}")))
    except ValueError:
        return {}
    return searches if isinstance(searches, dict) else {}
