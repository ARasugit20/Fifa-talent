"""Simulation orchestration and result serialization."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from india_football_funnel.config import RESULTS_DATA_DIR
from india_football_funnel.models import ScenarioParams, SimulationResult, SimulationYearResult
from india_football_funnel.simulation.talent_flow_model import run_monte_carlo_paths

logger = logging.getLogger(__name__)


def aggregate_simulation_results(
    params: ScenarioParams,
    paths: NDArray[np.float64],
) -> SimulationResult:
    """Aggregate Monte Carlo paths into summary statistics."""
    annual_results: list[SimulationYearResult] = []
    for year_idx in range(params.years):
        year_values = paths[:, year_idx]
        annual_results.append(
            SimulationYearResult(
                year=year_idx + 1,
                mean_medals=float(np.mean(year_values)),
                p10_medals=float(np.percentile(year_values, 10)),
                p90_medals=float(np.percentile(year_values, 90)),
                mean_participation_rate=params.baseline_participation_rate,
            )
        )

    final_values = paths[:, -1]
    return SimulationResult(
        scenario_name=params.name,
        n_runs=params.n_runs,
        years=params.years,
        annual_results=annual_results,
        final_medals_mean=float(np.mean(final_values)),
        final_medals_std=float(np.std(final_values)),
    )


def run_simulation(params: ScenarioParams) -> SimulationResult:
    """Execute a full Monte Carlo simulation."""
    paths = run_monte_carlo_paths(params)
    result = aggregate_simulation_results(params, paths)
    logger.info(
        "Simulation complete: scenario=%s final_medals_mean=%.1f",
        result.scenario_name,
        result.final_medals_mean,
    )
    return result


def simulation_result_to_frame(result: SimulationResult) -> pd.DataFrame:
    """Convert simulation result to a flat dataframe for storage."""
    rows = [
        {
            "scenario_name": result.scenario_name,
            "n_runs": result.n_runs,
            "year": year_result.year,
            "mean_medals": year_result.mean_medals,
            "p10_medals": year_result.p10_medals,
            "p90_medals": year_result.p90_medals,
            "mean_participation_rate": year_result.mean_participation_rate,
            "final_medals_mean": result.final_medals_mean,
            "final_medals_std": result.final_medals_std,
        }
        for year_result in result.annual_results
    ]
    return pd.DataFrame(rows)


def write_simulation_outputs(
    result: SimulationResult,
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Write simulation results as parquet and JSON summary."""
    if output_dir is None:
        output_dir = RESULTS_DATA_DIR / result.scenario_name
    output_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = output_dir / "simulation_results.parquet"
    json_path = output_dir / "simulation_summary.json"

    simulation_result_to_frame(result).to_parquet(parquet_path, index=False)
    json_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    logger.info("Wrote simulation outputs to %s", output_dir)
    return parquet_path, json_path


def load_simulation_summary(path: Path) -> SimulationResult:
    """Load a simulation summary JSON file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return SimulationResult.model_validate(payload)
