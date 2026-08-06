"""Shared artifact writers for local and AWS infrastructure pipeline runs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from india_football_funnel.analysis.infrastructure_metrics import compute_infrastructure_summaries
from india_football_funnel.cli_options import ReproduceOptions
from india_football_funnel.data.infrastructure_pipeline import (
    PROCESSED_INFRASTRUCTURE_FILENAME,
    build_run_manifest,
    write_processed_infrastructure_frame,
    write_state_reconciliation_report,
)
from india_football_funnel.data.quality_checks import build_data_quality_report
from india_football_funnel.data.state_names import StateReconciliationReport
from india_football_funnel.models import DataQualityReport


def write_reproduce_artifacts(
    frame: pd.DataFrame,
    report: StateReconciliationReport,
    source_hashes: dict[str, str],
    processed_dir: Path,
    results_dir: Path,
    options: ReproduceOptions | None = None,
) -> dict[str, Path]:
    """Write the standard infrastructure reproduction artifact set."""
    opts = options or ReproduceOptions()
    processed_path = write_processed_infrastructure_frame(
        frame,
        processed_dir / PROCESSED_INFRASTRUCTURE_FILENAME,
    )

    artifacts: dict[str, Path] = {"processed": processed_path}
    data_quality: DataQualityReport | None = None
    if not opts.skip_quality:
        data_quality = build_data_quality_report(frame, report)

    if not opts.skip_summaries:
        summaries = compute_infrastructure_summaries(frame)
        analysis_dir = results_dir / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        summaries_path = analysis_dir / "infrastructure_summaries.json"
        summaries_path.write_text(
            json.dumps([summary.model_dump() for summary in summaries], indent=2),
            encoding="utf-8",
        )
        artifacts["summaries"] = summaries_path

    if not opts.skip_quality and data_quality is not None:
        quality_path = results_dir / "data_quality_report.json"
        quality_path.parent.mkdir(parents=True, exist_ok=True)
        quality_path.write_text(data_quality.model_dump_json(indent=2), encoding="utf-8")
        artifacts["quality"] = quality_path

    if not opts.skip_reconciliation:
        reconciliation_path = results_dir / "state_reconciliation_report.csv"
        write_state_reconciliation_report(report, reconciliation_path)
        artifacts["reconciliation"] = reconciliation_path

    if not opts.skip_manifest:
        manifest = build_run_manifest(
            frame,
            report,
            source_hashes,
            processed_path,
            data_quality=data_quality,
        )
        manifest_path = results_dir / "run_manifest.json"
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        artifacts["manifest"] = manifest_path

    if not opts.skip_csv_export:
        export_path = processed_dir / "infrastructure_by_state.csv"
        export_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(export_path, index=False)
        artifacts["csv_export"] = export_path

    return artifacts
