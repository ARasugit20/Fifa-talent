"""Canonical state/UT naming and alias reconciliation."""

from __future__ import annotations

from dataclasses import dataclass, field

CANONICAL_STATES_UTS: tuple[str, ...] = (
    "Andaman and Nicobar Islands",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chandigarh",
    "Chhattisgarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Ladakh",
    "Lakshadweep",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Puducherry",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
)

STATE_ALIASES: dict[str, str] = {
    "Orissa": "Odisha",
    "NCT of Delhi": "Delhi",
    "National Capital Territory of Delhi": "Delhi",
    "Jammu & Kashmir": "Jammu and Kashmir",
    "Dadra & Nagar Haveli and Daman & Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "The Dadra And Nagar Haveli And Daman And Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "Pondicherry": "Puducherry",
    "Andaman & Nicobar Islands": "Andaman and Nicobar Islands",
}

# Ladakh did not exist as a separate UT in Census 2011; exclude from joins unless
# explicitly mapped to Jammu and Kashmir for denominator purposes.
EXCLUDED_FROM_CENSUS_2011_DENOMINATOR: frozenset[str] = frozenset({"Ladakh"})


@dataclass
class StateReconciliationReport:
    """Summary of state-name matching across source files."""

    matched: list[str] = field(default_factory=list)
    aliased: dict[str, str] = field(default_factory=dict)
    unmatched: list[str] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)

    @property
    def has_blocking_issues(self) -> bool:
        return bool(self.unmatched)


def normalize_state_name(raw_name: str) -> str:
    """Normalize whitespace and apply known aliases."""
    cleaned = " ".join(raw_name.strip().split())
    return STATE_ALIASES.get(cleaned, cleaned)


def reconcile_state_name(
    raw_name: str,
    report: StateReconciliationReport,
) -> str | None:
    """Map a source state label to a canonical state/UT name."""
    cleaned = " ".join(raw_name.strip().split())
    normalized = STATE_ALIASES.get(cleaned, cleaned)
    if normalized in CANONICAL_STATES_UTS:
        if cleaned != normalized:
            report.aliased[cleaned] = normalized
        if normalized not in report.matched:
            report.matched.append(normalized)
        return normalized
    if normalized not in report.unmatched:
        report.unmatched.append(normalized)
    return None
