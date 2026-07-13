"""Data validation schemas."""

from __future__ import annotations

import pandera as pa
from pandera.typing import Series

from india_football_funnel.config import CENSUS_YEAR


class RawInvestmentOutcomeSchema(pa.DataFrameModel):
    """Schema for raw public investment/outcome records."""

    state: Series[str] = pa.Field(nullable=False)
    district: Series[str] = pa.Field(nullable=True)
    year: Series[int] = pa.Field(ge=CENSUS_YEAR)
    census_year: Series[int] = pa.Field(eq=CENSUS_YEAR)
    youth_population_10_17: Series[int] = pa.Field(ge=0)
    budget_allocation_inr: Series[float] = pa.Field(ge=0.0)
    khelo_india_centres: Series[float] = pa.Field(nullable=True, ge=0.0)
    participation_count: Series[int] = pa.Field(ge=0)
    medals: Series[int] = pa.Field(ge=0)
    tournament_results_score: Series[float] = pa.Field(nullable=True, ge=0.0)
    facility_data_status: Series[str] = pa.Field(
        isin=("available", "not_currently_available"),
    )

    class Config:
        coerce = True
        strict = False


class ProcessedInvestmentOutcomeSchema(pa.DataFrameModel):
    """Schema for processed public investment/outcome parquet output."""

    state: Series[str] = pa.Field(nullable=False)
    district: Series[str] = pa.Field(nullable=True)
    year: Series[int] = pa.Field(ge=CENSUS_YEAR)
    census_year: Series[int] = pa.Field(eq=CENSUS_YEAR)
    youth_population_10_17: Series[int] = pa.Field(ge=0)
    budget_allocation_inr: Series[float] = pa.Field(ge=0.0)
    budget_per_capita: Series[float] = pa.Field(ge=0.0)
    khelo_india_centres: Series[float] = pa.Field(nullable=True, ge=0.0)
    facility_density: Series[float] = pa.Field(nullable=True, ge=0.0)
    participation_count: Series[int] = pa.Field(ge=0)
    participation_rate: Series[float] = pa.Field(ge=0.0)
    medals: Series[int] = pa.Field(ge=0)
    medals_per_participant: Series[float] = pa.Field(ge=0.0)
    tournament_results_score: Series[float] = pa.Field(nullable=True, ge=0.0)
    facility_data_status: Series[str] = pa.Field(
        isin=("available", "not_currently_available"),
    )
    source_file: Series[str] = pa.Field(nullable=False)

    class Config:
        coerce = True
        strict = False


class PublicSportsInfrastructureSchema(pa.DataFrameModel):
    """Schema for joined state/UT public sports infrastructure records."""

    canonical_state_ut: Series[str] = pa.Field(nullable=False)
    reporting_period: Series[str] = pa.Field(nullable=False)
    projects_to_be_started: Series[int] = pa.Field(ge=0)
    projects_under_progress: Series[int] = pa.Field(ge=0)
    projects_completed: Series[int] = pa.Field(ge=0)
    projects_total: Series[int] = pa.Field(ge=0)
    amount_sanctioned_inr: Series[float] = pa.Field(ge=0.0)
    amount_released_inr: Series[float] = pa.Field(ge=0.0)
    financial_assistance_inr: Series[float] = pa.Field(ge=0.0)
    denominator_value: Series[int] = pa.Field(ge=0)
    denominator_definition: Series[str] = pa.Field(nullable=False)
    denominator_year: Series[int] = pa.Field(eq=CENSUS_YEAR)
    denominator_is_stale: Series[bool] = pa.Field(nullable=False)
    source_file: Series[str] = pa.Field(nullable=False)
    source_url: Series[str] = pa.Field(nullable=False)
    retrieved_at_utc: Series[str] = pa.Field(nullable=False)
    provenance_sha256: Series[str] = pa.Field(nullable=False)

    class Config:
        coerce = True
        strict = False


# Backwards-compatible aliases for older ETL handler imports; the primary schema
# is investment_outcome_observation.
RawFunnelSchema = RawInvestmentOutcomeSchema
ProcessedFunnelSchema = ProcessedInvestmentOutcomeSchema
