"""Predefined simulation scenarios."""

from __future__ import annotations

from india_football_funnel.config import (
    DEFAULT_MONTE_CARLO_RUNS,
    DEFAULT_RNG_SEED,
    DEFAULT_SIMULATION_YEARS,
)
from india_football_funnel.models import ScenarioParams


def baseline_scenario(
    base_population: int = 50_000,
    years: int = DEFAULT_SIMULATION_YEARS,
    n_runs: int = DEFAULT_MONTE_CARLO_RUNS,
    rng_seed: int = DEFAULT_RNG_SEED,
) -> ScenarioParams:
    """Status-quo public investment/outcome scenario."""
    return ScenarioParams(
        name="baseline",
        years=years,
        n_runs=n_runs,
        rng_seed=rng_seed,
        base_youth_population=base_population,
        baseline_participation_rate=0.012,
        baseline_medals_per_participant=0.08,
        budget_per_capita=120.0,
        intervention_enabled=False,
    )


def intervention_scenario(
    base_population: int = 50_000,
    years: int = DEFAULT_SIMULATION_YEARS,
    n_runs: int = DEFAULT_MONTE_CARLO_RUNS,
    rng_seed: int = DEFAULT_RNG_SEED,
) -> ScenarioParams:
    """Scenario where budget per capita moves toward a top-quartile state."""
    return ScenarioParams(
        name="top_quartile_budget",
        years=years,
        n_runs=n_runs,
        rng_seed=rng_seed,
        base_youth_population=base_population,
        baseline_participation_rate=0.012,
        baseline_medals_per_participant=0.08,
        budget_per_capita=120.0,
        target_budget_per_capita=240.0,
        intervention_enabled=True,
    )


def high_growth_scenario(
    base_population: int = 50_000,
    years: int = DEFAULT_SIMULATION_YEARS,
    n_runs: int = DEFAULT_MONTE_CARLO_RUNS,
    rng_seed: int = DEFAULT_RNG_SEED,
) -> ScenarioParams:
    """Scenario with elevated youth sports participation growth."""
    return ScenarioParams(
        name="high_participation_growth",
        years=years,
        n_runs=n_runs,
        rng_seed=rng_seed,
        base_youth_population=base_population,
        baseline_participation_rate=0.012,
        baseline_medals_per_participant=0.08,
        budget_per_capita=120.0,
        intervention_enabled=False,
        growth_rate_override=0.06,
    )


def get_scenario_by_name(name: str, rng_seed: int = DEFAULT_RNG_SEED) -> ScenarioParams:
    """Resolve a scenario by name."""
    scenarios = {
        "baseline": baseline_scenario(rng_seed=rng_seed),
        "top_quartile_budget": intervention_scenario(rng_seed=rng_seed),
        "high_participation_growth": high_growth_scenario(rng_seed=rng_seed),
    }
    if name not in scenarios:
        msg = f"Unknown scenario: {name}"
        raise ValueError(msg)
    return scenarios[name]
