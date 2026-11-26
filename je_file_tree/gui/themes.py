"""Application-wide Fluent light/dark themes (System follows the platform) with a persisted menu choice."""

from __future__ import annotations

import re

from PySide6.QtCore import QObject, QSettings, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QColor, QPalette, QStyleHints
from PySide6.QtWidgets import QApplication, QColorDialog, QMenu

from je_file_tree.gui.chart_palette import COLOUR_BLIND, PALETTE_KEY, STANDARD, palette_controller
from je_file_tree.gui.fluent_style import CONTRAST_ACCENT, FluentStyle, style_sheet, tokens_for
from je_file_tree.gui.i18n import tr

THEMES = ('system', 'light', 'dark', 'contrast')
SCHEMES = THEMES[1:]  # the ones with tokens of their own
ACCENT_KEY = 'accent'
_ACCENT = re.compile(r'#[0-9a-f]{6}')
NATIVE = 'native'  # the platform's own style and palette, used for System under high contrast


def theme_palette(theme: str, accent: QColor | str | None = None) -> QPalette:
    """Build the palette for one of ``SCHEMES`` from the Fluent tokens; anything else is empty (native)."""
    palette = QPalette()
    if theme not in SCHEMES:
        return palette
    t = tokens_for(theme, accent)
    roles = {
        'Window': t.window, 'WindowText': t.text, 'Base': t.card, 'AlternateBase': t.subtle,
        'Text': t.text, 'Button': t.control, 'ButtonText': t.text, 'BrightText': t.on_accent,
        'Highlight': t.accent, 'HighlightedText': t.on_accent, 'Accent': t.accent,
        'Light': t.card, 'Midlight': t.stroke, 'Mid': t.stroke_strong, 'Dark': t.stroke_strong,
        'Shadow': '#000000', 'ToolTipBase': t.card, 'ToolTipText': t.text,
        'Link': t.link, 'LinkVisited': t.link, 'PlaceholderText': t.text_secondary,
    }
    for role, colour in roles.items():
        palette.setColor(getattr(QPalette.ColorRole, role), QColor(colour))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(t.text_disabled))
    return palette


def _high_contrast(hints: QStyleHints) -> bool:
    """Whether the platform asks for high contrast (Qt 6.10+; older Qt cannot tell and answers no)."""
    accessibility = getattr(hints, 'accessibility', None)
    if accessibility is None:
        return False
    return accessibility().contrastPreference() == Qt.ContrastPreference.HighContrast


class ThemeController(QObject):
    """Apply one Fluent palette and style sheet application-wide, without changing scan data.

    System follows the platform's light/dark setting (and re-applies when it changes) unless the
    platform asks for high contrast, which keeps the native style and palette. Every theme uses the
    accent the user chose, or the platform accent captured before the first override.
    """

    changed = Signal(str)

    def __init__(self, app: QApplication) -> None:
        super().__init__(app)
        self.app = app
        self.native_style = app.style().objectName()
        self.platform_accent = QColor(app.palette().color(QPalette.ColorRole.Accent))
        self.chosen_accent = ''  # ``#rrggbb``, or empty for the platform's
        self._applied_accent = ''
        self.choice = 'system'
        self.resolved = NATIVE
        self.style: FluentStyle | None = None  # the applied style; Qt wraps it while a style sheet is set
        self._applying = False
        # Style sheets otherwise stop fonts set on a window (language fonts) reaching its children.
        app.setAttribute(Qt.ApplicationAttribute.AA_UseStyleSheetPropagationInWidgetStyles, True)
        app.styleHints().colorSchemeChanged.connect(self._platform_changed)

    @property
    def accent(self) -> QColor:
        """The accent in use."""
        return self.accent_for(self.resolved)

    def accent_for(self, scheme: str) -> QColor:
        """The chosen accent; without one, yellow in high contrast and the platform's elsewhere."""
        if self.chosen_accent:
            return QColor(self.chosen_accent)
        return QColor(CONTRAST_ACCENT) if scheme == 'contrast' else QColor(self.platform_accent)

    def set_accent(self, accent: str) -> None:
        """Use ``accent`` (``#rrggbb``; anything else means the platform's) in every theme."""
        self.chosen_accent = valid_accent(accent)
        self.apply(self.choice)

    def resolve(self, theme: str) -> str:
        """The scheme a choice shows now: ``light``, ``dark`` or ``native``."""
        if theme in SCHEMES:
            return theme
        hints = self.app.styleHints()
        if _high_contrast(hints):
            return NATIVE
        return 'dark' if hints.colorScheme() == Qt.ColorScheme.Dark else 'light'

    def apply(self, theme: str) -> None:
        """Apply one validated choice; repeated calls with the same platform state change nothing visible."""
        theme = theme if theme in THEMES else 'system'
        self._applying = True
        try:
            self._follow_platform_scheme(theme)
            resolved = self.resolve(theme)
            if (resolved == self.resolved and self.chosen_accent == self._applied_accent
                    and (resolved == NATIVE or self.style is not None)):
                # Re-setting an identical sheet repolishes every existing widget; each new window
                # applies the saved theme, so skip the work when nothing would change.
                pass
            elif resolved == NATIVE:
                self.app.setStyleSheet('')
                self.app.setStyle(self.native_style)
                self.app.setPalette(QPalette())
                self.style = None
            else:
                accent = self.accent_for(resolved)
                tokens = tokens_for(resolved, accent)
                self.style = FluentStyle(tokens)
                self.app.setStyle(self.style)
                self.app.setPalette(theme_palette(resolved, accent))
                self.app.setStyleSheet(style_sheet(tokens))
        finally:
            self._applying = False
        self.choice, self.resolved, self._applied_accent = theme, resolved, self.chosen_accent
        self.changed.emit(theme)

    def _follow_platform_scheme(self, theme: str) -> None:
        """Ask the platform for a matching title bar on explicit themes (Qt 6.8+); System follows it."""
        set_scheme = getattr(self.app.styleHints(), 'setColorScheme', None)
        if set_scheme is None:
            return
        scheme = {'light': Qt.ColorScheme.Light, 'dark': Qt.ColorScheme.Dark,
                  'contrast': Qt.ColorScheme.Dark}.get(theme, Qt.ColorScheme.Unknown)
        set_scheme(scheme)

    def _platform_changed(self, _scheme: Qt.ColorScheme) -> None:
        if self.choice == 'system' and not self._applying:
            self.apply('system')


