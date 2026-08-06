"""Runtime data-quality checks for public sports infrastructure outputs."""

from __future__ import annotations

from datetime import date

import pandas as pd

from india_football_funnel.config import CENSUS_YEAR
from india_football_funnel.data.state_names import (
    CANONICAL_STATES_UTS,
    EXCLUDED_FROM_CENSUS_2011_DENOMINATOR,
    StateReconciliationReport,
)
from india_football_funnel.models import DataQualityReport


def build_data_quality_report(
    frame: pd.DataFrame,
    report: StateReconciliationReport,
    reference_year: int | None = None,
) -> DataQualityReport:
    """Summarize non-blocking completeness, grain, and Census-vintage signals."""
    evaluation_year = reference_year or date.today().year
    denominator_year = int(frame["denominator_year"].iloc[0]) if not frame.empty else CENSUS_YEAR
    census_staleness_years = max(evaluation_year - denominator_year, 0)
    joined_states = set(frame["canonical_state_ut"]) if not frame.empty else set()
    expected_states = set(CANONICAL_STATES_UTS) - EXCLUDED_FROM_CENSUS_2011_DENOMINATOR
    missing_canonical_states = sorted(expected_states - joined_states)
    states_dropped_from_join = sorted(set(report.matched) - joined_states)
    row_counts = (
        frame["canonical_state_ut"].value_counts() if not frame.empty else pd.Series(dtype=int)
    )
    rows_per_state_min = int(row_counts.min()) if not row_counts.empty else 0
    rows_per_state_max = int(row_counts.max()) if not row_counts.empty else 0
    stale_denominator_count = int(frame["denominator_is_stale"].sum()) if not frame.empty else 0

    warnings: list[str] = []
    if stale_denominator_count:
        warnings.append(
            f"{stale_denominator_count} row(s) use a Census {denominator_year} denominator."
        )
    if census_staleness_years >= 10:
        warnings.append(
            f"Census denominator is {census_staleness_years} years older than the reference year."
        )
    if missing_canonical_states:
        warnings.append(
            f"{len(missing_canonical_states)} canonical state/UT unit(s) are absent "
            "from the joined frame."
        )
    if states_dropped_from_join:
        warnings.append(
            f"{len(states_dropped_from_join)} reconciled state/UT unit(s) were dropped "
            "from the source join."
        )
    if rows_per_state_max > 1:
        warnings.append("Duplicate state/UT rows detected; expected one joined row per state/UT.")

    return DataQualityReport(
        census_staleness_years=census_staleness_years,
        denominator_year=denominator_year,
        row_count=len(frame),
        rows_per_state_min=rows_per_state_min,
        rows_per_state_max=rows_per_state_max,
        missing_canonical_states=missing_canonical_states,
        states_dropped_from_join=states_dropped_from_join,
        stale_denominator_count=stale_denominator_count,
        warnings=warnings,
        blocking=False,
    )
