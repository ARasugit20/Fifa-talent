"""Census of India ingestion with API primary and Excel fallback."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

from india_football_funnel.config import CENSUS_API_BASE_URL, CENSUS_TABLES_URL, CENSUS_YEAR

logger = logging.getLogger(__name__)


def fetch_census_api_table(
    table_id: str,
    params: dict[str, str] | None = None,
    timeout_seconds: int = 30,
) -> list[dict[str, Any]]:
    """Fetch a Census table from the public API.

    Census 2011 is the latest complete source; callers must keep the explicit
    census_year tag in downstream records.
    """
    query = urlencode(params or {})
    url = f"{CENSUS_API_BASE_URL}/{table_id}"
    if query:
        url = f"{url}?{query}"
    logger.info("Fetching Census API table %s", table_id)
    try:
        with urlopen(url, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, TimeoutError) as exc:
        msg = f"Census API request failed for table {table_id}: {exc}"
        raise ConnectionError(msg) from exc

    records = payload.get("data", payload) if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        msg = f"Unexpected Census API payload for table {table_id}"
        raise ValueError(msg)
    return [record for record in records if isinstance(record, dict)]


def load_census_excel_fallback(path: Path) -> pd.DataFrame:
    """Parse a downloaded Census Excel fallback table."""
    logger.info("Loading Census Excel fallback from %s", path)
    frame = pd.read_excel(path)
    required = {"state", "district", "youth_population_10_17"}
    missing = required.difference(frame.columns)
    if missing:
        msg = f"Census fallback missing columns: {sorted(missing)}"
        raise ValueError(msg)
    frame["census_year"] = CENSUS_YEAR
    return frame


def normalize_census_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Normalize Census API records to the project schema."""
    frame = pd.DataFrame(records)
    rename_map = {
        "State": "state",
        "District": "district",
        "Age_10_17": "youth_population_10_17",
        "youth_population": "youth_population_10_17",
    }
    frame = frame.rename(columns={k: v for k, v in rename_map.items() if k in frame.columns})
    required = {"state", "district", "youth_population_10_17"}
    missing = required.difference(frame.columns)
    if missing:
        msg = f"Census records missing columns: {sorted(missing)}"
        raise ValueError(msg)
    frame["census_year"] = CENSUS_YEAR
    return frame[["state", "district", "youth_population_10_17", "census_year"]]


def load_youth_population(
    table_id: str,
    fallback_excel_path: Path | None = None,
    params: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Load district youth population, using Excel fallback if the API is unreliable."""
    try:
        return normalize_census_records(fetch_census_api_table(table_id, params=params))
    except (ConnectionError, ValueError) as exc:
        if fallback_excel_path is None:
            raise
        logger.warning(
            "Falling back to Census Excel table from %s after API issue: %s. " "Source index: %s",
            fallback_excel_path,
            exc,
            CENSUS_TABLES_URL,
        )
        return load_census_excel_fallback(fallback_excel_path)
