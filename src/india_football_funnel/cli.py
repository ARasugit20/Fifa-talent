"""CLI entry points for reproduce and simulate workflows."""

from __future__ import annotations

import json
import logging

from india_football_funnel.analysis.associative_regression import run_default_regressions
from india_football_funnel.analysis.funnel_metrics import compute_all_state_summaries
from india_football_funnel.config import PROCESSED_DATA_DIR, RAW_DATA_DIR, RESULTS_DATA_DIR
from india_football_funnel.data.loader import (
    ensure_local_data_dirs,
    load_processed_parquet,
    process_raw_file,
)
from india_football_funnel.data.scrapers.state_registry import scrape_state_registry_stub
from india_football_funnel.simulation.run_simulation import run_simulation, write_simulation_outputs
from india_football_funnel.simulation.scenarios import baseline_scenario, intervention_scenario

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def reproduce() -> None:
    """Regenerate outputs from public-data shaped raw inputs."""
    _configure_logging()
    ensure_local_data_dirs()

    raw_path = RAW_DATA_DIR / "investment_outcomes.csv"
    if not raw_path.exists():
        scrape_state_registry_stub(raw_path)

    processed_path = process_raw_file(raw_path)
    frame = load_processed_parquet(processed_path)

    summaries = compute_all_state_summaries(frame)
    regressions = run_default_regressions(frame)

    analysis_dir = RESULTS_DATA_DIR / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    summaries_path = analysis_dir / "funnel_summaries.json"
    summaries_path.write_text(
        json.dumps([s.model_dump() for s in summaries], indent=2, default=str),
        encoding="utf-8",
    )

    participation_path = PROCESSED_DATA_DIR / "participation_by_state.csv"
    frame[
        [
            "state",
            "year",
            "census_year",
            "budget_per_capita",
            "participation_rate",
            "medals_per_participant",
            "facility_data_status",
        ]
    ].to_csv(participation_path, index=False)

    regressions_path = analysis_dir / "regression_results.json"
    regressions_path.write_text(
        json.dumps([r.model_dump() for r in regressions], indent=2),
        encoding="utf-8",
    )

    for scenario in (baseline_scenario(n_runs=200), intervention_scenario(n_runs=200)):
        result = run_simulation(scenario)
        write_simulation_outputs(result)

    logger.info("Reproduce pipeline complete")


def simulate() -> None:
    """Run baseline simulation only (quick CLI)."""
    _configure_logging()
    result = run_simulation(baseline_scenario())
    write_simulation_outputs(result)
    logger.info(
        "Illustrative scenario complete (uncalibrated, not a forecast): " "final_medals_mean=%.1f",
        result.final_medals_mean,
    )


def main() -> None:
    reproduce()


if __name__ == "__main__":
    main()
