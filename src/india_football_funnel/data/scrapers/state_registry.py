"""Local fixture generator for verified public-data ingestion (no network in tests)."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def scrape_state_registry_stub(output_path: Path) -> Path:
    """Write a deterministic public-data shaped sample for local development.

    This is not AIFF CRS/CMS data. It mirrors the final public-source grain:
    Census youth population + Khelo India budget/participation/outcome.
    """
    logger.info("Generating public-data sample at %s", output_path)
    rows = [
        {
            "state": "Maharashtra",
            "district": "Mumbai",
            "year": 2023,
            "census_year": 2011,
            "youth_population_10_17": 1_100_000,
            "budget_allocation_inr": 180_000_000.0,
            "khelo_india_centres": None,
            "participation_count": 14_000,
            "medals": 55,
            "tournament_results_score": 55.0,
            "facility_data_status": "not_currently_available",
            "source": "local public-data fixture",
        },
        {
            "state": "Kerala",
            "district": "Kochi",
            "year": 2023,
            "census_year": 2011,
            "youth_population_10_17": 430_000,
            "budget_allocation_inr": 84_000_000.0,
            "khelo_india_centres": None,
            "participation_count": 6_800,
            "medals": 31,
            "tournament_results_score": 31.0,
            "facility_data_status": "not_currently_available",
            "source": "local public-data fixture",
        },
        {
            "state": "West Bengal",
            "district": "Kolkata",
            "year": 2023,
            "census_year": 2011,
            "youth_population_10_17": 720_000,
            "budget_allocation_inr": 96_000_000.0,
            "khelo_india_centres": None,
            "participation_count": 8_200,
            "medals": 29,
            "tournament_results_score": 29.0,
            "facility_data_status": "not_currently_available",
            "source": "local public-data fixture",
        },
        {
            "state": "Karnataka",
            "district": "Bengaluru",
            "year": 2023,
            "census_year": 2011,
            "youth_population_10_17": 860_000,
            "budget_allocation_inr": 130_000_000.0,
            "khelo_india_centres": None,
            "participation_count": 10_500,
            "medals": 41,
            "tournament_results_score": 41.0,
            "facility_data_status": "not_currently_available",
            "source": "local public-data fixture",
        },
        {
            "state": "Punjab",
            "district": "Ludhiana",
            "year": 2023,
            "census_year": 2011,
            "youth_population_10_17": 390_000,
            "budget_allocation_inr": 74_000_000.0,
            "khelo_india_centres": None,
            "participation_count": 5_600,
            "medals": 24,
            "tournament_results_score": 24.0,
            "facility_data_status": "not_currently_available",
            "source": "local public-data fixture",
        },
        {
            "state": "Tamil Nadu",
            "district": "Chennai",
            "year": 2023,
            "census_year": 2011,
            "youth_population_10_17": 760_000,
            "budget_allocation_inr": 115_000_000.0,
            "khelo_india_centres": None,
            "participation_count": 9_300,
            "medals": 37,
            "tournament_results_score": 37.0,
            "facility_data_status": "not_currently_available",
            "source": "local public-data fixture",
        },
        {
            "state": "Goa",
            "district": "North Goa",
            "year": 2023,
            "census_year": 2011,
            "youth_population_10_17": 85_000,
            "budget_allocation_inr": 26_000_000.0,
            "khelo_india_centres": None,
            "participation_count": 2_100,
            "medals": 12,
            "tournament_results_score": 12.0,
            "facility_data_status": "not_currently_available",
            "source": "local public-data fixture",
        },
        {
            "state": "Odisha",
            "district": "Bhubaneswar",
            "year": 2023,
            "census_year": 2011,
            "youth_population_10_17": 310_000,
            "budget_allocation_inr": 88_000_000.0,
            "khelo_india_centres": None,
            "participation_count": 4_900,
            "medals": 28,
            "tournament_results_score": 28.0,
            "facility_data_status": "not_currently_available",
            "source": "local public-data fixture",
        },
        {
            "state": "Manipur",
            "district": "Imphal West",
            "year": 2023,
            "census_year": 2011,
            "youth_population_10_17": 120_000,
            "budget_allocation_inr": 42_000_000.0,
            "khelo_india_centres": None,
            "participation_count": 3_200,
            "medals": 22,
            "tournament_results_score": 22.0,
            "facility_data_status": "not_currently_available",
            "source": "local public-data fixture",
        },
        {
            "state": "Assam",
            "district": "Kamrup Metropolitan",
            "year": 2023,
            "census_year": 2011,
            "youth_population_10_17": 250_000,
            "budget_allocation_inr": 53_000_000.0,
            "khelo_india_centres": None,
            "participation_count": 3_800,
            "medals": 17,
            "tournament_results_score": 17.0,
            "facility_data_status": "not_currently_available",
            "source": "local public-data fixture",
        },
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_path, index=False)
    return output_path
