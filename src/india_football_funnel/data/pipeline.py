"""Public-data pipeline orchestration helpers."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from india_football_funnel.config import CENSUS_YEAR, RAW_DATA_DIR
from india_football_funnel.data.loader import load_processed_parquet, process_raw_file
from india_football_funnel.data.scrapers.state_registry import scrape_state_registry_stub

logger = logging.getLogger(__name__)


def ensure_raw_investment_outcomes(raw_path: Path | None = None) -> Path:
    """Ensure a raw public-data shaped CSV exists for local reproduction."""
    if raw_path is None:
        raw_path = RAW_DATA_DIR / "investment_outcomes.csv"
    if not raw_path.exists():
        scrape_state_registry_stub(raw_path)
    return raw_path


def build_processed_investment_frame(raw_path: Path | None = None) -> pd.DataFrame:
    """Run ETL on the public investment/outcome raw file."""
    source = ensure_raw_investment_outcomes(raw_path)
    processed_path = process_raw_file(source)
    frame = load_processed_parquet(processed_path)
    if not (frame["census_year"] == CENSUS_YEAR).all():
        msg = f"Processed data must be tagged with census_year={CENSUS_YEAR}"
        raise ValueError(msg)
    logger.info("Built processed investment frame with %d rows", len(frame))
    return frame
