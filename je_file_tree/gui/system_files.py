"""Read-only Windows-space explanations and explicit links to system-managed tools."""

from __future__ import annotations

import ntpath
import os
import subprocess  # nosec B404 - fixed absolute Windows system tools, never a shell
import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from je_file_tree.core.node import Node
from je_file_tree.core.system_files import SystemFile, system_file
from je_file_tree.gui.i18n import tr

_TOOLS = {'memory': 'SystemPropertiesAdvanced.exe', 'restore': 'SystemPropertiesProtection.exe',
          'cleanup': 'cleanmgr.exe'}
_SETTINGS = {'power': 'ms-settings:powersleep', 'storage': 'ms-settings:storagesense',
             'disks_volumes': 'ms-settings:disksandvolumes'}
# Tools whose manifests ask for elevation open through the shell's own "open" verb, so Windows shows its
# usual consent prompt instead of CreateProcess refusing them; FileTree passes no arguments to them.
_SHELL_TOOLS = {'disk_management': 'diskmgmt.msc', 'optimize': 'dfrgui.exe'}
_DRIVE_LENGTH = 2


def _system32() -> str | None:
    windows = os.environ.get('SYSTEMROOT') or os.environ.get('WINDIR', '')
    return ntpath.join(windows, 'System32') if windows and ntpath.isabs(windows) else None


def open_system_tool(tool: str, path: str) -> bool:
    """Open a fixed settings page or system tool; never issue cleanup/shutdown/hibernation commands."""
    if sys.platform != 'win32':
        return False
    if tool in _SETTINGS:
        return QDesktopServices.openUrl(QUrl(_SETTINGS[tool]))
    system32 = _system32()
    if system32 is None or (tool not in _TOOLS and tool not in _SHELL_TOOLS):
        return False
    if tool in _SHELL_TOOLS:
        return QDesktopServices.openUrl(QUrl.fromLocalFile(ntpath.join(system32, _SHELL_TOOLS[tool])))
    command = [ntpath.join(system32, _TOOLS[tool])]
    drive = ntpath.splitdrive(path)[0]
    if tool == 'cleanup' and len(drive) == _DRIVE_LENGTH and drive[0].isalpha() and drive[1] == ':':
        command.extend(['/d', drive[0]])
    try:
        subprocess.Popen(command)  # noqa: S603 # nosec B603 - fixed program and validated drive letter
    except OSError:
        return False
    return True


class SystemFileInfo(QWidget):
    """Explain an anchored system entry and offer its safe external configuration tool."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.node: Node | None = None
        self.info: SystemFile | None = None
        self.explanation = QLabel()
        self.explanation.setWordWrap(True)
        self.explanation.setTextFormat(Qt.TextFormat.PlainText)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.explanation.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.button = QPushButton()
        self.button.clicked.connect(self._open)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.explanation)
        layout.addWidget(self.button)
        self.set_node(None)

    def set_node(self, node: Node | None) -> None:
        """Update the explanation from a single path; no descendants/files are read."""
        self.node = node
        self.info = system_file(node.path) if node is not None and node.path is not None else None
        self.setVisible(self.info is not None)
        if self.info is not None:
            self.explanation.setText(tr(f'system_file_{self.info.kind}'))
            self.button.setText(tr(f'system_tool_{self.info.tool}'))

    def _open(self) -> None:
        if self.info is not None and self.node is not None and not open_system_tool(self.info.tool, self.node.path):
            QMessageBox.warning(self, tr('details_title'), tr('system_tool_failed'))
