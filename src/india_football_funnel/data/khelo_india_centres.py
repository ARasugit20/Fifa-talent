"""Khelo India facility-location availability checks."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

OFFICIAL_SOURCE_URLS: tuple[str, ...] = (
    "https://kheloindia.gov.in/",
    "https://yas.gov.in/",
)


def load_structured_centres(path: Path) -> pd.DataFrame:
    """Load an official structured centres list if one has been manually verified."""
    logger.info("Loading official Khelo India centres list from %s", path)
    frame = pd.read_csv(path)
    required = {"state", "district", "centre_name", "source_document"}
    missing = required.difference(frame.columns)
    if missing:
        msg = f"Khelo India centres file missing columns: {sorted(missing)}"
        raise ValueError(msg)
    frame["facility_data_status"] = "available"
    return frame


def unavailable_facility_frame(states: list[str], year: int) -> pd.DataFrame:
    """Represent unavailable facility-location data without substituting secondary sources."""
    logger.warning(
        "No verified structured Khelo India centres list found on official sources: %s",
        ", ".join(OFFICIAL_SOURCE_URLS),
    )
    return pd.DataFrame(
        [
            {
                "state": state,
                "year": year,
                "khelo_india_centres": None,
                "facility_data_status": "not_currently_available",
                "source_document": "official structured list not found",
            }
            for state in states
        ]
    )


def centres_by_state(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate verified centre counts by state/year."""
    if frame.empty or "centre_name" not in frame.columns:
        return frame
    grouped = (
        frame.groupby(["state"], as_index=False)
        .agg(khelo_india_centres=("centre_name", "count"))
        .assign(facility_data_status="available")
    )
    return grouped
