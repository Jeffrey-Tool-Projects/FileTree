"""The Free up space dialog: a plan from ``core.reclaim`` towards an amount of space the user picks.

It proposes and nothing else. Nothing is checked when it opens (the Clean up tab pre-selects nothing on
its own either), and the user's own large files are a separate list of options. *Review and move to
Recycle Bin…* closes the dialog and hands exactly the checked entries to ``MainWindow.move_to_trash``,
which asks every question it always asks; a declined question moves nothing.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QHBoxLayout, QLabel,
                               QProgressBar, QPushButton, QSpinBox, QTreeWidget, QTreeWidgetItem,
                               QTreeWidgetItemIterator, QVBoxLayout, QWidget)

from je_file_tree.core.formatting import format_count, format_size
from je_file_tree.core.node import Node
from je_file_tree.core.reclaim import (CLEANUP, DUPLICATES, PlanStep, ReclaimPlan, ReclaimSources, build_plan,
                                       free_share_target)
from je_file_tree.gui.advice_text import dot
from je_file_tree.gui.cleanup_text import explanation
from je_file_tree.gui.delegates import ShareBarDelegate
from je_file_tree.gui.i18n import tr
from je_file_tree.gui.text_scale import text_scaled
from je_file_tree.gui.tree_model import NODE_ROLE, SHARE_ROLE
from je_file_tree.gui.window_fit import fit_window

if TYPE_CHECKING:
    from je_file_tree.gui.results_view import ResultsView

GB = 1024 ** 3  # the unit the size columns call GB (``core.formatting`` steps by 1,024)
PRESETS_GB = (1, 5, 10, 50)
CUSTOM, SHARE = "custom", "share"
_ENTRY, _SIZE, _TOTAL = 0, 1, 2
_METER_STEPS = 1000


def reclaim_sources(results: ResultsView) -> ReclaimSources | None:
    """What the scan on screen offers a plan: its clean-up suggestions once known, duplicate groups whose
    kept copy the user chose, its largest files and its drive's capacity; None without a scan."""
    outcome = results.outcome
    if outcome is None:
        return None
    groups = tuple(results.cleanup.groups) if results.cleanup.proposal_summary is not None else ()
    capacity = outcome.capacity
    return ReclaimSources(outcome.result.root, results.adviser, groups, results.duplicates.link_groups,
                          tuple(outcome.largest), capacity.total if capacity is not None else None,
                          capacity.free if capacity is not None else None)


