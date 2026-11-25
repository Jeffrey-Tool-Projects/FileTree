"""User-written clean-up rules stay data: validated, manual, out of bulk selection and away from protected places."""

import json
import time

import pytest

from je_file_tree.core import recurring
from je_file_tree.core.cleanup import CUSTOM_PREFIX, find_cleanup
from je_file_tree.core.cleanup_policy import CleanupPolicy, load_policy
from je_file_tree.core.custom_rules import MAX_PATTERNS, MAX_RULES, CustomRule, Guard, check_rules
from je_file_tree.core.node import Node
from je_file_tree.core.protected import FREE, PROGRAMS, SYSTEM, Protection

_OLD = time.time() - 400 * 86400


def _tree(base: str) -> Node:
    """A scanned folder with old backups, a cache and a recent file."""
    root = Node(base, True, children=[], modified=_OLD)

    def folder(name, parent):
        node = Node(name, True, children=[], parent=parent, modified=_OLD)
        parent.children.append(node)
        return node

    def file(name, parent, modified=_OLD):
        node = Node(name, False, size=10, parent=parent, modified=modified)
        parent.children.append(node)
        return node
    work = folder("Work", root)
    file("plan.bak", work)
    file("plan.txt", work)
    file("new.bak", work, time.time())
    cache = folder("MyCache", folder("MyApp", root))
    file("blob.bin", cache)
    backups = folder("Backups", root)
    file("other.bak", backups)
    return root


def _paths(groups, rule):
    return {node.name for group in groups if group.key == rule.key for node in group.nodes}


@pytest.mark.parametrize("fields", [
    {"name": ""}, {"name": " x"}, {"name": "a:b"}, {"name": "x" * 81}, {"name": "line\nbreak"}, {"name": 5},
    {"folders": (), "files": ()}, {"files": ("*",)}, {"files": ("*.*",)}, {"files": ("*.b",)},
    {"files": ("[a-z0-9]*",)}, {"files": ("[!abc]*",)},
    {"folders": ("[abcd]*/x",)}, {"files": ("a/b.bak",)},
    {"files": ("C:x.bak",)}, {"files": ("..",)}, {"folders": ("*",)}, {"folders": ("/",)}, {"folders": ("/data",)},
    {"folders": ("a/../b",)}, {"folders": ("Users/*",)}, {"folders": ("C:/Windows",)}, {"folders": ("a\\b",)},
    {"folders": ("x" * 201,)}, {"folders": ("aaa",) * (MAX_PATTERNS + 1)}, {"folders": ["aaa"]}, {"files": (3,)},
    {"days": 0}, {"days": True}, {"days": 1.5}, {"days": 36501},
    {"in_folder": "Downloads", "files": (), "folders": ("abc",)},
    {"in_folder": "Down*", "files": ("*.bak",)}, {"in_folder": "", "files": ("*.bak",)},
])
def test_unusable_rules_cannot_be_built(fields):
    values = {"name": "Mine", "files": ("*.bak",)} | fields
    with pytest.raises(ValueError):
        CustomRule(**values)


def test_rules_are_bounded_and_named_once():
    rule = CustomRule("Mine", files=("*.bak",))
    check_rules((rule,))
    for rules in ((rule, CustomRule("MINE", files=("*.old",))), [rule], (rule, "x"),
                  tuple(CustomRule(f"r{index}", files=("*.bak",)) for index in range(MAX_RULES + 1))):
        with pytest.raises(ValueError):
            check_rules(rules)


def test_finds_are_manual_and_follow_the_pattern_folder_and_age(tmp_path):
    root = _tree(str(tmp_path))
    files = CustomRule("Backups", files=("*.bak",), days=30)
    folders = CustomRule("App cache", folders=("MyApp/MyCache",))
    groups = find_cleanup(root, policy=CleanupPolicy(custom=(files, folders)))
    assert _paths(groups, files) == {"plan.bak", "other.bak"}
    assert _paths(groups, folders) == {"MyCache"}
    for group in groups:
        if group.key.startswith(CUSTOM_PREFIX):
            assert group.details.risk == "manual" and not group.details.rebuildable
    only = CustomRule("Backups", files=("*.bak",), in_folder="Backups")
    assert _paths(find_cleanup(root, policy=CleanupPolicy(custom=(only,))), only) == {"other.bak"}


def test_protected_places_are_refused_whatever_the_pattern_says(tmp_path, monkeypatch):
    base = str(tmp_path)
    places = (Protection(str(tmp_path / "Work"), PROGRAMS),
              Protection(str(tmp_path / "MyApp" / "MyCache" / "deep"), SYSTEM),
              Protection(str(tmp_path / "Backups"), FREE))
    monkeypatch.setattr("je_file_tree.core.cleanup_policy.Guard", lambda: Guard(places))
    files, folders = CustomRule("Files", files=("*.bak",)), CustomRule("Folders", folders=("MyCache",))
    groups = find_cleanup(_tree(base), policy=CleanupPolicy(custom=(files, folders)))
    assert _paths(groups, files) == {"other.bak"}  # nothing inside the protected program folder
    assert _paths(groups, folders) == set()  # it holds a protected place
    assert Guard(places).refuses(None) and Guard(places).refuses("relative/path")


def test_without_a_guard_custom_rules_find_nothing(tmp_path):
    rule = CustomRule("Files", files=("*.bak",))
    assert _paths(find_cleanup(_tree(str(tmp_path)), rules=(rule.rule(),)), rule) == set()


def test_policy_files_round_trip_and_stay_version_1_without_own_rules():
    plain = CleanupPolicy(exclusions=("keep",))
    assert json.loads(plain.dumps())["version"] == 1 and load_policy(plain.dumps()) == plain
    own = CleanupPolicy(custom=(CustomRule("Mine", ("Cache/Old",), ("*.bak",), "Saved", 12),))
    assert json.loads(own.dumps())["version"] == 2 and load_policy(own.dumps()) == own
    assert own.built_in() == CleanupPolicy()


@pytest.mark.parametrize("change", [
    {"version": 1}, {"version": 3}, {"version": True}, {"custom": {}}, {"custom": [{}]}, {"extra": 1},
    {"custom": [{"name": "Mine", "folders": [], "files": ["*"], "in_folder": None, "days": 3}]},
    {"custom": [{"name": "Mine", "folders": [], "files": ["*.bak"], "in_folder": None, "days": 3, "risk": "low"}]},
])
def test_altered_policy_files_are_refused(change):
    document = json.loads(CleanupPolicy(custom=(CustomRule("Mine", files=("*.bak",)),)).dumps()) | change
    with pytest.raises(ValueError):
        load_policy(json.dumps(document))


def test_background_proposals_never_use_own_rules(tmp_path):
    own = CleanupPolicy(custom=(CustomRule("Files", files=("*.bak",)),))
    candidates, _count = recurring._candidates(_tree(str(tmp_path)), own, time.time(), None)
    assert all(not candidate.rule.startswith(CUSTOM_PREFIX) for candidate in candidates)
    assert recurring.policy_version(own) == recurring.policy_version(own.built_in())
