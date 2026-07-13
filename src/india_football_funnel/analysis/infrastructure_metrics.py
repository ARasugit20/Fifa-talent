"""Descriptive metrics for state/UT public sports infrastructure records."""

from __future__ import annotations

import pandas as pd

from india_football_funnel.models import InfrastructureSummary


def compute_infrastructure_summaries(frame: pd.DataFrame) -> list[InfrastructureSummary]:
    """Compute descriptive per-state infrastructure metrics."""
    summaries: list[InfrastructureSummary] = []
    for _, row in frame.iterrows():
        denominator = int(row["denominator_value"])
        released = float(row["amount_released_inr"])
        assistance = float(row["financial_assistance_inr"])
        completed = int(row["projects_completed"])
        total = int(row["projects_total"])
        summaries.append(
            InfrastructureSummary(
                canonical_state_ut=str(row["canonical_state_ut"]),
                reporting_period=str(row["reporting_period"]),
                projects_total=total,
                completion_rate=0.0 if total == 0 else completed / total,
                amount_released_per_capita=0.0 if denominator == 0 else released / denominator,
                financial_assistance_per_capita=0.0
                if denominator == 0
                else assistance / denominator,
                denominator_definition=str(row["denominator_definition"]),
                denominator_year=int(row["denominator_year"]),
                denominator_is_stale=bool(row["denominator_is_stale"]),
            )
        )
    return summaries
