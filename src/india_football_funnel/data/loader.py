"""Data loading and ETL processing."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal, cast

import pandas as pd

from india_football_funnel.config import (
    MAX_MISSING_RATE,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    RESULTS_DATA_DIR,
)
from india_football_funnel.data.schema import (
    ProcessedInvestmentOutcomeSchema,
    RawInvestmentOutcomeSchema,
)
from india_football_funnel.models import InvestmentOutcomeObservation, ProcessedRecord

logger = logging.getLogger(__name__)


def load_raw_csv(path: Path) -> pd.DataFrame:
    """Load raw CSV and validate against schema."""
    logger.info("Loading raw data from %s", path)
    frame = pd.read_csv(path)
    validated = RawInvestmentOutcomeSchema.validate(frame, lazy=True)
    return cast(pd.DataFrame, validated)


def assess_data_quality(frame: pd.DataFrame) -> dict[str, float]:
    """Compute missing-rate per column and flag quality issues."""
    missing_rates = {column: float(frame[column].isna().mean()) for column in frame.columns}
    for column, rate in missing_rates.items():
        if rate > MAX_MISSING_RATE:
            logger.warning("Column %s missing rate %.2f exceeds threshold", column, rate)
    return missing_rates


def raw_frame_to_observations(frame: pd.DataFrame) -> list[InvestmentOutcomeObservation]:
    """Convert validated dataframe to typed observations."""
    observations: list[InvestmentOutcomeObservation] = []
    for row in frame.to_dict(orient="records"):
        observations.append(
            InvestmentOutcomeObservation(
                state=str(row["state"]),
                district=None if pd.isna(row.get("district")) else str(row["district"]),
                year=int(row["year"]),
                census_year=int(row["census_year"]),
                youth_population_10_17=int(row["youth_population_10_17"]),
                budget_allocation_inr=float(row["budget_allocation_inr"]),
                khelo_india_centres=None
                if pd.isna(row.get("khelo_india_centres"))
                else int(row["khelo_india_centres"]),
                participation_count=int(row["participation_count"]),
                medals=int(row["medals"]),
                tournament_results_score=None
                if pd.isna(row.get("tournament_results_score"))
                else float(row["tournament_results_score"]),
                facility_data_status=cast(
                    Literal["available", "not_currently_available"],
                    str(row["facility_data_status"]),
                ),
                source=str(row.get("source", "local_fixture")),
            )
        )
    return observations


def observations_to_processed_records(
    observations: list[InvestmentOutcomeObservation],
    source_file: str,
) -> list[ProcessedRecord]:
    """Map observations to processed storage records."""
    return [
        ProcessedRecord(
            state=obs.state,
            district=obs.district,
            year=obs.year,
            census_year=obs.census_year,
            youth_population_10_17=obs.youth_population_10_17,
            budget_allocation_inr=obs.budget_allocation_inr,
            khelo_india_centres=obs.khelo_india_centres,
            participation_count=obs.participation_count,
            medals=obs.medals,
            tournament_results_score=obs.tournament_results_score,
            facility_data_status=obs.facility_data_status,
            source_file=source_file,
        )
        for obs in observations
    ]


def processed_records_to_frame(records: list[ProcessedRecord]) -> pd.DataFrame:
    """Convert processed records to a validated dataframe."""
    frame = pd.DataFrame([record.model_dump() for record in records])
    frame["budget_per_capita"] = frame["budget_allocation_inr"] / frame[
        "youth_population_10_17"
    ].replace(0, pd.NA)
    frame["facility_density"] = frame["khelo_india_centres"] / frame[
        "youth_population_10_17"
    ].replace(0, pd.NA)
    frame["participation_rate"] = frame["participation_count"] / frame[
        "youth_population_10_17"
    ].replace(0, pd.NA)
    frame["medals_per_participant"] = frame["medals"] / frame["participation_count"].replace(
        0, pd.NA
    )
    frame = frame.fillna(
        {
            "budget_per_capita": 0.0,
            "participation_rate": 0.0,
            "medals_per_participant": 0.0,
        }
    )
    return cast(pd.DataFrame, ProcessedInvestmentOutcomeSchema.validate(frame))


def write_processed_parquet(frame: pd.DataFrame, output_path: Path) -> Path:
    """Write validated processed data to parquet."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output_path, index=False)
    logger.info("Wrote processed parquet to %s", output_path)
    return output_path


def process_raw_file(raw_path: Path, processed_path: Path | None = None) -> Path:
    """Full ETL: load, validate, transform, and write processed parquet."""
    if processed_path is None:
        processed_path = PROCESSED_DATA_DIR / f"{raw_path.stem}.parquet"

    frame = load_raw_csv(raw_path)
    assess_data_quality(frame)
    observations = raw_frame_to_observations(frame)
    records = observations_to_processed_records(observations, source_file=raw_path.name)
    processed_frame = processed_records_to_frame(records)
    return write_processed_parquet(processed_frame, processed_path)


def load_processed_parquet(path: Path) -> pd.DataFrame:
    """Load processed parquet with schema validation."""
    logger.info("Loading processed data from %s", path)
    frame = pd.read_parquet(path)
    return cast(pd.DataFrame, ProcessedInvestmentOutcomeSchema.validate(frame))


def ensure_local_data_dirs() -> None:
    """Create local data directories for reproducibility workflow."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_raw_json(path: Path) -> pd.DataFrame:
    """Load raw JSON records (S3 event payloads / API dumps)."""
    logger.info("Loading raw JSON from %s", path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "records" in payload:
        frame = pd.DataFrame(payload["records"])
    elif isinstance(payload, list):
        frame = pd.DataFrame(payload)
    else:
        msg = f"Unsupported JSON structure in {path}"
        raise ValueError(msg)
    return cast(pd.DataFrame, RawInvestmentOutcomeSchema.validate(frame))
