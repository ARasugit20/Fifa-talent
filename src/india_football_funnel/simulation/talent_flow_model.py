"""Talent flow Monte Carlo model."""

from __future__ import annotations

import logging

import numpy as np
from numpy.typing import NDArray

from india_football_funnel.config import (
    BUDGET_EFFECT_MEAN,
    BUDGET_EFFECT_STD,
    PARTICIPATION_GROWTH_RATE_MEAN,
    PARTICIPATION_GROWTH_RATE_STD,
)
from india_football_funnel.models import ScenarioParams

logger = logging.getLogger(__name__)


def _clip_rate(rate: float) -> float:
    return float(np.clip(rate, 0.0, 1.0))


def simulate_single_path(params: ScenarioParams, rng: np.random.Generator) -> list[float]:
    """Simulate one Monte Carlo path returning medals per year."""
    if params.growth_rate_override is not None:
        growth_mean = params.growth_rate_override
    else:
        growth_mean = PARTICIPATION_GROWTH_RATE_MEAN
    medals_by_year: list[float] = []
    youth_population = float(params.base_youth_population)
    participation_rate = params.baseline_participation_rate

    for _year in range(params.years):
        growth = rng.normal(growth_mean, PARTICIPATION_GROWTH_RATE_STD)
        youth_population *= max(1.0 + growth, 0.0)

        budget_multiplier = 1.0
        if params.intervention_enabled and params.target_budget_per_capita is not None:
            budget_gap = max(params.target_budget_per_capita - params.budget_per_capita, 0.0)
            budget_multiplier += min(budget_gap / max(params.budget_per_capita, 1.0), 1.0)

        uplift = 0.0
        if params.intervention_enabled:
            uplift = rng.normal(BUDGET_EFFECT_MEAN, BUDGET_EFFECT_STD) * budget_multiplier

        simulated_participation_rate = _clip_rate(participation_rate + uplift)
        participants = youth_population * simulated_participation_rate
        medals = participants * max(params.baseline_medals_per_participant, 0.0)
        medals_by_year.append(medals)

    return medals_by_year


def run_monte_carlo_paths(params: ScenarioParams) -> NDArray[np.float64]:
    """Run n_runs Monte Carlo paths; returns shape (n_runs, years)."""
    rng = np.random.default_rng(params.rng_seed)
    logger.info(
        "Starting Monte Carlo: scenario=%s runs=%d years=%d seed=%d",
        params.name,
        params.n_runs,
        params.years,
        params.rng_seed,
    )
    paths: list[list[float]] = []
    for _ in range(params.n_runs):
        paths.append(simulate_single_path(params, rng))
    return np.array(paths, dtype=float)
