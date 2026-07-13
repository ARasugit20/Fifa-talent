"""End-to-end integration test for the infrastructure pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tests.conftest import raw_fixture_root

from india_football_funnel.analysis.infrastructure_metrics import compute_infrastructure_summaries
from india_football_funnel.config import CENSUS_YEAR
from india_football_funnel.data.infrastructure_pipeline import (
    build_public_sports_infrastructure_frame,
    build_run_manifest,
    write_processed_infrastructure_frame,
)


@pytest.mark.integration
def test_infrastructure_pipeline_end_to_end(tmp_path: Path) -> None:
    frame, report, source_hashes = build_public_sports_infrastructure_frame(raw_fixture_root())

    assert len(frame) == 10
    assert (frame["denominator_year"] == CENSUS_YEAR).all()
    assert frame["denominator_is_stale"].all()
    assert not report.unmatched

    summaries = compute_infrastructure_summaries(frame)
    assert len(summaries) == 10
    assert all(summary.denominator_is_stale for summary in summaries)

    processed_path = write_processed_infrastructure_frame(frame, tmp_path / "infra.parquet")
    manifest = build_run_manifest(frame, report, source_hashes, processed_path)
    manifest_path = tmp_path / "run_manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["row_count"] == 10
    assert "source_hashes" in payload
    assert "not football-specific" in payload["caveat"]
