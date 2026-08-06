"""Unit tests for CLI and config."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tests.conftest import raw_fixture_root

from india_football_funnel.cli import reproduce, simulate
from india_football_funnel.config import Settings, get_settings
from india_football_funnel.simulation.run_simulation import load_simulation_summary
from india_football_funnel.simulation.scenarios import get_scenario_by_name


def test_settings_resolved_bucket() -> None:
    settings = Settings(aws_account_id="123456789012")
    assert settings.resolved_bucket_name == "india-football-funnel-data-123456789012"


def test_get_settings_cached() -> None:
    assert get_settings() is get_settings()


def test_unknown_scenario_raises() -> None:
    with pytest.raises(ValueError, match="Unknown scenario"):
        get_scenario_by_name("nonexistent")


def test_reproduce_writes_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw_dir = raw_fixture_root()
    processed_dir = tmp_path / "processed"
    results_dir = tmp_path / "results"
    for target in (
        "india_football_funnel.cli",
        "india_football_funnel.config",
    ):
        monkeypatch.setattr(f"{target}.RAW_DATA_DIR", raw_dir)
        monkeypatch.setattr(f"{target}.PROCESSED_DATA_DIR", processed_dir)
        monkeypatch.setattr(f"{target}.RESULTS_DATA_DIR", results_dir)
    monkeypatch.setattr("india_football_funnel.data.infrastructure_pipeline.RAW_DATA_DIR", raw_dir)
    monkeypatch.setattr(
        "india_football_funnel.data.infrastructure_pipeline.PROCESSED_DATA_DIR",
        processed_dir,
    )

    reproduce()

    assert (processed_dir / "public_sports_infrastructure.parquet").exists()
    assert (processed_dir / "infrastructure_by_state.csv").exists()
    assert (results_dir / "analysis" / "infrastructure_summaries.json").exists()
    assert (results_dir / "data_quality_report.json").exists()
    assert (results_dir / "state_reconciliation_report.csv").exists()
    assert (results_dir / "run_manifest.json").exists()

    manifest = json.loads((results_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["row_count"] == 10
    assert "not football-specific" in manifest["caveat"]
    assert manifest["data_quality"]["stale_denominator_count"] == 10


def test_reproduce_fails_without_required_raw_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    empty_raw = tmp_path / "raw"
    empty_raw.mkdir()
    monkeypatch.setattr("india_football_funnel.cli.RAW_DATA_DIR", empty_raw)

    with pytest.raises(FileNotFoundError, match="Required official raw inputs are missing"):
        reproduce()


def test_simulate_writes_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    results_dir = tmp_path / "results"
    monkeypatch.setattr(
        "india_football_funnel.simulation.run_simulation.RESULTS_DATA_DIR",
        results_dir,
    )

    simulate()

    assert (results_dir / "baseline" / "simulation_summary.json").exists()
    assert (results_dir / "baseline" / "simulation_results.parquet").exists()


def test_load_simulation_summary(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "scenario_name": "baseline",
                "n_runs": 10,
                "years": 2,
                "annual_results": [
                    {
                        "year": 1,
                        "mean_medals": 5.0,
                        "p10_medals": 3.0,
                        "p90_medals": 7.0,
                        "mean_participation_rate": 0.012,
                    }
                ],
                "final_medals_mean": 6.0,
                "final_medals_std": 1.0,
                "assumption_based": True,
                "uncalibrated": True,
            }
        ),
        encoding="utf-8",
    )
    result = load_simulation_summary(summary_path)
    assert result.scenario_name == "baseline"
    assert result.n_runs == 10
