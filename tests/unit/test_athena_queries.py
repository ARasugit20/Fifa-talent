"""Unit tests for Athena query strings."""

from __future__ import annotations

from india_football_funnel.aws.athena_queries import ALL_QUERIES


def test_all_queries_present() -> None:
    assert len(ALL_QUERIES) >= 4
    assert "average_participation_by_state" in ALL_QUERIES
    assert "scenario_comparison_summary" in ALL_QUERIES


def test_queries_contain_expected_tables() -> None:
    assert "investment_outcome_observation" in ALL_QUERIES["average_participation_by_state"]
    assert "simulation_results" in ALL_QUERIES["scenario_comparison_summary"]
