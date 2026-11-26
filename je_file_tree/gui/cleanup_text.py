"""Translate the evidence, risk and rebuild instructions attached to clean-up rules."""

from je_file_tree.core.cleanup import CUSTOM_PREFIX, DETAILS, RuleDetails
from je_file_tree.gui.i18n import tr


_CUSTOM = RuleDetails("custom", 0, "manual", "custom", "custom")


def title(key: str) -> str:
    """The name of a clean-up group; rules the user wrote carry their own."""
    if key.startswith(CUSTOM_PREFIX):
        return tr("cleanup_custom", name=key.removeprefix(CUSTOM_PREFIX))
    return tr(f"cleanup_{key}")


def explanation(key: str, details: RuleDetails | None = None) -> str:
    """Full rule explanation for group tooltips and the review queue."""
    custom = key.startswith(CUSTOM_PREFIX)
    details = details or (_CUSTOM if custom else DETAILS[key])
    return tr("cleanup_evidence", category=tr(f"cleanup_category_{details.category}"),
              days=str(details.minimum_age), risk=tr(f"cleanup_risk_{details.risk}"),
              evidence=tr("cleanup_custom_tip" if custom else f"cleanup_{key}_tip"),
              rebuild=tr(f"cleanup_rebuild_{details.rebuild}"))