class ReclaimDialog(QDialog):
    """Pick an amount; see a ranked plan to check entries from; send the checked ones for review."""

    selected = Signal(object)
    review_requested = Signal(object)

    def __init__(self, sources: ReclaimSources, unit: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.unit = unit
        self._sources = sources
        self._plan: ReclaimPlan | None = None
        self._base: ReclaimPlan | None = None
        fit_window(self, 980, 640)
        self.hint, self.status, self.note, self.drive, self.selection = (QLabel() for _ in range(5))
        for label in (self.hint, self.status, self.note):
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.PlainText)
        self._target_label = QLabel()
        self.preset = QComboBox()
        self.custom = QDoubleSpinBox()
        self.custom.setRange(0.1, 1_000_000.0)
        self.custom.setDecimals(1)
        self.custom.setValue(10.0)
        self.custom.setSuffix(" GB")
        self.share = QSpinBox()
        self.share.setRange(1, 99)
        self.share.setValue(20)
        self.share.setSuffix(" %")
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setItemDelegateForColumn(_SIZE, ShareBarDelegate(self.tree))
        self.tree.setColumnWidth(_ENTRY, text_scaled(560))
        self.tree.setColumnWidth(_SIZE, text_scaled(140))
        self.meter = QProgressBar()
        self.meter.setRange(0, _METER_STEPS)
        self.meter.setTextVisible(False)
        self.show_button, self.review_button = QPushButton(), QPushButton()
        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self._recount = QTimer(self)
        self._recount.setSingleShot(True)
        self._recount.setInterval(0)  # one recount after a check box changed many entries at once
        self._assemble()
        self._connect()
        self.retranslate()

    # --- public API -------------------------------------------------------

    @property
    def plan(self) -> ReclaimPlan | None:
        """The plan on screen."""
        return self._plan

    def target(self) -> int:
        """The bytes asked for: a preset, the custom amount or what the drive needs to reach its free share."""
        choice = self.preset.currentData()
        if choice == CUSTOM:
            return round(self.custom.value() * GB)
        if choice == SHARE:
            total, free = self._sources.total, self._sources.free
            return free_share_target(self.share.value(), total, free) if total and free is not None else 0
        return int(choice or 0) * GB

    def checked_nodes(self) -> list[Node]:
        """The checked entries, in plan order."""
        found: list[Node] = []
        iterator = QTreeWidgetItemIterator(self.tree)
        while (item := iterator.value()) is not None:
            node = item.data(_ENTRY, NODE_ROLE)
            if isinstance(node, Node) and item.checkState(_ENTRY) == Qt.CheckState.Checked:
                found.append(node)
            iterator += 1
        return found

    def selected_size(self) -> int:
        """The estimate for the checked entries, each counted once."""
        return self._plan.size_of(self.checked_nodes()) if self._plan is not None else 0

    def update_sources(self, sources: ReclaimSources | None) -> None:
        """Rebuild from newer suggestions (the clean-up search finished); the checks that still apply stay."""
        if sources is None or (sources.adviser is self._sources.adviser and sources.root is self._sources.root
                               and tuple(sources.duplicates) == tuple(self._sources.duplicates)):
            return
        self._sources = sources
        self._base = None
        self._fill_presets()
        self.rebuild()

    def rebuild(self) -> None:
        """Build the plan for the current target and show it, keeping the checks of entries still listed."""
        checked = set(self.checked_nodes())
        if self._base is None:  # the steps do not depend on the target: build them once per set of sources
            self._base = build_plan(0, self._sources)
        self._plan = plan = replace(self._base, target=max(self.target(), 0))
        self.tree.blockSignals(True)
        self.tree.clear()
        biggest = max((step.size for step in plan.steps), default=0)
        for step in plan.steps:
            self._add_step(step, checked, biggest)
        if plan.options is not None:
            self._add_step(plan.options, checked, max(biggest, plan.options.size))
        self.tree.expandAll()
        self.tree.blockSignals(False)
        self._target_controls()
        self.status.setText(self._status_text(plan))
        self._update_selection()

    def show_current(self) -> None:
        """Show the entry under the cursor in the folder tree; the plan stays open."""
        item = self.tree.currentItem()
        node = item.data(_ENTRY, NODE_ROLE) if item is not None else None
        if isinstance(node, Node):
            self.selected.emit(node)

    def review(self) -> None:
        """Close and hand exactly the checked entries to the Recycle Bin flow, which asks first."""
        nodes = self.checked_nodes()
        if not nodes:
            return
        self.accept()
        self.review_requested.emit(nodes)

    def retranslate(self) -> None:
        """Re-read every translated text and rebuild the plan's wording."""
        self.setWindowTitle(tr("reclaim_title"))
        self.hint.setText(tr("reclaim_hint"))
        self._target_label.setText(tr("reclaim_target"))
        self.note.setText(tr("reclaim_note"))
        self.tree.setHeaderLabels([tr("reclaim_column_entry"), tr("column_size"), tr("reclaim_column_total")])
        self.show_button.setText(tr("reclaim_show"))
        self.review_button.setText(tr("reclaim_review"))
        self._fill_presets()
        self.rebuild()

    # --- building ---------------------------------------------------------

    def _assemble(self) -> None:
        target = QHBoxLayout()
        for widget in (self._target_label, self.preset, self.custom, self.share, self.drive):
            target.addWidget(widget)
        target.addStretch(1)
        meter = QHBoxLayout()
        meter.addWidget(self.selection)
        meter.addWidget(self.meter, 1)
        buttons = QHBoxLayout()
        buttons.addWidget(self.show_button)
        buttons.addStretch(1)
        buttons.addWidget(self.review_button)
        buttons.addWidget(self._buttons)
        layout = QVBoxLayout(self)
        layout.addWidget(self.hint)
        layout.addLayout(target)
        layout.addWidget(self.status)
        layout.addWidget(self.tree, 1)
        layout.addLayout(meter)
        layout.addWidget(self.note)
        layout.addLayout(buttons)

    def _connect(self) -> None:
        self.preset.currentIndexChanged.connect(lambda _index: self.rebuild())
        self.custom.valueChanged.connect(lambda _value: self.rebuild())
        self.share.valueChanged.connect(lambda _value: self.rebuild())
        self.tree.itemChanged.connect(lambda _item, _column: self._recount.start())
        self.tree.currentItemChanged.connect(lambda _current, _previous: self._update_buttons())
        self.tree.itemDoubleClicked.connect(lambda _item, _column: self.show_current())
        self._recount.timeout.connect(self._update_selection)
        self.show_button.clicked.connect(self.show_current)
        self.review_button.clicked.connect(self.review)
        self._buttons.rejected.connect(self.reject)

    def _fill_presets(self) -> None:
        """The amounts to choose from; the free share only when the drive's capacity is known."""
        current = self.preset.currentData()
        self.preset.blockSignals(True)
        self.preset.clear()
        for amount in PRESETS_GB:
            self.preset.addItem(f"{amount} GB", amount)
        self.preset.addItem(tr("reclaim_custom"), CUSTOM)
        if self._sources.total and self._sources.free is not None:
            self.preset.addItem(tr("reclaim_share"), SHARE)
        position = self.preset.findData(current) if current is not None else -1
        self.preset.setCurrentIndex(position if position >= 0 else 0)
        self.preset.blockSignals(False)

    def _add_step(self, step: PlanStep, checked: set[Node], biggest: int) -> None:
        item = QTreeWidgetItem(self.tree)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsAutoTristate)
        item.setCheckState(_ENTRY, Qt.CheckState.Unchecked)  # before the entries, so it sets none of them
        item.setIcon(_ENTRY, dot(step.risk))
        item.setText(_ENTRY, tr("reclaim_step", risk=tr(f"advice_{step.risk}"), title=self._step_title(step),
                                count=format_count(len(step.entries))))
        item.setToolTip(_ENTRY, self._step_tip(step))
        self._size_cells(item, step.size, biggest)
        item.setText(_TOTAL, self._total_text(step))
        largest = max(entry.counted for entry in step.entries)
        for entry in step.entries:
            child = QTreeWidgetItem(item)
            child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            child.setData(_ENTRY, NODE_ROLE, entry.node)
            child.setText(_ENTRY, entry.node.path or entry.node.name)
            child.setToolTip(_ENTRY, entry.node.path or entry.node.name)
            child.setCheckState(_ENTRY, Qt.CheckState.Checked if entry.node in checked else Qt.CheckState.Unchecked)
            self._size_cells(child, entry.counted, largest)
            if entry.counted != entry.size:
                child.setToolTip(_SIZE, tr("reclaim_overlap", size=format_size(entry.size, self.unit)))
        if step.more:
            more = QTreeWidgetItem(item)
            more.setFlags(Qt.ItemFlag.ItemIsEnabled)
            more.setText(_ENTRY, tr("reclaim_more", count=format_count(step.more)))

    def _size_cells(self, item: QTreeWidgetItem, size: int, biggest: int) -> None:
        item.setText(_SIZE, format_size(size, self.unit))
        item.setData(_SIZE, SHARE_ROLE, size / biggest if biggest > 0 else 0.0)

    def _step_title(self, step: PlanStep) -> str:
        if step.category == CLEANUP:
            return tr(f"cleanup_{step.key}")
        return tr("reclaim_duplicates") if step.category == DUPLICATES else tr("reclaim_options")

    def _step_tip(self, step: PlanStep) -> str:
        if step.category == CLEANUP:
            return explanation(step.key)
        return tr("reclaim_duplicates_tip") if step.category == DUPLICATES else tr("advice_personal_tip")

    def _total_text(self, step: PlanStep) -> str:
        plan = self._plan
        target = format_size(plan.target if plan is not None else 0, self.unit)
        key = "reclaim_running" if plan is None or step is plan.options or plan.needed(step) else "reclaim_beyond"
        return tr(key, total=format_size(step.total, self.unit), target=target)

    def _status_text(self, plan: ReclaimPlan) -> str:
        found, target = format_size(plan.total, self.unit), format_size(plan.target, self.unit)
        if not plan.steps and plan.options is None:
            lines = [tr("reclaim_empty")]
        elif plan.reached:
            lines = [tr("reclaim_reached", found=found, target=target)]
        else:
            lines = [tr("reclaim_short", found=found, short=format_size(plan.shortfall, self.unit), target=target)]
        if not self._sources.ready:
            lines.append(tr("reclaim_waiting"))
        if plan.undecided_duplicates:
            lines.append(tr("reclaim_undecided", count=format_count(plan.undecided_duplicates)))
        return "\n".join(lines)

    def _target_controls(self) -> None:
        choice = self.preset.currentData()
        self.custom.setVisible(choice == CUSTOM)
        self.share.setVisible(choice == SHARE)
        self.drive.setVisible(choice == SHARE)
        total, free = self._sources.total, self._sources.free
        if total and free is not None:
            self.drive.setText(tr("reclaim_drive", free=format_size(free, self.unit),
                                  total=format_size(total, self.unit)))

    def _update_selection(self) -> None:
        plan = self._plan
        nodes = self.checked_nodes()
        size = plan.size_of(nodes) if plan is not None else 0
        target = plan.target if plan is not None else 0
        share = 1.0 if target <= 0 else min(size / target, 1.0)
        self.meter.setValue(round(share * _METER_STEPS))
        self.selection.setText(tr("reclaim_selected", selected=format_size(size, self.unit),
                                  target=format_size(target, self.unit)))
        self.review_button.setEnabled(bool(nodes))
        self._update_buttons()

    def _update_buttons(self) -> None:
        item = self.tree.currentItem()
        self.show_button.setEnabled(item is not None and isinstance(item.data(_ENTRY, NODE_ROLE), Node))
