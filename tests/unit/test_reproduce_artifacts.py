"""Unit tests for shared reproduce artifact writer."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import raw_fixture_root

from india_football_funnel.cli_options import ReproduceOptions
from india_football_funnel.data.infrastructure_pipeline import (
    build_public_sports_infrastructure_frame,
)
from india_football_funnel.data.reproduce_artifacts import write_reproduce_artifacts


def test_write_reproduce_artifacts_honors_skip_flags(tmp_path: Path) -> None:
    frame, report, source_hashes = build_public_sports_infrastructure_frame(raw_fixture_root())
    processed_dir = tmp_path / "processed"
    results_dir = tmp_path / "results"

    artifacts = write_reproduce_artifacts(
        frame,
        report,
        source_hashes,
        processed_dir,
        results_dir,
        options=ReproduceOptions(
            skip_quality=True,
            skip_summaries=True,
            skip_reconciliation=True,
            skip_manifest=True,
            skip_csv_export=True,
        ),
    )

    assert set(artifacts.keys()) == {"processed"}
    assert artifacts["processed"].exists()
