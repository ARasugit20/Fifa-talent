"""Funnel metrics computation."""

from __future__ import annotations

import logging

import pandas as pd

from india_football_funnel.config import FUNNEL_STAGES, MIN_COHORT_SIZE, STAGE_CONVERSION_BASELINES
from india_football_funnel.models import InvestmentOutcomeSummary

logger = logging.getLogger(__name__)


def compute_stage_counts(frame: pd.DataFrame, state: str) -> dict[str, int]:
    """Aggregate public-data stage values for a state.

    Values are aggregate counts/amounts, not individual player records.
    """
    subset = frame[frame["state"] == state]
    return {
        "investment": int(subset["budget_allocation_inr"].sum()),
        "youth_population": int(subset["youth_population_10_17"].sum()),
        "participation": int(subset["participation_count"].sum()),
        "competitive_outcome": int(subset["medals"].sum()),
    }


def compute_stage_retention(frame: pd.DataFrame, state: str) -> dict[str, float]:
    """Compute stage-conversion rates for the new 4-stage public funnel."""
    values = compute_stage_counts(frame, state)
    youth_population = values["youth_population"]
    participation = values["participation"]
    medals = values["competitive_outcome"]
    investment = values["investment"]
    return {
        "investment_to_youth_population": 0.0
        if youth_population == 0
        else investment / youth_population,
        "youth_population_to_participation": 0.0
        if youth_population == 0
        else participation / youth_population,
        "participation_to_competitive_outcome": 0.0
        if participation == 0
        else medals / participation,
    }


def identify_bottleneck(stage_counts: dict[str, int]) -> str:
    """Identify the stage with the largest proportional drop or weakest conversion."""
    max_drop = -1.0
    bottleneck = FUNNEL_STAGES[0]
    ordered_counts = [stage_counts.get(stage, 0) for stage in FUNNEL_STAGES]
    for idx in range(1, len(FUNNEL_STAGES)):
        previous = ordered_counts[idx - 1]
        current = ordered_counts[idx]
        if previous <= 0:
            continue
        drop_rate = 1.0 - (current / previous)
        if drop_rate > max_drop:
            max_drop = drop_rate
            bottleneck = FUNNEL_STAGES[idx]
    return bottleneck


def compute_funnel_summary(frame: pd.DataFrame, state: str) -> InvestmentOutcomeSummary:
    """Compute full funnel summary for a single state."""
    stage_counts = compute_stage_counts(frame, state)
    total_cohort = stage_counts.get("youth_population", 0)
    if total_cohort < MIN_COHORT_SIZE:
        logger.warning("State %s cohort size %d below minimum", state, total_cohort)

    subset = frame[frame["state"] == state]
    year = int(subset["year"].max()) if not subset.empty else 0
    conversions = compute_stage_retention(frame, state)
    return InvestmentOutcomeSummary(
        state=state,
        year=year,
        investment_per_youth=conversions["investment_to_youth_population"],
        participation_rate=conversions["youth_population_to_participation"],
        medals_per_participant=conversions["participation_to_competitive_outcome"],
        stage_values={key: float(value) for key, value in stage_counts.items()},
        stage_conversion=conversions,
        bottleneck_stage=min(conversions, key=lambda key: conversions[key]),
        census_year=int(subset["census_year"].iloc[0]) if not subset.empty else 2011,
    )


def compute_all_state_summaries(frame: pd.DataFrame) -> list[InvestmentOutcomeSummary]:
    """Compute funnel summaries for every state in the dataset."""
    states = sorted(frame["state"].unique())
    return [compute_funnel_summary(frame, state) for state in states]


def expected_retention_for_transition(from_stage: str, to_stage: str) -> float:
    """Look up configured baseline retention for a stage transition."""
    key = f"{from_stage}_to_{to_stage}"
    return STAGE_CONVERSION_BASELINES.get(key, 0.0)


def assert_funnel_monotonic(stage_counts: dict[str, int]) -> bool:
    """Return True if cohort counts decrease monotonically through stages."""
    ordered = [stage_counts.get(stage, 0) for stage in FUNNEL_STAGES]
    return all(ordered[i] >= ordered[i + 1] for i in range(len(ordered) - 1))
