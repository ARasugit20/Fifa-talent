"""CLI entry points for reproduce and simulate workflows."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from india_football_funnel.analysis.infrastructure_metrics import compute_infrastructure_summaries
from india_football_funnel.config import PROCESSED_DATA_DIR, RAW_DATA_DIR, RESULTS_DATA_DIR
from india_football_funnel.data.infrastructure_pipeline import (
    build_public_sports_infrastructure_frame,
    build_run_manifest,
    write_processed_infrastructure_frame,
    write_state_reconciliation_report,
)
from india_football_funnel.data.loader import ensure_local_data_dirs
from india_football_funnel.data.quality_checks import build_data_quality_report
from india_football_funnel.simulation.run_simulation import run_simulation, write_simulation_outputs
from india_football_funnel.simulation.scenarios import baseline_scenario

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def run_reproduce_pipeline(
    raw_root: Path,
    processed_dir: Path,
    results_dir: Path,
) -> dict[str, Path]:
    """Build all local reproduction artifacts from a supplied raw-data root."""
    frame, report, source_hashes = build_public_sports_infrastructure_frame(raw_root)
    processed_path = write_processed_infrastructure_frame(
        frame,
        processed_dir / "public_sports_infrastructure.parquet",
    )
    summaries = compute_infrastructure_summaries(frame)
    data_quality = build_data_quality_report(frame, report)

    analysis_dir = results_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    summaries_path = analysis_dir / "infrastructure_summaries.json"
    summaries_path.write_text(
        json.dumps([summary.model_dump() for summary in summaries], indent=2),
        encoding="utf-8",
    )

    quality_path = results_dir / "data_quality_report.json"
    quality_path.parent.mkdir(parents=True, exist_ok=True)
    quality_path.write_text(data_quality.model_dump_json(indent=2), encoding="utf-8")

    reconciliation_path = results_dir / "state_reconciliation_report.csv"
    write_state_reconciliation_report(report, reconciliation_path)

    manifest = build_run_manifest(
        frame,
        report,
        source_hashes,
        processed_path,
        data_quality=data_quality,
    )
    manifest_path = results_dir / "run_manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    export_path = processed_dir / "infrastructure_by_state.csv"
    export_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(export_path, index=False)
    return {
        "processed": processed_path,
        "csv_export": export_path,
        "summaries": summaries_path,
        "quality": quality_path,
        "reconciliation": reconciliation_path,
        "manifest": manifest_path,
    }


def reproduce() -> None:
    """Regenerate outputs from manually supplied official raw inputs."""
    _configure_logging()
    ensure_local_data_dirs()
    artifacts = run_reproduce_pipeline(RAW_DATA_DIR, PROCESSED_DATA_DIR, RESULTS_DATA_DIR)
    manifest = json.loads(artifacts["manifest"].read_text(encoding="utf-8"))

    logger.info(
        "Reproduce pipeline complete: %d state/UT rows written to %s",
        manifest["row_count"],
        artifacts["processed"],
    )
    logger.info("Caveat: %s", manifest["caveat"])


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
