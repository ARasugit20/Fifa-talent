"""Versioned assumption registry for uncalibrated simulation outputs."""

from __future__ import annotations

from india_football_funnel.config import (
    ASSUMPTION_REGISTRY_VERSION,
    BUDGET_EFFECT_MEAN,
    BUDGET_EFFECT_STD,
    PARTICIPATION_GROWTH_RATE_MEAN,
    PARTICIPATION_GROWTH_RATE_STD,
)
from india_football_funnel.models import Assumption, ScenarioParams


def _scenario_assumption(
    key: str,
    value: float | int | str | bool | None,
    unit: str,
    rationale: str,
    sensitivity_low: float | None = None,
    sensitivity_high: float | None = None,
) -> Assumption:
    """Build a documented scenario-derived assumption."""
    return Assumption(
        key=key,
        value=value,
        unit=unit,
        source="scenario",
        rationale=rationale,
        sensitivity_low=sensitivity_low,
        sensitivity_high=sensitivity_high,
    )


def build_assumption_manifest(params: ScenarioParams) -> list[Assumption]:
    """Capture every scenario and config input that governs a simulation run."""
    return [
        _scenario_assumption(
            "baseline_participation_rate",
            params.baseline_participation_rate,
            "share_of_youth_population",
            "Initial participation share supplied by the selected scenario.",
            0.0,
            1.0,
        ),
        _scenario_assumption(
            "baseline_medals_per_participant",
            params.baseline_medals_per_participant,
            "medals_per_participant",
            "Initial medal yield supplied by the selected scenario.",
            0.0,
            None,
        ),
        _scenario_assumption(
            "budget_per_capita",
            params.budget_per_capita,
            "INR_per_person",
            "Baseline per-capita budget supplied by the selected scenario.",
            0.0,
            None,
        ),
        _scenario_assumption(
            "target_budget_per_capita",
            params.target_budget_per_capita,
            "INR_per_person",
            "Optional intervention target; null means no target budget is modeled.",
            0.0,
            None,
        ),
        _scenario_assumption(
            "growth_rate_override",
            params.growth_rate_override,
            "annual_rate",
            "Optional scenario override for the configured participation growth mean.",
            None,
            None,
        ),
        _scenario_assumption(
            "years",
            params.years,
            "years",
            "Simulation horizon supplied by the selected scenario.",
            1.0,
            50.0,
        ),
        _scenario_assumption(
            "n_runs",
            params.n_runs,
            "monte_carlo_runs",
            "Number of seeded Monte Carlo paths in the selected scenario.",
            1.0,
            100_000.0,
        ),
        _scenario_assumption(
            "rng_seed",
            params.rng_seed,
            "seed",
            "Deterministic seed used to reproduce the scenario output.",
        ),
        Assumption(
            key="PARTICIPATION_GROWTH_RATE_MEAN",
            value=PARTICIPATION_GROWTH_RATE_MEAN,
            unit="annual_rate",
            source="config",
            rationale=(
                "Configured mean annual participation growth; " "not calibrated from observed data."
            ),
            sensitivity_low=0.0,
            sensitivity_high=0.1,
        ),
        Assumption(
            key="PARTICIPATION_GROWTH_RATE_STD",
            value=PARTICIPATION_GROWTH_RATE_STD,
            unit="annual_rate_stddev",
            source="config",
            rationale="Configured uncertainty around annual participation growth.",
            sensitivity_low=0.0,
            sensitivity_high=0.05,
        ),
        Assumption(
            key="BUDGET_EFFECT_MEAN",
            value=BUDGET_EFFECT_MEAN,
            unit="participation_rate_uplift",
            source="config",
            rationale="Configured intervention uplift; not a causal estimate.",
            sensitivity_low=0.0,
            sensitivity_high=0.2,
        ),
        Assumption(
            key="BUDGET_EFFECT_STD",
            value=BUDGET_EFFECT_STD,
            unit="participation_rate_uplift_stddev",
            source="config",
            rationale="Configured uncertainty around the intervention uplift.",
            sensitivity_low=0.0,
            sensitivity_high=0.1,
        ),
        Assumption(
            key="assumption_registry_version",
            value=ASSUMPTION_REGISTRY_VERSION,
            unit="version",
            source="derived",
            rationale="Version identifier for the assumption registry schema and defaults.",
        ),
    ]
