"""Join source lines of Chinese text."""

from __future__ import annotations


def cjk(html: str) -> str:
    """Join the source lines of Chinese HTML: a line break there would show up as a space between characters."""
    return "".join(line.strip() for line in html.splitlines())
