"""Cross-cutting contract test for reproduce outputs and simulation assumptions."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from tests.conftest import raw_fixture_root

from india_football_funnel.cli import run_reproduce_pipeline
from india_football_funnel.data.schema import PublicSportsInfrastructureSchema
from india_football_funnel.simulation.run_simulation import run_simulation, write_simulation_outputs
from india_football_funnel.simulation.scenarios import baseline_scenario


@pytest.mark.integration
def test_reproduce_quality_and_simulation_contract(tmp_path: Path) -> None:
    artifacts = run_reproduce_pipeline(
        raw_fixture_root(),
        tmp_path / "processed",
        tmp_path / "results",
    )

    expected_artifacts = {
        "processed",
        "csv_export",
        "summaries",
        "quality",
        "reconciliation",
        "manifest",
    }
    assert artifacts.keys() == expected_artifacts
    assert all(path.exists() for path in artifacts.values())

    processed = pd.read_parquet(artifacts["processed"])
    PublicSportsInfrastructureSchema.validate(processed)

    manifest = json.loads(artifacts["manifest"].read_text(encoding="utf-8"))
    quality = json.loads(artifacts["quality"].read_text(encoding="utf-8"))
    assert manifest["data_quality"] == quality
    assert manifest["state_reconciliation"]["unmatched"] == []
    assert manifest["state_mapping_version"] == "v1"

    result = run_simulation(baseline_scenario(n_runs=50, years=5))
    _parquet_path, summary_path = write_simulation_outputs(result, tmp_path / "simulation")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["uncalibrated"] is True
    assert summary["assumptions"]
    assert summary["assumption_registry_version"] == "v1"
