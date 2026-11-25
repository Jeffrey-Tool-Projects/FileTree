"""Clean-up rules the user writes: data only, always for manual review, never reaching protected places.

A rule names folders by the end of their path and files by their name, as the built-in rules do, plus a
minimum age. It has no say in its risk: what it finds is never selected in bulk, never proposed by background
scans and never includes system, program or profile folders or Windows-managed files. Patterns have to say
enough: ``*`` alone would match everything.
"""

from __future__ import annotations

import ntpath
import os
import posixpath
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass

from je_file_tree.core.cleanup import CUSTOM_PREFIX, Rule, RuleDetails
from je_file_tree.core.protected import FREE, Protection, protected_places, protection_of
from je_file_tree.core.system_files import system_file

MAX_RULES = 50
MAX_PATTERNS = 20
MAX_NAME, MAX_PATTERN = 80, 200
MIN_LITERALS = 3
MAX_AGE = 36500
_WILDCARDS = frozenset("*?[]")
_CLASS = re.compile(r"\[!?\]?[^\]]*\]")  # one character out of a set: says as little as "?"
_FORBIDDEN = frozenset('<>"|\0\r\n\t')


def _literals(text: str) -> int:
    return sum(character.isalnum() for character in _CLASS.sub("", text))


def _usable_text(text: object, limit: int) -> bool:
    return isinstance(text, str) and text == text.strip() and 0 < len(text) <= limit and not _FORBIDDEN & set(text)


def _usable_file(pattern: object) -> bool:
    return (_usable_text(pattern, MAX_PATTERN) and not {"/", "\\", ":"} & set(pattern)
            and _literals(pattern) >= MIN_LITERALS)


def _usable_folder(pattern: object) -> bool:
    if not _usable_text(pattern, MAX_PATTERN) or {"\\", ":"} & set(pattern):
        return False
    parts = pattern.split("/")
    # The last name is looked up literally, so it says what is proposed; "." and ".." are no names.
    return (all(part and part not in (".", "..") for part in parts) and not _WILDCARDS & set(parts[-1])
            and _literals(parts[-1]) >= 1 and _literals(pattern) >= MIN_LITERALS)


@dataclass(frozen=True, slots=True)
class CustomRule:
    """One user-written rule; an unusable one cannot be built."""

    name: str
    folders: tuple[str, ...] = ()
    files: tuple[str, ...] = ()
    in_folder: str | None = None
    days: int = 30

    def __post_init__(self) -> None:
        if not _usable_text(self.name, MAX_NAME) or ":" in self.name:
            raise ValueError("invalid custom rule name")
        if (not isinstance(self.folders, tuple) or not isinstance(self.files, tuple)
                or not 1 <= len(self.folders) + len(self.files) <= MAX_PATTERNS):
            raise ValueError("invalid custom rule patterns")
        if not all(map(_usable_folder, self.folders)) or not all(map(_usable_file, self.files)):
            raise ValueError("a custom rule pattern is too broad or not a name")
        if self.in_folder is not None and (not self.files or not _usable_file(self.in_folder)
                                           or _WILDCARDS & set(self.in_folder)):
            raise ValueError("invalid custom rule folder")
        if type(self.days) is not int or not 1 <= self.days <= MAX_AGE:
            raise ValueError("invalid custom rule age")

    @property
    def key(self) -> str:
        """The clean-up group this rule's finds land in."""
        return CUSTOM_PREFIX + self.name

    def rule(self) -> Rule:
        """The matcher's rule; its risk is fixed."""
        return Rule(self.key, folders=self.folders, files=self.files, in_folder=self.in_folder,
                    details=RuleDetails("custom", self.days, "manual", "custom", "custom"))

    def document(self) -> dict[str, object]:
        """The rule as the policy file holds it."""
        return {"name": self.name, "folders": list(self.folders), "files": list(self.files),
                "in_folder": self.in_folder, "days": self.days}


def from_document(value: object) -> CustomRule:
    """Read one rule strictly."""
    if (not isinstance(value, dict) or set(value) != {"name", "folders", "files", "in_folder", "days"}
            or not isinstance(value["folders"], list) or not isinstance(value["files"], list)):
        raise ValueError("invalid custom rule")
    return CustomRule(value["name"], tuple(value["folders"]), tuple(value["files"]), value["in_folder"],
                      value["days"])


def check_rules(rules: object) -> None:
    """Refuse a set of rules that is too large or uses one name twice."""
    if not isinstance(rules, tuple) or len(rules) > MAX_RULES or not all(isinstance(rule, CustomRule)
                                                                         for rule in rules):
        raise ValueError("invalid custom rules")
    if len({rule.name.casefold() for rule in rules}) != len(rules):
        raise ValueError("repeated custom rule name")


class Guard:
    """Whether a custom rule must leave an entry alone: protected, Windows-managed, or holding such a place."""

    def __init__(self, places: Iterable[Protection] | None = None, platform: str = sys.platform) -> None:
        self._places = tuple(protected_places() if places is None else places)
        self._platform = platform
        paths = ntpath if platform == "win32" else posixpath
        self._paths = paths
        self._held = [self._normal(place.path) for place in self._places if place.reason != FREE]

    def _normal(self, path: str) -> str:
        normal = self._paths.normpath(path)
        return self._paths.normcase(normal) if self._platform == "win32" else normal

    def refuses(self, path: str | None) -> bool:
        """True for anything a user-written pattern may not propose."""
        if path is None or not os.path.isabs(path):
            return True
        if (protection_of(path, self._places, self._platform) is not None
                or system_file(path, platform=self._platform) is not None):
            return True
        inside = self._normal(path).rstrip(self._paths.sep) + self._paths.sep
        return any(place.startswith(inside) for place in self._held)
