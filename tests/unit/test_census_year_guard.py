"""Tests enforcing Census 2011 tagging across the pipeline."""

from __future__ import annotations

import pandas as pd
import pytest
from tests.conftest import fixture_path, load_fixture_csv

from india_football_funnel.config import CENSUS_YEAR
from india_football_funnel.data.loader import load_processed_parquet, process_raw_file
from india_football_funnel.data.pipeline import build_processed_investment_frame
from india_football_funnel.models import InvestmentOutcomeObservation


def test_fixture_csv_tags_census_year() -> None:
    frame = load_fixture_csv()
    assert (frame["census_year"] == CENSUS_YEAR).all()


def test_processed_parquet_tags_census_year(tmp_path) -> None:  # type: ignore[no-untyped-def]
    processed = tmp_path / "processed.parquet"
    process_raw_file(fixture_path("sample_investment_outcomes.csv"), processed)
    frame = load_processed_parquet(processed)
    assert (frame["census_year"] == CENSUS_YEAR).all()


def test_investment_observation_rejects_wrong_census_year() -> None:
    with pytest.raises(ValueError, match="2011"):
        InvestmentOutcomeObservation(
            state="Kerala",
            year=2023,
            census_year=2021,
            youth_population_10_17=1000,
            budget_allocation_inr=1000.0,
            participation_count=10,
            medals=1,
            source="test",
        )


def test_pipeline_builder_preserves_census_year(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    for target in (
        "india_football_funnel.config",
        "india_football_funnel.data.pipeline",
        "india_football_funnel.data.loader",
    ):
        monkeypatch.setattr(f"{target}.RAW_DATA_DIR", raw_dir)
    for target in (
        "india_football_funnel.config",
        "india_football_funnel.data.loader",
    ):
        monkeypatch.setattr(f"{target}.PROCESSED_DATA_DIR", processed_dir)

    frame = build_processed_investment_frame()
    assert isinstance(frame, pd.DataFrame)
    assert (frame["census_year"] == CENSUS_YEAR).all()
