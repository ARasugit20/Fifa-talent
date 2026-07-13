"""Shared test helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from india_football_funnel.config import FIXTURES_DIR


def fixture_path(name: str) -> Path:
    return FIXTURES_DIR / name


def raw_fixture_root() -> Path:
    return FIXTURES_DIR / "raw"


def load_fixture_csv(name: str = "sample_investment_outcomes.csv") -> pd.DataFrame:
    return pd.read_csv(fixture_path(name))
