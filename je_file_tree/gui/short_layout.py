"""Tighten the results page when the window is too short for it, and relax it again when there is room."""

from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QLabel, QWidget

from je_file_tree.gui.result_highlights import ResultHighlights
from je_file_tree.gui.result_overview import ResultOverview
from je_file_tree.gui.text_size import text_size_controller

_SLACK = 24  # pixels to spare before the page relaxes, so it never flips back and forth at one size


class ShortLayout(QObject):
    """Folds the highlights, puts each total on one line and drops the hint while the page does not fit.

    The page needs 786 pixels of window at the system's text size against 672 on a 1920 x 1080 screen at
    150 % scaling (2026-11-25). Once the user opens or closes the highlights, that choice stays theirs.
    """

    def __init__(self, page: QWidget, highlights: ResultHighlights, overview: ResultOverview, hint: QLabel) -> None:
        super().__init__(page)
        self.page, self.highlights, self.overview, self.hint = page, highlights, overview, hint
        self.short = False
        self._saved = 0
        self._chosen = False  # the user opened or closed the highlights
        highlights.toggle.clicked.connect(self._choose)
        text_size_controller().changed.connect(self._relax)

    def _choose(self, _checked: bool) -> None:
        self._chosen = True

    def fit(self, room: int) -> None:
        """Choose the layout for ``room`` pixels of height."""
        if room <= 0:
            return
        needed = self.page.minimumSizeHint().height()
        if not self.short and needed > room:
            self._tighten()
        elif self.short and needed + self._saved + self._folded() + _SLACK <= room:
            self._relax()

    def _tighten(self) -> None:
        self.short = True
        before = self._measure()
        self.overview.set_inline(True)
        self.hint.hide()
        self._saved = before - self._measure()
        if not self._chosen:
            self.highlights.toggle.setChecked(False)

    def _relax(self, _percent: int = 0) -> None:
        """Show everything again (a changed text size measures it afresh)."""
        if not self.short:
            return
        self.short = False
        self.overview.set_inline(False)
        self.hint.show()
        if not self._chosen:
            self.highlights.toggle.setChecked(True)

    def _folded(self) -> int:
        """The height the highlights would take if opened; their content changes while they are folded."""
        if self._chosen or self.highlights.toggle.isChecked():
            return 0
        return self.highlights.body.layout().totalMinimumSize().height() + self.highlights.layout().spacing()

    def _measure(self) -> int:
        """The page's minimum height right after its parts changed, before Qt lays them out again."""
        for part in (self.overview, self.hint.parentWidget(), self.page):
            layout = part.layout()
            if layout is not None:
                layout.invalidate()
                layout.activate()
        return self.page.minimumSizeHint().height()
