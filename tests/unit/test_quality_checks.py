"""Unit tests for infrastructure data-quality reporting."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd
from tests.conftest import raw_fixture_root

from india_football_funnel.data.infrastructure_pipeline import (
    build_public_sports_infrastructure_frame,
)
from india_football_funnel.data.quality_checks import build_data_quality_report


def test_quality_report_warns_for_stale_census_and_missing_states() -> None:
    frame, report, _source_hashes = build_public_sports_infrastructure_frame(raw_fixture_root())

    quality = build_data_quality_report(frame, report, reference_year=2026)

    assert quality.census_staleness_years == 15
    assert quality.stale_denominator_count == 10
    assert "Bihar" in quality.missing_canonical_states
    assert any("15 years" in warning for warning in quality.warnings)
    assert quality.blocking is False


def test_quality_report_detects_duplicate_state_rows() -> None:
    frame, report, _source_hashes = build_public_sports_infrastructure_frame(raw_fixture_root())
    duplicated = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)

    quality = build_data_quality_report(duplicated, report, reference_year=2026)

    assert quality.rows_per_state_min == 1
    assert quality.rows_per_state_max == 2
    assert any("Duplicate" in warning for warning in quality.warnings)


def test_quality_report_warns_when_reconciled_states_drop_from_join() -> None:
    frame, report, _source_hashes = build_public_sports_infrastructure_frame(raw_fixture_root())
    modified_report = replace(report, matched=[*report.matched, "Synthetic State"])

    quality = build_data_quality_report(frame, modified_report, reference_year=2026)

    assert "Synthetic State" not in frame["canonical_state_ut"].tolist()
    assert any("dropped" in warning for warning in quality.warnings)
