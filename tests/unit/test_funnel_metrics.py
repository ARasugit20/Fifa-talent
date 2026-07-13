"""Unit tests for funnel metrics."""

from __future__ import annotations

import pandas as pd
from tests.conftest import load_fixture_csv

from india_football_funnel.analysis.funnel_metrics import (
    assert_funnel_monotonic,
    compute_funnel_summary,
    compute_stage_counts,
    expected_retention_for_transition,
    identify_bottleneck,
)
from india_football_funnel.config import RETENTION_MAX, RETENTION_MIN


def test_compute_stage_counts() -> None:
    frame = load_fixture_csv()
    counts = compute_stage_counts(frame, "Maharashtra")
    assert counts["youth_population"] == 1_100_000
    assert counts["participation"] == 14_000


def test_identify_bottleneck() -> None:
    counts = {
        "investment": 10000,
        "youth_population": 3500,
        "participation": 800,
        "competitive_outcome": 8,
    }
    bottleneck = identify_bottleneck(counts)
    assert bottleneck in {"youth_population", "participation", "competitive_outcome"}


def test_funnel_monotonic_fixture() -> None:
    frame = load_fixture_csv()
    for state in frame["state"].unique():
        counts = compute_stage_counts(frame, state)
        assert assert_funnel_monotonic(counts)


def test_retention_bounds() -> None:
    frame = load_fixture_csv()
    summary = compute_funnel_summary(frame, "Kerala")
    assert summary.census_year == 2011
    bounded_rates = [
        summary.stage_conversion["youth_population_to_participation"],
        summary.stage_conversion["participation_to_competitive_outcome"],
    ]
    for rate in bounded_rates:
        assert RETENTION_MIN <= rate <= RETENTION_MAX


def test_expected_retention_lookup() -> None:
    rate = expected_retention_for_transition("youth_population", "participation")
    assert 0.0 < rate < 1.0


def test_empty_state_returns_zero_counts() -> None:
    frame = pd.DataFrame(
        columns=[
            "state",
            "year",
            "census_year",
            "budget_allocation_inr",
            "youth_population_10_17",
            "participation_count",
            "medals",
        ]
    )
    counts = compute_stage_counts(frame, "Unknown")
    assert all(value == 0 for value in counts.values())
