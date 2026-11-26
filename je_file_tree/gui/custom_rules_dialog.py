"""Edit clean-up rules the user writes; the policy editor still has to preview them before they are saved."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from je_file_tree.core.custom_rules import MAX_AGE, MAX_RULES, CustomRule, check_rules
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.window_fit import fit_window


def _parts(text: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in text.split(";") if part.strip())


class CustomRulesDialog(QDialog):
    """A list of rules and one form; OK is refused while a rule is too broad, unusable or named twice."""

    def __init__(self, rules: Sequence[CustomRule], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("custom_rules_title"))
        fit_window(self, 720, 460)
        self._rules = list(rules)
        self.list = QListWidget()
        self.list.setAccessibleName(tr("custom_rules_title"))
        self.name, self.folders, self.files, self.in_folder = (QLineEdit() for _ in range(4))
        self.days = QSpinBox()
        self.days.setRange(1, MAX_AGE)
        self.days.setValue(30)
        self.folders.setPlaceholderText("Cache; MyApp/logs")
        self.files.setPlaceholderText("*.bak; *.old")
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.add, self.update_rule, self.remove = (QPushButton(tr(f"custom_rules_{key}"))
                                                   for key in ("add", "update", "remove"))
        for button in (self.add, self.update_rule, self.remove):
            button.setAutoDefault(False)
        self.add.clicked.connect(lambda: self._store(None))
        self.update_rule.clicked.connect(lambda: self._store(self.list.currentRow()))
        self.remove.clicked.connect(self._remove)
        self.list.currentRowChanged.connect(self._chosen)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self._assemble()
        self._fill(0 if self._rules else -1)

    def _assemble(self) -> None:
        hint = QLabel(tr("custom_rules_hint"))
        hint.setWordWrap(True)
        form = QFormLayout()
        for key, field in (("name", self.name), ("folders", self.folders), ("files", self.files),
                           ("in_folder", self.in_folder), ("days", self.days)):
            label = QLabel(tr(f"custom_rules_{key}"))
            label.setBuddy(field)
            field.setAccessibleName(tr(f"custom_rules_{key}"))
            field.setToolTip(tr(f"custom_rules_{key}_tip"))
            form.addRow(label, field)
        row = QHBoxLayout()
        for button in (self.add, self.update_rule, self.remove):
            row.addWidget(button)
        row.addStretch(1)
        side = QVBoxLayout()
        side.addLayout(form)
        side.addLayout(row)
        side.addWidget(self.status)
        side.addStretch(1)
        middle = QHBoxLayout()
        middle.addWidget(self.list, 2)
        middle.addLayout(side, 3)
        layout = QVBoxLayout(self)
        layout.addWidget(hint)
        layout.addLayout(middle, 1)
        layout.addWidget(self.buttons)

    def rules(self) -> tuple[CustomRule, ...]:
        """The rules as listed."""
        return tuple(self._rules)

    def _form_rule(self) -> CustomRule:
        return CustomRule(self.name.text().strip(), _parts(self.folders.text()), _parts(self.files.text()),
                          self.in_folder.text().strip() or None, self.days.value())

    def _store(self, row: int | None) -> None:
        """Add the form as a rule, or replace rule ``row`` with it; an unusable one changes nothing."""
        rules = list(self._rules)
        try:
            rule = self._form_rule()
            if row is None:
                rules.append(rule)
            else:
                rules[row] = rule
            check_rules(tuple(rules))
        except ValueError:
            self.status.setText(tr("custom_rules_invalid"))
            return
        self._rules = rules
        self._fill(len(rules) - 1 if row is None else row)

    def _remove(self) -> None:
        row = self.list.currentRow()
        if 0 <= row < len(self._rules):
            del self._rules[row]
            self._fill(min(row, len(self._rules) - 1))

    def _fill(self, row: int) -> None:
        self.status.clear()
        self.list.blockSignals(True)
        self.list.clear()
        for rule in self._rules:
            item = QListWidgetItem(rule.name)
            item.setToolTip("; ".join((*rule.folders, *rule.files)))
            self.list.addItem(item)
        self.list.setCurrentRow(row)
        self.list.blockSignals(False)
        self._chosen(row)

    def _chosen(self, row: int) -> None:
        chosen = 0 <= row < len(self._rules)
        self.update_rule.setEnabled(chosen)
        self.remove.setEnabled(chosen)
        self.add.setEnabled(len(self._rules) < MAX_RULES)
        if not chosen:
            return
        rule = self._rules[row]
        self.name.setText(rule.name)
        self.folders.setText("; ".join(rule.folders))
        self.files.setText("; ".join(rule.files))
        self.in_folder.setText(rule.in_folder or "")
        self.days.setValue(rule.days)
