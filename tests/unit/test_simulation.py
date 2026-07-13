"""Unit tests for simulation."""

from __future__ import annotations

import numpy as np

from india_football_funnel.config import DEFAULT_RNG_SEED
from india_football_funnel.simulation.run_simulation import run_simulation
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
