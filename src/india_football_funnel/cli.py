"""CLI entry points for reproduce, simulate, and provenance workflows."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from india_football_funnel.analysis.infrastructure_metrics import compute_infrastructure_summaries
from india_football_funnel.cli_options import ReproduceOptions
from india_football_funnel.config import (
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    REQUIRED_RAW_FILES,
    RESULTS_DATA_DIR,
)
from india_football_funnel.data.infrastructure_pipeline import (
    build_public_sports_infrastructure_frame,
    build_run_manifest,
    write_processed_infrastructure_frame,
    write_state_reconciliation_report,
)
from india_football_funnel.data.loader import ensure_local_data_dirs
from india_football_funnel.data.provenance import (
    init_provenance_template,
    update_provenance_sha256,
    validate_raw_file_with_provenance,
)
from india_football_funnel.data.quality_checks import build_data_quality_report
from india_football_funnel.models import DataQualityReport
from india_football_funnel.simulation.run_simulation import run_simulation, write_simulation_outputs
from india_football_funnel.simulation.scenarios import baseline_scenario

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def _build_reproduce_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reproduce public sports infrastructure outputs.")
    parser.add_argument(
        "--skip-summaries",
        action="store_true",
        help="Skip infrastructure_summaries.json generation.",
    )
    parser.add_argument(
        "--skip-quality",
        action="store_true",
        help="Skip data_quality_report.json generation.",
    )
    parser.add_argument(
        "--skip-reconciliation",
        action="store_true",
        help="Skip state_reconciliation_report.csv generation.",
    )
    parser.add_argument(
        "--skip-manifest",
        action="store_true",
        help="Skip run_manifest.json generation.",
    )
    parser.add_argument(
        "--skip-csv-export",
        action="store_true",
        help="Skip infrastructure_by_state.csv export.",
    )
    return parser


def parse_reproduce_options(argv: list[str] | None = None) -> ReproduceOptions:
    """Parse reproduce CLI flags into a ReproduceOptions object."""
    args = _build_reproduce_parser().parse_args(argv)
    return ReproduceOptions(
        skip_summaries=args.skip_summaries,
        skip_quality=args.skip_quality,
        skip_reconciliation=args.skip_reconciliation,
        skip_manifest=args.skip_manifest,
        skip_csv_export=args.skip_csv_export,
    )


def run_reproduce_pipeline(
    raw_root: Path,
    processed_dir: Path,
    results_dir: Path,
    options: ReproduceOptions | None = None,
) -> dict[str, Path]:
    """Build local reproduction artifacts from a supplied raw-data root."""
    opts = options or ReproduceOptions()
    frame, report, source_hashes = build_public_sports_infrastructure_frame(raw_root)
    processed_path = write_processed_infrastructure_frame(
        frame,
        processed_dir / "public_sports_infrastructure.parquet",
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


def reproduce(options: ReproduceOptions | None = None, argv: list[str] | None = None) -> None:
    """Regenerate outputs from manually supplied official raw inputs."""
    _configure_logging()
    ensure_local_data_dirs()
    if options is not None:
        resolved = options
    elif argv is not None:
        resolved = parse_reproduce_options(argv)
    else:
        resolved = ReproduceOptions()
    artifacts = run_reproduce_pipeline(
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        RESULTS_DATA_DIR,
        options=resolved,
    )
    if "manifest" in artifacts:
        manifest = json.loads(artifacts["manifest"].read_text(encoding="utf-8"))
        logger.info(
            "Reproduce pipeline complete: %d state/UT rows written to %s",
            manifest["row_count"],
            artifacts["processed"],
        )
        logger.info("Caveat: %s", manifest["caveat"])
    else:
        logger.info(
            "Reproduce pipeline complete (manifest skipped): output at %s",
            artifacts["processed"],
        )


def simulate() -> None:
    """Run baseline illustrative scenario only (quick CLI)."""
    _configure_logging()
    result = run_simulation(baseline_scenario())
    write_simulation_outputs(result)
    logger.info(
        "Illustrative scenario complete (uncalibrated, not a forecast): final_medals_mean=%.1f",
        result.final_medals_mean,
    )


def _resolve_required_file_metadata(raw_file: Path) -> dict[str, str]:
    for relative_path, metadata in REQUIRED_RAW_FILES.items():
        if raw_file.name == Path(relative_path).name:
            return metadata
    msg = (
        f"No configured raw-file role found for {raw_file.name}. "
        "See docs/data_inventory.md for required filenames."
    )
    raise ValueError(msg)


def provenance_init(raw_file: Path, retrieved_at_utc: str | None = None) -> Path:
    """Create a provenance template for a manually downloaded raw file."""
    metadata = _resolve_required_file_metadata(raw_file)
    timestamp = retrieved_at_utc or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )
    return init_provenance_template(
        raw_file,
        dataset_name=metadata["role"],
        organization="Manual official download",
        source_page_url=metadata["source_page_url"],
        download_url="manual_official_download",
        retrieved_at_utc=timestamp,
        source_published_or_updated_at=timestamp[:10],
        geographic_grain="state_ut",
        time_coverage="operator-supplied",
        license_or_terms_note="Record the official license or terms in this field.",
        retrieval_method="manual_official_download",
        notes="Fill in organization and publication metadata before running iff-reproduce.",
    )


def provenance_hash(raw_file: Path) -> str:
    """Compute and persist the SHA-256 digest for a raw file's provenance record."""
    return update_provenance_sha256(raw_file).sha256


def provenance_verify(raw_file: Path) -> None:
    """Validate a raw file against its sibling provenance record."""
    validate_raw_file_with_provenance(raw_file)


def _build_provenance_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage raw-file provenance records.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a provenance JSON template.")
    init_parser.add_argument("raw_file", type=Path)

    hash_parser = subparsers.add_parser("hash", help="Compute and save SHA-256 in provenance JSON.")
    hash_parser.add_argument("raw_file", type=Path)

    verify_parser = subparsers.add_parser("verify", help="Validate raw file and provenance hash.")
    verify_parser.add_argument("raw_file", type=Path)
    return parser


def provenance_main(argv: list[str] | None = None) -> None:
    """CLI entry point for provenance helper commands."""
    _configure_logging()
    args = _build_provenance_parser().parse_args(argv)
    if args.command == "init":
        path = provenance_init(args.raw_file)
        logger.info("Wrote provenance template to %s", path)
        return
    if args.command == "hash":
        digest = provenance_hash(args.raw_file)
        logger.info("Updated provenance sha256 for %s: %s", args.raw_file.name, digest)
        return
    if args.command == "verify":
        provenance_verify(args.raw_file)
        logger.info("Provenance verified for %s", args.raw_file.name)
        return
    raise SystemExit(f"Unknown provenance command: {args.command}")


def main_reproduce() -> None:
    """Console-script entry point honoring reproduce CLI flags."""
    import sys

    reproduce(argv=sys.argv[1:])


def main() -> None:
    main_reproduce()


if __name__ == "__main__":
    main()
