"""Unit tests for CLI and config."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

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
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    results_dir = tmp_path / "results"
    for target in (
        "india_football_funnel.cli",
        "india_football_funnel.config",
        "india_football_funnel.data.loader",
    ):
        monkeypatch.setattr(f"{target}.RAW_DATA_DIR", raw_dir)
        monkeypatch.setattr(f"{target}.PROCESSED_DATA_DIR", processed_dir)
        monkeypatch.setattr(f"{target}.RESULTS_DATA_DIR", results_dir)
    monkeypatch.setattr(
        "india_football_funnel.simulation.run_simulation.RESULTS_DATA_DIR",
        results_dir,
    )

    reproduce()

    assert (raw_dir / "investment_outcomes.csv").exists()
    assert (processed_dir / "investment_outcomes.parquet").exists()
    assert (processed_dir / "participation_by_state.csv").exists()
    assert (results_dir / "analysis" / "funnel_summaries.json").exists()
    assert (results_dir / "analysis" / "regression_results.json").exists()
    assert (results_dir / "baseline" / "simulation_summary.json").exists()
    assert (results_dir / "top_quartile_budget" / "simulation_summary.json").exists()


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
            }
        ),
        encoding="utf-8",
    )
    result = load_simulation_summary(summary_path)
    assert result.scenario_name == "baseline"
    assert result.n_runs == 10
