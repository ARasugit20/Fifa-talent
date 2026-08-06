"""Unit tests for simulation."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from india_football_funnel.config import DEFAULT_RNG_SEED
from india_football_funnel.simulation.run_simulation import (
    load_simulation_summary,
    run_simulation,
    simulation_result_to_frame,
    write_simulation_outputs,
)
from india_football_funnel.simulation.scenarios import (
    baseline_scenario,
    get_scenario_by_name,
    intervention_scenario,
)
from india_football_funnel.simulation.talent_flow_model import run_monte_carlo_paths


def test_baseline_simulation_deterministic() -> None:
    params = baseline_scenario(n_runs=50, rng_seed=DEFAULT_RNG_SEED)
    result_a = run_simulation(params)
    result_b = run_simulation(params)
    assert result_a.final_medals_mean == result_b.final_medals_mean


def test_intervention_exceeds_baseline_on_average() -> None:
    baseline = run_simulation(baseline_scenario(n_runs=200, rng_seed=7))
    intervention = run_simulation(intervention_scenario(n_runs=200, rng_seed=7))
    assert intervention.final_medals_mean >= baseline.final_medals_mean


def test_simulation_output_sane_range() -> None:
    result = run_simulation(baseline_scenario(n_runs=100))
    assert result.final_medals_mean > 0
    assert result.final_medals_std >= 0
    assert result.assumption_based is True
    assert result.uncalibrated is True
    for year_result in result.annual_results:
        assert year_result.p10_medals <= year_result.mean_medals
        assert year_result.mean_medals <= year_result.p90_medals


def test_monte_carlo_paths_shape() -> None:
    params = baseline_scenario(n_runs=20, years=5)
    paths = run_monte_carlo_paths(params)
    assert paths.shape == (20, 5)
    assert np.all(paths >= 0)


def test_get_scenario_by_name() -> None:
    scenario = get_scenario_by_name("high_participation_growth")
    assert scenario.name == "high_participation_growth"
    assert scenario.growth_rate_override == 0.06


def test_participation_rate_compounds_across_years(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "india_football_funnel.simulation.talent_flow_model.PARTICIPATION_GROWTH_RATE_MEAN",
        0.0,
    )
    monkeypatch.setattr(
        "india_football_funnel.simulation.talent_flow_model.PARTICIPATION_GROWTH_RATE_STD",
        0.0,
    )
    monkeypatch.setattr(
        "india_football_funnel.simulation.talent_flow_model.BUDGET_EFFECT_MEAN",
        0.01,
    )
    monkeypatch.setattr(
        "india_football_funnel.simulation.talent_flow_model.BUDGET_EFFECT_STD",
        0.0,
    )

    params = intervention_scenario(n_runs=1, years=2, rng_seed=42, base_population=10_000)
    paths = run_monte_carlo_paths(params)

    assert paths[0, 1] > paths[0, 0]


def test_simulation_outputs_include_uncalibrated_labels(tmp_path: Path) -> None:
    result = run_simulation(baseline_scenario(n_runs=10, years=2))
    parquet_path, json_path = write_simulation_outputs(result, tmp_path)

    frame = simulation_result_to_frame(result)
    assert frame["assumption_based"].all()
    assert frame["uncalibrated"].all()

    summary = json.loads(json_path.read_text(encoding="utf-8"))
    assert summary["assumption_based"] is True
    assert summary["uncalibrated"] is True
    assert summary["assumption_registry_version"] == "v1"
    assert {assumption["key"] for assumption in summary["assumptions"]} >= {
        "baseline_participation_rate",
        "PARTICIPATION_GROWTH_RATE_MEAN",
        "BUDGET_EFFECT_MEAN",
    }
    assert parquet_path.exists()


def test_simulation_clips_zero_participation_and_non_negative_medals() -> None:
    params = baseline_scenario(n_runs=10, years=3).model_copy(
        update={"baseline_participation_rate": 0.0, "baseline_medals_per_participant": 0.0}
    )

    paths = run_monte_carlo_paths(params)

    assert np.all(paths >= 0.0)
    assert np.all(paths == 0.0)


def test_simulation_accepts_extreme_medals_per_participant() -> None:
    params = baseline_scenario(n_runs=5, years=2).model_copy(
        update={"baseline_medals_per_participant": 1_000_000.0}
    )

    result = run_simulation(params)

    assert result.final_medals_mean >= 0.0


def test_load_simulation_summary_without_label_fields(tmp_path: Path) -> None:
    summary_path = tmp_path / "legacy_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "scenario_name": "baseline",
                "n_runs": 10,
                "years": 2,
                "annual_results": [
                    {
                        "year": 1,
                        "mean_medals": 5.0,
                        "p10_medals": 3.0,
                        "p90_medals": 7.0,
                        "mean_participation_rate": 0.012,
                    }
                ],
                "final_medals_mean": 6.0,
                "final_medals_std": 1.0,
            }
        ),
        encoding="utf-8",
    )

    result = load_simulation_summary(summary_path)
    assert result.assumption_based is True
    assert result.uncalibrated is True
