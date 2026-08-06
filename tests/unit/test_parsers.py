"""Unit tests for manual raw dataset parsers."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.conftest import raw_fixture_root

from india_football_funnel.data.parsers.census import parse_state_denominators
from india_football_funnel.data.parsers.khelo_india import parse_financial_assistance
from india_football_funnel.data.parsers.mdsd import parse_grantee_amounts, parse_state_wise_progress
from india_football_funnel.data.provenance import load_provenance
from india_football_funnel.data.state_names import StateReconciliationReport


def test_parse_state_wise_progress() -> None:
    report = StateReconciliationReport()
    records = parse_state_wise_progress(
        raw_fixture_root() / "mdsd/state_wise_progress.csv",
        report=report,
    )
    assert len(records) == 10
    assert records[0].projects_total >= records[0].projects_completed
    assert not report.unmatched


def test_parse_grantee_amounts_converts_crore_to_inr() -> None:
    report = StateReconciliationReport()
    records = parse_grantee_amounts(
        raw_fixture_root() / "mdsd/grantee_amounts.csv",
        report=report,
    )
    kerala = next(record for record in records if record.canonical_state_ut == "Kerala")
    assert kerala.amount_sanctioned_inr == pytest.approx(45.0 * 10_000_000)


def test_parse_financial_assistance() -> None:
    report = StateReconciliationReport()
    records = parse_financial_assistance(
        raw_fixture_root() / "khelo_india/financial_assistance.csv",
        report=report,
    )
    assert len(records) == 10
    assert records[0].financial_assistance_inr > 0


def test_parse_state_denominators_flags_stale_denominator() -> None:
    report = StateReconciliationReport()
    records = parse_state_denominators(
        raw_fixture_root() / "census/state_population_2011.csv",
        report=report,
    )
    assert all(record.denominator_is_stale for record in records)
    assert all(
        "total_population_2011_state_ut" in record.denominator_definition for record in records
    )


def test_unmapped_state_name_fails_reconciliation() -> None:
    from india_football_funnel.data.state_names import reconcile_state_name

    report = StateReconciliationReport()
    assert reconcile_state_name("Unknown Territory", report) is None
    assert report.unmatched == ["Unknown Territory"]


@pytest.mark.parametrize(
    ("parser", "filename", "columns"),
    [
        (parse_state_wise_progress, "progress.csv", "state,projects_total\nKerala,1\n"),
        (parse_grantee_amounts, "amounts.csv", "state,amount_sanctioned\nKerala,1\n"),
        (parse_financial_assistance, "assistance.csv", "state,financial_assistance\nKerala,1\n"),
        (parse_state_denominators, "census.csv", "state,denominator_value\nKerala,1\n"),
    ],
)
def test_parsers_reject_missing_required_columns(
    parser: object,
    filename: str,
    columns: str,
    tmp_path: Path,
) -> None:
    path = tmp_path / filename
    path.write_text(columns, encoding="utf-8")
    provenance = load_provenance(raw_fixture_root() / "census/state_population_2011.csv")

    with pytest.raises(ValueError, match="missing required columns"):
        parser(path, provenance=provenance)  # type: ignore[operator]
