"""Unit tests for data loader."""

from __future__ import annotations

from pathlib import Path

import pandera.errors
import pytest
from tests.conftest import fixture_path

from india_football_funnel.data.loader import (
    load_raw_csv,
    process_raw_file,
    raw_frame_to_observations,
)


def test_load_raw_csv(tmp_path: Path) -> None:
    source = fixture_path("sample_funnel.csv")
    frame = load_raw_csv(source)
    assert len(frame) == 10
    assert "state" in frame.columns
    assert (frame["census_year"] == 2011).all()


def test_raw_frame_to_observations() -> None:
    frame = load_raw_csv(fixture_path("sample_funnel.csv"))
    observations = raw_frame_to_observations(frame)
    assert len(observations) == 10
    assert observations[0].state == "Maharashtra"
    assert observations[0].census_year == 2011


def test_process_raw_file(tmp_path: Path) -> None:
    source = fixture_path("sample_funnel.csv")
    output = tmp_path / "processed.parquet"
    result_path = process_raw_file(source, output)
    assert result_path.exists()


def test_invalid_csv_raises(tmp_path: Path) -> None:
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("state,district\nonly,headers\n", encoding="utf-8")
    with pytest.raises(pandera.errors.SchemaErrors):
        load_raw_csv(bad_csv)
