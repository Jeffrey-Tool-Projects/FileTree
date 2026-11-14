"""Open a window at a size taken from the screen it appears on, instead of a fixed pixel size.

Every window names the size it was laid out for on a full-HD desktop. On a smaller screen that size
is cut back so the window, its title bar and its buttons stay on screen; on a larger one it grows
in proportion, so lists and charts use the room instead of sitting in a corner. A size the user
chose themselves (a restored geometry, a drag) is applied after this and wins.
"""

from PySide6.QtCore import QSize
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget

DESIGN = QSize(1920, 1040)  # the available desktop area the preferred sizes were chosen on
_SHARE = 0.92  # at most this part of the available area, so the frame and task bar stay reachable
_LARGEST_GROWTH = 1.5  # beyond this a dialog is only harder to read across
_SMALLEST = QSize(320, 160)


def fitted_size(width: int, height: int, available: QSize | None) -> QSize:
    """The size for a window laid out for ``width`` x ``height`` on a screen with ``available`` room.

    Without a known screen the preferred size is returned unchanged.
    """
    if available is None or available.width() <= 0 or available.height() <= 0:
        return QSize(width, height)
    growth = min(available.width() / DESIGN.width(), available.height() / DESIGN.height())
    growth = max(1.0, min(_LARGEST_GROWTH, growth))
    return QSize(_bounded(width * growth, available.width(), _SMALLEST.width()),
                 _bounded(height * growth, available.height(), _SMALLEST.height()))


def fit_window(window: QWidget, width: int, height: int) -> None:
    """Resize ``window`` to its preferred size adapted to the screen of its parent (or the primary one)."""
    window.resize(fitted_size(width, height, _available(window)))


def _bounded(wanted: float, room: int, smallest: int) -> int:
    return max(min(smallest, room), min(round(wanted), int(room * _SHARE)))


def _available(window: QWidget) -> QSize | None:
    parent = window.parentWidget()
    screen = parent.screen() if parent is not None else QGuiApplication.primaryScreen()
    return None if screen is None else screen.availableGeometry().size()