def valid_accent(accent: object) -> str:
    """``accent`` as ``#rrggbb`` in lower case, or empty when it is not a colour."""
    text = accent.lower() if isinstance(accent, str) else ''
    return text if _ACCENT.fullmatch(text) else ''


def theme_controller() -> ThemeController:
    """Return the single controller attached to this QApplication, creating it before any override."""
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        raise RuntimeError('a QApplication is required')
    controller = getattr(app, '_filetree_theme_controller', None)
    if controller is None:
        controller = ThemeController(app)
        app._filetree_theme_controller = controller
    return controller


class ThemeMenu(QMenu):
    """A translated exclusive View → Theme submenu, with an independent saved setting."""

    def __init__(self, parent: QMenu, settings: QSettings) -> None:
        super().__init__(parent)
        parent.addMenu(self)
        self.settings = settings
        self.controller = theme_controller()
        group = QActionGroup(self)
        self.actions_by_theme: dict[str, QAction] = {}
        for theme in THEMES:
            action = self.addAction('')
            action.setCheckable(True)
            group.addAction(action)
            action.triggered.connect(lambda _checked=False, chosen=theme: self.choose(chosen))
            self.actions_by_theme[theme] = action
        self.addSeparator()
        self.accent = self.addAction('')
        self.accent.triggered.connect(lambda _checked=False: self._ask_accent())
        self.platform_accent = self.addAction('')
        self.platform_accent.triggered.connect(lambda _checked=False: self.choose_accent(''))
        self.colour_blind = self.addAction('')
        self.colour_blind.setCheckable(True)
        self.colour_blind.triggered.connect(lambda checked: self.choose_palette(COLOUR_BLIND if checked else STANDARD))
        palette_controller().changed.connect(self._mark_palette)
        self._mark_palette(palette_controller().choice)
        self.controller.changed.connect(self._mark)
        self._mark(self.controller.choice)
        self.retranslate()

    def retranslate(self) -> None:
        """Refresh the submenu labels in the current language without changing the choice."""
        self.setTitle(tr('menu_theme'))
        for theme, action in self.actions_by_theme.items():
            action.setText(tr(f'theme_{theme}'))
        self.accent.setText(tr('theme_accent'))
        self.platform_accent.setText(tr('theme_accent_platform'))
        self.colour_blind.setText(tr('theme_colour_blind'))

    def choose(self, theme: str) -> None:
        """Use ``theme`` everywhere and remember it."""
        self.settings.setValue('theme', theme)
        self.controller.apply(theme)

    def choose_accent(self, accent: str) -> None:
        """Use ``accent`` everywhere (empty: the platform's) and remember it."""
        accent = valid_accent(accent)
        self.settings.setValue(ACCENT_KEY, accent)
        self.controller.set_accent(accent)

    def choose_palette(self, name: str) -> None:
        """Use the chart colours ``name`` everywhere and remember them."""
        self.settings.setValue(PALETTE_KEY, name)
        palette_controller().apply(name)

    def _ask_accent(self) -> None:
        colour = QColorDialog.getColor(self.controller.accent, self.parentWidget(), tr('theme_accent'))
        if colour.isValid():
            self.choose_accent(colour.name())

    def _mark(self, theme: str) -> None:
        self.actions_by_theme[theme].setChecked(True)
        self.platform_accent.setEnabled(bool(self.controller.chosen_accent))

    def _mark_palette(self, name: str) -> None:
        self.colour_blind.setChecked(name == COLOUR_BLIND)
