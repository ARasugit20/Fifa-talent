"""Structured domain models crossing module boundaries."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from india_football_funnel.config import CENSUS_YEAR


class InvestmentOutcomeObservation(BaseModel):
    """District/state public-data observation for the new analysis grain."""

    state: str
    district: str | None = None
    year: int = Field(ge=CENSUS_YEAR)
    census_year: int = Field(default=CENSUS_YEAR)
    youth_population_10_17: int = Field(ge=0)
    budget_allocation_inr: float = Field(ge=0.0)
    khelo_india_centres: int | None = Field(default=None, ge=0)
    participation_count: int = Field(ge=0)
    medals: int = Field(ge=0)
    tournament_results_score: float | None = Field(default=None, ge=0.0)
    source: str
    facility_data_status: Literal["available", "not_currently_available"] = (
        "not_currently_available"
    )

    @field_validator("census_year")
    @classmethod
    def validate_census_year(cls, value: int) -> int:
        if value != CENSUS_YEAR:
            msg = f"Census records must be explicitly tagged as {CENSUS_YEAR}"
            raise ValueError(msg)
        return value

    @property
    def budget_per_capita(self) -> float:
        if self.youth_population_10_17 == 0:
            return 0.0
        return self.budget_allocation_inr / self.youth_population_10_17

    @property
    def facility_density(self) -> float | None:
        if self.khelo_india_centres is None or self.youth_population_10_17 == 0:
            return None
        return self.khelo_india_centres / self.youth_population_10_17

    @property
    def participation_rate(self) -> float:
        if self.youth_population_10_17 == 0:
            return 0.0
        return self.participation_count / self.youth_population_10_17


class RegressionResult(BaseModel):
    """Output from exploratory associative regression analysis."""

    predictor: str
    coefficient: float
    std_error: float
    p_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    n_observations: int
    r_squared: float
    covariates_used: list[str] = Field(default_factory=list)
    covariates_dropped: list[str] = Field(default_factory=list)


class ScenarioParams(BaseModel):
    """Parameters for a Monte Carlo simulation scenario."""

    name: str
    years: int = Field(ge=1, le=50)
    n_runs: int = Field(ge=1, le=100_000)
    rng_seed: int
    base_youth_population: int = Field(ge=1)
    baseline_participation_rate: float = Field(ge=0.0, le=1.0)
    baseline_medals_per_participant: float = Field(ge=0.0)
    budget_per_capita: float = Field(ge=0.0)
    target_budget_per_capita: float | None = Field(default=None, ge=0.0)
    intervention_enabled: bool = False
    growth_rate_override: float | None = None


class SimulationYearResult(BaseModel):
    """Aggregated simulation metrics for a single scenario year."""

    year: int
    mean_medals: float
    p10_medals: float
    p90_medals: float
    mean_participation_rate: float


class SimulationResult(BaseModel):
    """Full Monte Carlo simulation output.

    Growth, budget-effect, and uncertainty parameters are manual assumptions,
    not estimated from data. Outputs are illustrative scenarios, not forecasts.
    """

    scenario_name: str
    n_runs: int
    years: int
    annual_results: list[SimulationYearResult]
    final_medals_mean: float
    final_medals_std: float
    assumption_based: bool = True
    uncalibrated: bool = True


class FunnelMetricsSummary(BaseModel):
    """Aggregated funnel metrics for a geography."""

    state: str
    stage_counts: dict[str, int]
    stage_retention: dict[str, float]
    total_cohort: int
    bottleneck_stage: str


class InvestmentOutcomeSummary(BaseModel):
    """Aggregated conversion metrics for the public-data funnel."""

    state: str
    year: int
    investment_per_youth: float
    participation_rate: float
    medals_per_participant: float
    stage_values: dict[str, float]
    stage_conversion: dict[str, float]
    bottleneck_stage: str
    census_year: int = CENSUS_YEAR


class ProcessedRecord(BaseModel):
    """Validated investment-outcome record written to processed storage."""

    state: str
    district: str | None
    year: int
    census_year: int
    youth_population_10_17: int
    budget_allocation_inr: float
    khelo_india_centres: int | None
    participation_count: int
    medals: int
    tournament_results_score: float | None
    facility_data_status: str
    source_file: str


class PdfExtractedMetric(BaseModel):
    """Traceable metric extracted from a FIFA/AFC PDF report."""

    metric_name: str
    metric_value: float | str
    source_pdf: str
    source_page: int = Field(ge=1)
    extraction_note: str
