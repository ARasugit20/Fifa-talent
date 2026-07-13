"""Unit tests for geospatial helpers."""

from __future__ import annotations

import pandas as pd

from india_football_funnel.analysis.geospatial import (
    aggregate_retention_by_state,
    compute_state_centroid,
    filter_valid_coordinates,
    is_within_india,
)


def test_is_within_india_valid() -> None:
    assert is_within_india(19.0760, 72.8777)


def test_is_within_india_invalid() -> None:
    assert not is_within_india(51.5074, -0.1278)


def test_filter_valid_coordinates() -> None:
    frame = pd.DataFrame(
        [{"state": "Kerala", "retention_rate": 0.1, "latitude": 9.9, "longitude": 76.2}]
    )
    filtered = filter_valid_coordinates(frame)
    assert len(filtered) == len(frame)


def test_aggregate_retention_by_state() -> None:
    frame = pd.DataFrame(
        [
            {"state": "Kerala", "retention_rate": 0.2},
            {"state": "Kerala", "retention_rate": 0.4},
        ]
    )
    grouped = aggregate_retention_by_state(frame)
    assert "state" in grouped.columns
    assert "avg_retention" in grouped.columns
    assert len(grouped) == frame["state"].nunique()


def test_compute_state_centroid() -> None:
    frame = pd.DataFrame(
        [{"state": "Kerala", "retention_rate": 0.1, "latitude": 9.9312, "longitude": 76.2673}]
    )
    lat, lon = compute_state_centroid(frame, "Kerala")
    assert 9.0 < lat < 10.0
    assert 76.0 < lon < 77.0
