"""Chart colours for how each folder changed since the saved scan on the Changes tab."""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtGui import QColor

from je_file_tree.core.compare import FolderChange
from je_file_tree.core.node import Node

NEW, GREW_LOT, GREW, SAME, SHRANK, SHRANK_LOT = "new", "grew_lot", "grew", "same", "shrank", "shrank_lot"
# Orange against blue, which colour-blind viewers tell apart too; each 3:1 on the light and the dark card.
CHANGE_COLOURS = {NEW: "#b45fa5", GREW_LOT: "#d55e00", GREW: "#c08a4e", SAME: "#8c8c8c", SHRANK: "#5b95c9",
                  SHRANK_LOT: "#2a78b8"}
LOT = .25  # of the size before


def kind_of(change: FolderChange) -> str:
    """Which colour a changed folder gets."""
    if change.before is None:
        return NEW
    grown = change.change
    if grown == 0:
        return SAME
    lot = abs(grown) > LOT * max(change.before, 1)
    if grown > 0:
        return GREW_LOT if lot else GREW
    return SHRANK_LOT if lot else SHRANK


class ChangeColours:
    """Colours by captured comparison: a folder by its own change, a file by the folder that holds it.

    A saved scan records folders, not files. The changes are kept so that their nodes stay alive and their
    identities valid; folders that are not listed did not change.
    """

    def __init__(self, changes: Iterable[FolderChange] = ()) -> None:
        self._changes = tuple(change for change in changes if change.node is not None)
        self._kinds = {id(change.node): kind_of(change) for change in self._changes}

    def kind(self, node: Node) -> str:
        """The kind of change of ``node``'s folder."""
        folder = node if node.is_dir and not node.is_link else node.parent
        return SAME if folder is None else self._kinds.get(id(folder), SAME)

    def colour(self, node: Node) -> QColor:
        """The fill for ``node``."""
        return QColor(CHANGE_COLOURS[self.kind(node)])
