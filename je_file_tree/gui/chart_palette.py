"""The colours of file types in charts: the standard set, or one that colour-blind viewers can tell apart."""

from __future__ import annotations

from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtWidgets import QApplication

PALETTE_KEY = "chart_palette"
STANDARD, COLOUR_BLIND = "standard", "colour_blind"
# One flat colour per file-type group (every key of analysis.CATEGORIES): evenly bright hues; labels pick
# black or white by contrast. The second set follows Okabe and Ito, darkened where needed; both keep 3:1 on
# the light and the dark card.
PALETTES: dict[str, dict[str, str]] = {
    STANDARD: {"images": "#3fa34d", "video": "#be8912", "audio": "#8e6cc8", "documents": "#3b82c4",
               "archives": "#dc7434", "code": "#1fa2a8", "programs": "#d9534f", "other": "#958a7b"},
    COLOUR_BLIND: {"images": "#009e73", "video": "#b88700", "audio": "#c977a4", "documents": "#0f78b8",
                   "archives": "#d55e00", "code": "#4a97c9", "programs": "#8c6bb1", "other": "#8a8a8a"},
}
# The set in use; every chart and legend reads this one dictionary.
CATEGORY_COLOURS: dict[str, str] = dict(PALETTES[STANDARD])


class PaletteController(QObject):
    """Switch the file-type colours application-wide; ``changed`` follows so charts and legends redraw."""

    changed = Signal(str)

    def __init__(self, app: QApplication) -> None:
        super().__init__(app)
        self.choice = STANDARD

    def apply(self, name: str) -> None:
        """Use palette ``name``; an unknown one means the standard set."""
        name = name if name in PALETTES else STANDARD
        if name == self.choice:
            return
        self.choice = name
        CATEGORY_COLOURS.update(PALETTES[name])
        self.changed.emit(name)


def palette_controller() -> PaletteController:
    """Return the single controller attached to this QApplication."""
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        raise RuntimeError("a QApplication is required")
    controller = getattr(app, "_filetree_palette_controller", None)
    if controller is None:
        controller = PaletteController(app)
        app._filetree_palette_controller = controller
    return controller


def saved_palette(settings: QSettings) -> str:
    """The remembered palette; an unknown one means the standard set."""
    name = str(settings.value(PALETTE_KEY, STANDARD))
    return name if name in PALETTES else STANDARD
