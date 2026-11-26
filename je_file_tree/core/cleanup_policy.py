"""Validated declarative clean-up settings, separate from scan exclusions."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, replace

from je_file_tree.core.cleanup import DETAILS, RULES, Rule
from je_file_tree.core.custom_rules import CustomRule, Guard, check_rules, from_document
from je_file_tree.core.exclusions import Excluded, exclusion_test, is_path
from je_file_tree.core.node import Node

_MAX_AGE = 36500
_MAX_EXCLUSIONS = 1000
_MAX_TEXT = 256_000
_MAX_PATH = 32767
_CUSTOM_VERSION = 2
_FIELDS = {1: {"version", "rules", "exclusions"}, _CUSTOM_VERSION: {"version", "rules", "exclusions", "custom"}}


@dataclass(frozen=True, slots=True)
class RuleSetting:
    """One supported rule's enabled state and minimum age in whole days."""

    key: str
    enabled: bool
    minimum_age: int


@dataclass(frozen=True, slots=True)
class CleanupPolicy:
    """Built-in rules with validated overrides, plus user-written rules as data; nothing executable."""

    overrides: tuple[RuleSetting, ...] = ()
    exclusions: tuple[str, ...] = ()
    custom: tuple[CustomRule, ...] = ()
    _excluded: Excluded | None = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        keys: set[str] = set()
        for setting in self.overrides:
            if (not isinstance(setting, RuleSetting) or setting.key not in DETAILS or setting.key in keys
                    or type(setting.enabled) is not bool or type(setting.minimum_age) is not int
                    or not 0 <= setting.minimum_age <= _MAX_AGE):
                raise ValueError("invalid rule setting")
            keys.add(setting.key)
        if len(self.exclusions) > _MAX_EXCLUSIONS:
            raise ValueError("too many exclusions")
        for path in self.exclusions:
            if not isinstance(path, str) or not path.strip() or "\0" in path or len(path) > _MAX_PATH:
                raise ValueError("invalid exclusion")
            if is_path(path) and not os.path.isabs(path):
                raise ValueError("exclusion paths must be absolute")
        check_rules(self.custom)
        object.__setattr__(self, "_excluded", exclusion_test(self.exclusions))

    def setting(self, key: str) -> RuleSetting:
        """The override or the current built-in default."""
        return next((setting for setting in self.overrides if setting.key == key),
                    RuleSetting(key, True, int(DETAILS[key].minimum_age)))

    def rules(self) -> tuple[Rule, ...]:
        """Built-in recognizers with effective ages; risk/evidence cannot be weakened by settings."""
        return tuple(replace(rule, details=replace(rule.details, minimum_age=self.setting(rule.key).minimum_age))
                     for rule in RULES if self.setting(rule.key).enabled) + tuple(rule.rule() for rule in self.custom)

    def guard(self) -> Guard | None:
        """What keeps user-written rules away from protected places; needed only when there are any."""
        return Guard() if self.custom else None

    def built_in(self) -> CleanupPolicy:
        """This policy without user-written rules, which background scans never use."""
        return replace(self, custom=()) if self.custom else self

    def excludes(self, node: Node) -> bool:
        """Whether this name or exact path must never be proposed, including its descendants."""
        return node.path is not None and self._excluded is not None and self._excluded(node.name, node.path)

    def dumps(self) -> str:
        """Validated JSON suitable for QSettings or an exported policy file."""
        rules = {setting.key: {"enabled": setting.enabled, "days": setting.minimum_age} for setting in self.overrides}
        value: dict[str, object] = {"version": 1, "rules": rules, "exclusions": list(self.exclusions)}
        if self.custom:  # version 1 stays readable by earlier releases
            value |= {"version": _CUSTOM_VERSION, "custom": [rule.document() for rule in self.custom]}
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def load_policy(text: str) -> CleanupPolicy:
    """Strictly load a bounded policy document; invalid/unknown settings raise ValueError."""
    if not isinstance(text, str) or len(text) > _MAX_TEXT:
        raise ValueError("policy is too large")
    try:
        value = json.loads(text, object_pairs_hook=_unique_object)
    except RecursionError as error:
        raise ValueError("policy nesting is too deep") from error
    if (not isinstance(value, dict) or type(value.get("version")) is not int
            or set(value) != _FIELDS.get(value["version"])
            or not isinstance(value["rules"], dict) or not isinstance(value["exclusions"], list)):
        raise ValueError("invalid policy document")
    settings = []
    for key, setting in value["rules"].items():
        if not isinstance(setting, dict) or set(setting) != {"enabled", "days"}:
            raise ValueError("invalid rule fields")
        settings.append(RuleSetting(key, setting["enabled"], setting["days"]))
    custom = value.get("custom", [])
    if not isinstance(custom, list):
        raise ValueError("invalid custom rules")
    return CleanupPolicy(tuple(settings), tuple(value["exclusions"]), tuple(map(from_document, custom)))


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("duplicate policy keys")
    return result
