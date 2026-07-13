"""Geospatial validation and aggregation helpers."""

from __future__ import annotations

import logging

import pandas as pd

from india_football_funnel.config import (
    INDIA_LAT_MAX,
    INDIA_LAT_MIN,
    INDIA_LON_MAX,
    INDIA_LON_MIN,
)

logger = logging.getLogger(__name__)


def is_within_india(latitude: float, longitude: float) -> bool:
    """Check whether coordinates fall within India's bounding box."""
    return (
        INDIA_LAT_MIN <= latitude <= INDIA_LAT_MAX and INDIA_LON_MIN <= longitude <= INDIA_LON_MAX
    )


def filter_valid_coordinates(frame: pd.DataFrame) -> pd.DataFrame:
    """Remove rows with coordinates outside India."""
    mask = frame.apply(
        lambda row: is_within_india(float(row["latitude"]), float(row["longitude"])),
        axis=1,
    )
    invalid_count = int((~mask).sum())
    if invalid_count > 0:
        logger.warning("Filtered %d rows with invalid coordinates", invalid_count)
    return frame.loc[mask].copy()


def aggregate_retention_by_state(frame: pd.DataFrame) -> pd.DataFrame:
    """Compute average retention rate grouped by state."""
    grouped = frame.groupby("state", as_index=False).agg(
        avg_retention=("retention_rate", "mean"),
    )
    return grouped.sort_values("avg_retention", ascending=False)


def compute_state_centroid(frame: pd.DataFrame, state: str) -> tuple[float, float]:
    """Compute mean lat/lon centroid for a state's observations."""
    subset = frame[frame["state"] == state]
    if subset.empty:
        msg = f"No observations for state: {state}"
        raise ValueError(msg)
    lat = float(subset["latitude"].mean())
    lon = float(subset["longitude"].mean())
    return lat, lon
