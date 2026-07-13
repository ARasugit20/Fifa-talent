"""Public-data pipeline orchestration helpers."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from india_football_funnel.config import CENSUS_YEAR, RAW_DATA_DIR
from india_football_funnel.data.infrastructure_pipeline import (
    build_public_sports_infrastructure_frame,
    write_processed_infrastructure_frame,
)
from india_football_funnel.data.loader import load_processed_parquet, process_raw_file

logger = logging.getLogger(__name__)


def build_processed_investment_frame(raw_path: Path | None = None) -> pd.DataFrame:
    """Run ETL on a legacy investment/outcome raw file when explicitly provided."""
    if raw_path is None:
        msg = (
            "Legacy investment/outcome ETL requires an explicit raw_path. "
            "Use build_public_sports_infrastructure_frame() for the manual raw pipeline."
        )
        raise ValueError(msg)
    processed_path = process_raw_file(raw_path)
    frame = load_processed_parquet(processed_path)
    if not (frame["census_year"] == CENSUS_YEAR).all():
        msg = f"Processed data must be tagged with census_year={CENSUS_YEAR}"
        raise ValueError(msg)
    logger.info("Built processed investment frame with %d rows", len(frame))
    return frame


def build_processed_infrastructure_frame(raw_root: Path | None = None) -> pd.DataFrame:
    """Run the manual official raw pipeline and return the joined infrastructure frame."""
    root = raw_root or RAW_DATA_DIR
    frame, _report, _hashes = build_public_sports_infrastructure_frame(root)
    write_processed_infrastructure_frame(frame)
    return frame
