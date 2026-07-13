"""CLI entry points for reproduce and simulate workflows."""

from __future__ import annotations

import json
import logging

from india_football_funnel.analysis.infrastructure_metrics import compute_infrastructure_summaries
from india_football_funnel.config import PROCESSED_DATA_DIR, RAW_DATA_DIR, RESULTS_DATA_DIR
from india_football_funnel.data.infrastructure_pipeline import (
    build_public_sports_infrastructure_frame,
    build_run_manifest,
    write_processed_infrastructure_frame,
)
from india_football_funnel.data.loader import ensure_local_data_dirs
from india_football_funnel.simulation.run_simulation import run_simulation, write_simulation_outputs
from india_football_funnel.simulation.scenarios import baseline_scenario

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def reproduce() -> None:
    """Regenerate outputs from manually supplied official raw inputs."""
    _configure_logging()
    ensure_local_data_dirs()

    frame, report, source_hashes = build_public_sports_infrastructure_frame(RAW_DATA_DIR)
    processed_path = write_processed_infrastructure_frame(frame)
    summaries = compute_infrastructure_summaries(frame)

    analysis_dir = RESULTS_DATA_DIR / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    summaries_path = analysis_dir / "infrastructure_summaries.json"
    summaries_path.write_text(
        json.dumps([summary.model_dump() for summary in summaries], indent=2),
        encoding="utf-8",
    )

    manifest = build_run_manifest(frame, report, source_hashes, processed_path)
    manifest_path = RESULTS_DATA_DIR / "run_manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    export_path = PROCESSED_DATA_DIR / "infrastructure_by_state.csv"
    frame.to_csv(export_path, index=False)

    logger.info(
        "Reproduce pipeline complete: %d state/UT rows written to %s",
        len(frame),
        processed_path,
    )
    logger.info("Caveat: %s", manifest.caveat)


def simulate() -> None:
    """Run baseline illustrative scenario only (quick CLI)."""
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
