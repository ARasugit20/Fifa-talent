"""Central configuration: constants, thresholds, and AWS resource names."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Verified public-data funnel stages
# ---------------------------------------------------------------------------
FUNNEL_STAGES: tuple[str, ...] = (
    "investment",
    "youth_population",
    "participation",
    "competitive_outcome",
)

# Stage conversion defaults (data-derived once real public datasets are pulled;
# these are only used for deterministic local fixtures and simulation baselines).
STAGE_CONVERSION_BASELINES: dict[str, float] = {
    "investment_to_youth_population": 0.0,  # not a literal conversion; exposure ratio
    "youth_population_to_participation": 0.012,  # fixture-derived participation share
    "participation_to_competitive_outcome": 0.08,  # fixture-derived medals/participants
}

# Data quality thresholds (assumption: portfolio-scale minimum viable records)
MIN_COHORT_SIZE: int = 5  # assumption: suppress noisy small-N cells
MAX_MISSING_RATE: float = 0.15  # assumption: flag columns above 15% missing
RETENTION_MIN: float = 0.0
RETENTION_MAX: float = 1.0

# Geospatial (assumption: India bounding box for coordinate validation)
INDIA_LAT_MIN: float = 6.0
INDIA_LAT_MAX: float = 37.0
INDIA_LON_MIN: float = 68.0
INDIA_LON_MAX: float = 97.0

# Census source metadata (verified limitation: 2011 is latest complete Census)
CENSUS_YEAR: int = 2011
CENSUS_API_BASE_URL: str = "http://digital-library.census.ihsn.org/index.php/api/tables/data"
CENSUS_TABLES_URL: str = "https://censusindia.gov.in/census.website/data/census-tables"

# Legacy optional data.gov.in client constants (not used by the manual raw pipeline)
KHELO_INDIA_MEDAL_TALLY_RESOURCE: str = "khelo-india-medal-tally"
KHELO_INDIA_BUDGET_RESOURCE: str = "khelo-india-budget-allocation"
KHELO_INDIA_RAW_PREFIX: str = "raw/khelo_india"
FIFA_AFC_RAW_PREFIX: str = "raw/fifa_afc_reports"

# Public data source references (official pages; not fabricated API resource IDs)
MDSD_SOURCE_PAGE_URL = "https://mdsd.kheloindia.gov.in/"
KHELO_INDIA_FINANCIAL_ASSISTANCE_SOURCE_URL = (
    "https://www.data.gov.in/resource/"
    "stateuts-wise-details-financial-assistance-provided-under-khelo-india-scheme-and-national"
)
CENSUS_PCA_SOURCE_URL = (
    "https://www.data.gov.in/catalog/primary-census-abstract-2011-india-and-states-0"
)

# Local paths for reproducibility (no AWS required)
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
RESULTS_DATA_DIR: Path = DATA_DIR / "results"
FIXTURES_DIR: Path = PROJECT_ROOT / "tests" / "fixtures"

# Required manually downloaded raw inputs for local reproduction
RAW_MSDS_DIR = RAW_DATA_DIR / "mdsd"
RAW_KHELO_INDIA_DIR = RAW_DATA_DIR / "khelo_india"
RAW_CENSUS_DIR = RAW_DATA_DIR / "census"
RAW_MINISTRY_REPORTS_DIR = RAW_DATA_DIR / "ministry_reports"

REQUIRED_RAW_FILES: dict[str, dict[str, str]] = {
    "mdsd/state_wise_progress.csv": {
        "role": "MD-SD state/UT project progress counts",
        "source_page_url": f"{MDSD_SOURCE_PAGE_URL}state-wise-progress",
    },
    "mdsd/grantee_amounts.csv": {
        "role": "MD-SD amount sanctioned and released by state/UT",
        "source_page_url": f"{MDSD_SOURCE_PAGE_URL}gratee-type-wise-progress",
    },
    "khelo_india/financial_assistance.csv": {
        "role": "State/UT financial assistance under Khelo India",
        "source_page_url": KHELO_INDIA_FINANCIAL_ASSISTANCE_SOURCE_URL,
    },
    "census/state_population_2011.csv": {
        "role": "Census 2011 state/UT denominator with explicit definition",
        "source_page_url": CENSUS_PCA_SOURCE_URL,
    },
}

INFRASTRUCTURE_CAUTION = (
    "State/UT public sports infrastructure and investment descriptive analytics; "
    "not football-specific; Census 2011 denominators are stale where paired with later years."
)

DATASET_READY_VERSION: str = "v1"
DATASET_READY_MANIFEST_KEY: str = "raw/dataset-ready.json"

# Causal regression defaults (literature baseline: OLS with fixed effects for public panel data)
REGRESSION_MIN_OBSERVATIONS: int = 10  # assumption: minimum rows for stable fit
REGRESSION_CONFIDENCE_LEVEL: float = 0.95  # literature baseline: 95% CI

# Simulation defaults (assumption: 10-year horizon, 1000 Monte Carlo draws)
DEFAULT_SIMULATION_YEARS: int = 10
DEFAULT_MONTE_CARLO_RUNS: int = 1000
DEFAULT_RNG_SEED: int = 42
PARTICIPATION_GROWTH_RATE_MEAN: float = 0.03  # assumption: annual youth participation growth
PARTICIPATION_GROWTH_RATE_STD: float = 0.01  # assumption: growth uncertainty
BUDGET_EFFECT_MEAN: float = 0.06  # assumption: top-quartile budget-per-capita uplift
BUDGET_EFFECT_STD: float = 0.02  # assumption: intervention variance
ASSUMPTION_REGISTRY_VERSION: str = "v1"
STATE_MAPPING_VERSION: str = "v1"

# S3 layout (env-driven resource names)
RAW_PREFIX: str = "raw"
PROCESSED_PREFIX: str = "processed"
RESULTS_PREFIX: str = "results"
RAW_SOURCE_NAME: str = "investment_outcomes"


class Settings(BaseModel):
    """Environment-driven runtime settings."""

    aws_region: str = Field(default="ap-south-1")
    aws_account_id: str = Field(default="")
    project_name: str = Field(default="india-football-funnel")
    s3_bucket_name: str = Field(default="")
    ecr_repository_name: str = Field(default="india-football-funnel")
    etl_lambda_name: str = Field(default="iff-etl-processor")
    simulation_lambda_name: str = Field(default="iff-simulation-runner")
    glue_database_name: str = Field(default="iff_data_catalog")
    athena_workgroup_name: str = Field(default="iff-analytics")
    raw_lifecycle_glacier_days: int = Field(default=90)
    local_mode: bool = Field(default=True)

    @property
    def resolved_bucket_name(self) -> str:
        if self.s3_bucket_name:
            return self.s3_bucket_name
        return f"{self.project_name}-data-{self.aws_account_id or 'local'}"

    @property
    def raw_s3_prefix(self) -> str:
        return f"s3://{self.resolved_bucket_name}/{RAW_PREFIX}"

    @property
    def processed_s3_prefix(self) -> str:
        return f"s3://{self.resolved_bucket_name}/{PROCESSED_PREFIX}"

    @property
    def results_s3_prefix(self) -> str:
        return f"s3://{self.resolved_bucket_name}/{RESULTS_PREFIX}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings from environment variables (cached)."""
    return Settings(
        aws_region=os.getenv("AWS_REGION", "ap-south-1"),
        aws_account_id=os.getenv("AWS_ACCOUNT_ID", ""),
        project_name=os.getenv("IFF_PROJECT_NAME", "india-football-funnel"),
        s3_bucket_name=os.getenv("IFF_S3_BUCKET", ""),
        ecr_repository_name=os.getenv("IFF_ECR_REPO", "india-football-funnel"),
        etl_lambda_name=os.getenv("IFF_ETL_LAMBDA", "iff-etl-processor"),
        simulation_lambda_name=os.getenv("IFF_SIM_LAMBDA", "iff-simulation-runner"),
        glue_database_name=os.getenv("IFF_GLUE_DATABASE", "iff_data_catalog"),
        athena_workgroup_name=os.getenv("IFF_ATHENA_WORKGROUP", "iff-analytics"),
        raw_lifecycle_glacier_days=int(os.getenv("IFF_GLACIER_DAYS", "90")),
        local_mode=os.getenv("IFF_LOCAL_MODE", "true").lower() == "true",
    )
