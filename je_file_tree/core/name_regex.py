"""Regular expressions for names that cannot hang a search.

Python's engine backtracks and holds the interpreter while it does, so one bad pattern would freeze the window.
Patterns that can take exponential time (a repeat inside a repeat, alternatives inside a repeat, references to
groups, look-around) and patterns with many open-ended repeats are refused before any name is tried.
"""

from __future__ import annotations

import re
from re import _constants as _kinds  # type: ignore[attr-defined]
from re import _parser  # type: ignore[attr-defined]

MAX_LENGTH = 500
MAX_COST = 16384
_OPEN_COST = 64  # what one open-ended repeat multiplies the cost by; two leave room for a few alternatives
_REPEATS = {_kinds.MAX_REPEAT, _kinds.MIN_REPEAT, _kinds.POSSESSIVE_REPEAT}
_REFUSED = {_kinds.GROUPREF, _kinds.GROUPREF_EXISTS, _kinds.ASSERT, _kinds.ASSERT_NOT}


class NameRegexError(ValueError):
    """Not a regular expression, or one that could take too long."""


def name_regex(text: str) -> re.Pattern[str]:
    """Compile ``text``, ignoring case; ``search`` on it finds a match anywhere in a name."""
    if not text or len(text) > MAX_LENGTH:
        raise NameRegexError("empty or too long")
    try:
        parsed = _parser.parse(text, re.IGNORECASE)
        pattern = re.compile(text, re.IGNORECASE)
    except (re.error, OverflowError, RecursionError) as error:
        raise NameRegexError(str(error)) from error
    if _cost(parsed, inside=False) > MAX_COST:
        raise NameRegexError("the pattern could take too long")
    return pattern


def _cost(parsed, *, inside: bool) -> int:
    """How many ways a parsed pattern can be tried, roughly; refuses anything that could grow exponentially.

    The ways of parts in sequence multiply (``a?a?a?`` has eight), the alternatives of a branch add up.
    """
    cost = 1
    for kind, value in parsed:
        if kind in _REFUSED:
            raise NameRegexError("references and look-around are not supported")
        if kind in _REPEATS:
            cost *= _repeat_cost(*value, inside=inside)
        elif kind == _kinds.BRANCH:
            if inside:
                raise NameRegexError("alternatives inside a repeat could take too long")
            cost *= sum(_cost(branch, inside=False) for branch in value[1])
        elif kind == _kinds.SUBPATTERN:
            cost *= _cost(value[-1], inside=inside)
        elif kind == _kinds.ATOMIC_GROUP:
            cost *= _cost(value, inside=inside)
    return cost


def _repeat_cost(least: int, most: int, body, *, inside: bool) -> int:
    if inside:
        raise NameRegexError("a repeat inside a repeat could take too long")
    if most == 1:  # an optional part may hold anything: it is tried at most once
        return 1 + _cost(body, inside=False)
    _cost(body, inside=True)
    return _OPEN_COST if most == _kinds.MAXREPEAT else int(most) - int(least) + 1
