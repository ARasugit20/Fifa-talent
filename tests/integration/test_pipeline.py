"""End-to-end integration test for the full pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tests.conftest import fixture_path

from india_football_funnel.analysis.causal_regression import run_default_regressions
from india_football_funnel.analysis.funnel_metrics import (
    assert_funnel_monotonic,
    compute_all_state_summaries,
    compute_stage_counts,
)
from india_football_funnel.config import RETENTION_MAX, RETENTION_MIN
from india_football_funnel.data.loader import load_processed_parquet, process_raw_file
from india_football_funnel.simulation.run_simulation import run_simulation, write_simulation_outputs
from india_football_funnel.simulation.scenarios import baseline_scenario


@pytest.mark.integration
def test_full_pipeline_invariants(tmp_path: Path) -> None:
    raw_path = fixture_path("sample_funnel.csv")
    processed_path = tmp_path / "processed.parquet"
    process_raw_file(raw_path, processed_path)

    frame = load_processed_parquet(processed_path)
    assert (frame["census_year"] == 2011).all()

    for state in frame["state"].unique():
        counts = compute_stage_counts(frame, state)
        assert assert_funnel_monotonic(counts)

    summaries = compute_all_state_summaries(frame)
    assert len(summaries) == frame["state"].nunique()

    for summary in summaries:
        assert summary.census_year == 2011
        bounded_rates = [
            summary.stage_conversion["youth_population_to_participation"],
            summary.stage_conversion["participation_to_competitive_outcome"],
        ]
        for rate in bounded_rates:
            assert RETENTION_MIN <= rate <= RETENTION_MAX

    regressions = run_default_regressions(frame)
    assert len(regressions) >= 1

    sim_result = run_simulation(baseline_scenario(n_runs=50, years=5))
    parquet_path, json_path = write_simulation_outputs(sim_result, tmp_path / "results")

    assert parquet_path.exists()
    assert json_path.exists()
    summary = json.loads(json_path.read_text(encoding="utf-8"))
    assert summary["scenario_name"] == "baseline"
    assert summary["final_medals_mean"] > 0
