"""Unit tests for canonical state/UT reconciliation."""

from __future__ import annotations

from india_football_funnel.data.state_names import (
    CANONICAL_STATES_UTS,
    STATE_ALIASES,
    StateReconciliationReport,
    normalize_state_name,
    reconcile_state_name,
)


def test_normalize_state_name_applies_aliases() -> None:
    assert normalize_state_name("Orissa") == "Odisha"
    assert normalize_state_name("Jammu & Kashmir") == "Jammu and Kashmir"


def test_reconcile_state_name_tracks_alias_usage() -> None:
    report = StateReconciliationReport()
    canonical = reconcile_state_name("Orissa", report)
    assert canonical == "Odisha"
    assert report.aliased["Orissa"] == "Odisha"
    assert "Odisha" in report.matched


def test_reconcile_state_name_records_unmatched() -> None:
    report = StateReconciliationReport()
    assert reconcile_state_name("Unknown Territory", report) is None
    assert report.unmatched == ["Unknown Territory"]
    assert report.has_blocking_issues


def test_canonical_states_include_post_2011_uts() -> None:
    assert "Ladakh" in CANONICAL_STATES_UTS
    assert "Odisha" in CANONICAL_STATES_UTS
    assert "Orissa" not in CANONICAL_STATES_UTS
    assert "Orissa" in STATE_ALIASES
