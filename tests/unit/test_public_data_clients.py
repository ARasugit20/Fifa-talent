"""Unit tests for verified public-data clients."""

from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest

from india_football_funnel.data.census_client import normalize_census_records
from india_football_funnel.data.datagovindia_client import (
    cache_raw_response_locally,
    fetch_khelo_india_resources,
    get_datagovindia_api_key,
)
from india_football_funnel.data.fifa_afc_reports import metrics_to_frame
from india_football_funnel.data.isl_data import load_isl_snapshot, verify_isl_license
from india_football_funnel.data.khelo_india_centres import unavailable_facility_frame
from india_football_funnel.models import PdfExtractedMetric


def test_census_records_are_tagged_2011() -> None:
    frame = normalize_census_records([{"State": "Kerala", "District": "Kochi", "Age_10_17": 1000}])
    assert (frame["census_year"] == 2011).all()


def test_datagovindia_api_key_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATAGOVINDIA_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="DATAGOVINDIA_API_KEY"):
        get_datagovindia_api_key()


def test_fetch_khelo_india_resources_mocked() -> None:
    client = MagicMock()
    client.get_data.side_effect = [
        {"records": [{"state": "Kerala", "medals": 1}]},
        {"records": [{"state": "Kerala", "budget": 100}]},
    ]
    client.search.return_value = {"records": [{"title": "Khelo India"}]}
    resources = fetch_khelo_india_resources(client)
    assert resources["medal_tally"][0]["medals"] == 1
    assert resources["budget_allocation"][0]["budget"] == 100


def test_cache_raw_response_locally(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = cache_raw_response_locally(tmp_path, "medal_tally", [{"state": "Kerala"}])
    assert path.exists()
    assert "Kerala" in path.read_text(encoding="utf-8")


def test_unavailable_facility_frame_marks_status() -> None:
    frame = unavailable_facility_frame(["Kerala"], year=2023)
    assert frame.loc[0, "facility_data_status"] == "not_currently_available"
    assert pd.isna(frame.loc[0, "khelo_india_centres"])


def test_pdf_metrics_require_source_citation() -> None:
    frame = metrics_to_frame(
        [
            PdfExtractedMetric(
                metric_name="participation",
                metric_value=100,
                source_pdf="afc-report.pdf",
                source_page=3,
                extraction_note="verified table",
            )
        ]
    )
    assert frame["source_pdf"].notna().all()
    assert frame["source_page"].notna().all()


def test_isl_license_gate_blocks_unknown_license(tmp_path) -> None:  # type: ignore[no-untyped-def]
    assert not verify_isl_license("unknown", "2024-01-01")
    snapshot = tmp_path / "isl.csv"
    snapshot.write_text("team,points\nA,1\n", encoding="utf-8")
    with pytest.raises(PermissionError):
        load_isl_snapshot(snapshot, license_name=None, last_updated=None)
