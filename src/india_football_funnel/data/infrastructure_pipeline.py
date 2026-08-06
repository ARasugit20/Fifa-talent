"""Build the joined public sports infrastructure dataset from manual raw inputs."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import cast

import pandas as pd

from india_football_funnel.config import (
    INFRASTRUCTURE_CAUTION,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    REQUIRED_RAW_FILES,
    STATE_MAPPING_VERSION,
)
from india_football_funnel.data.parsers.census import parse_state_denominators
from india_football_funnel.data.parsers.khelo_india import parse_financial_assistance
from india_football_funnel.data.parsers.mdsd import parse_grantee_amounts, parse_state_wise_progress
from india_football_funnel.data.provenance import validate_raw_file_with_provenance
from india_football_funnel.data.schema import PublicSportsInfrastructureSchema
from india_football_funnel.data.state_names import StateReconciliationReport
from india_football_funnel.models import (
    DataQualityReport,
    PublicSportsInfrastructureRecord,
    RunManifest,
)

logger = logging.getLogger(__name__)

PROCESSED_INFRASTRUCTURE_FILENAME = "public_sports_infrastructure.parquet"


def required_raw_path(relative_path: str, raw_root: Path | None = None) -> Path:
    """Resolve a required raw file path relative to the raw data root."""
    root = raw_root or RAW_DATA_DIR
    return root / relative_path


def validate_required_raw_inputs(raw_root: Path | None = None) -> dict[str, str]:
    """Fail fast when required raw files or provenance records are missing."""
    root = raw_root or RAW_DATA_DIR
    missing: list[str] = []
    source_hashes: dict[str, str] = {}

    for relative_path, metadata in REQUIRED_RAW_FILES.items():
        raw_path = required_raw_path(relative_path, root)
        if not raw_path.exists():
            missing.append(
                f"- {relative_path}: {metadata['role']}. "
                f"Download from {metadata['source_page_url']} and place under data/raw/."
            )
            continue
        provenance = validate_raw_file_with_provenance(raw_path)
        source_hashes[relative_path] = provenance.sha256

    if missing:
        msg = "Required official raw inputs are missing:\n" + "\n".join(missing)
        raise FileNotFoundError(msg)
    return source_hashes


def build_public_sports_infrastructure_frame(
    raw_root: Path | None = None,
) -> tuple[pd.DataFrame, StateReconciliationReport, dict[str, str]]:
    """Parse, reconcile, and join manually supplied official raw inputs."""
    root = raw_root or RAW_DATA_DIR
    source_hashes = validate_required_raw_inputs(root)
    report = StateReconciliationReport()

    progress_records = parse_state_wise_progress(
        required_raw_path("mdsd/state_wise_progress.csv", root),
        report=report,
    )
    sanction_records = parse_grantee_amounts(
        required_raw_path("mdsd/grantee_amounts.csv", root),
        report=report,
    )
    assistance_records = parse_financial_assistance(
        required_raw_path("khelo_india/financial_assistance.csv", root),
        report=report,
    )
    denominator_records = parse_state_denominators(
        required_raw_path("census/state_population_2011.csv", root),
        report=report,
    )

    if report.has_blocking_issues:
        msg = "Unmapped state/UT names found during reconciliation: " f"{sorted(report.unmatched)}"
        raise ValueError(msg)

    progress_by_state = {record.canonical_state_ut: record for record in progress_records}
    sanction_by_state = {record.canonical_state_ut: record for record in sanction_records}
    assistance_by_state = {record.canonical_state_ut: record for record in assistance_records}
    denominator_by_state = {record.canonical_state_ut: record for record in denominator_records}

    joined_states = sorted(
        set(progress_by_state)
        & set(sanction_by_state)
        & set(assistance_by_state)
        & set(denominator_by_state)
    )
    if not joined_states:
        msg = "No state/UT rows could be joined across all required raw inputs."
        raise ValueError(msg)

    records: list[PublicSportsInfrastructureRecord] = []
    for state in joined_states:
        progress = progress_by_state[state]
        sanction = sanction_by_state[state]
        assistance = assistance_by_state[state]
        denominator = denominator_by_state[state]
        records.append(
            PublicSportsInfrastructureRecord(
                canonical_state_ut=state,
                reporting_period=progress.reporting_period,
                projects_to_be_started=progress.projects_to_be_started,
                projects_under_progress=progress.projects_under_progress,
                projects_completed=progress.projects_completed,
                projects_total=progress.projects_total,
                amount_sanctioned_inr=sanction.amount_sanctioned_inr,
                amount_released_inr=sanction.amount_released_inr,
                financial_assistance_inr=assistance.financial_assistance_inr,
                denominator_value=denominator.denominator_value,
                denominator_definition=denominator.denominator_definition,
                denominator_year=denominator.denominator_year,
                denominator_is_stale=denominator.denominator_is_stale,
                source_file=";".join(
                    sorted(
                        {
                            progress.source_file,
                            sanction.source_file,
                            assistance.source_file,
                            denominator.source_file,
                        }
                    )
                ),
                source_url=progress.source_url,
                retrieved_at_utc=progress.retrieved_at_utc,
                provenance_sha256=";".join(
                    sorted(
                        {
                            progress.provenance_sha256,
                            sanction.provenance_sha256,
                            assistance.provenance_sha256,
                            denominator.provenance_sha256,
                        }
                    )
                ),
            )
        )

    frame = pd.DataFrame([record.model_dump() for record in records])
    validated = cast(pd.DataFrame, PublicSportsInfrastructureSchema.validate(frame))
    logger.info("Built public sports infrastructure frame with %d rows", len(validated))
    return validated, report, source_hashes


def write_processed_infrastructure_frame(
    frame: pd.DataFrame,
    output_path: Path | None = None,
) -> Path:
    """Write the joined infrastructure dataset to parquet."""
    if output_path is None:
        output_path = PROCESSED_DATA_DIR / PROCESSED_INFRASTRUCTURE_FILENAME
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output_path, index=False)
    logger.info("Wrote processed infrastructure parquet to %s", output_path)
    return output_path


def build_run_manifest(
    frame: pd.DataFrame,
    report: StateReconciliationReport,
    source_hashes: dict[str, str],
    processed_output: Path,
    data_quality: DataQualityReport | None = None,
) -> RunManifest:
    """Create a reproducibility manifest for the infrastructure pipeline run."""
    return RunManifest(
        caveat=INFRASTRUCTURE_CAUTION,
        row_count=len(frame),
        reporting_periods=sorted(frame["reporting_period"].unique().tolist()),
        source_hashes=source_hashes,
        state_reconciliation={
            "matched": sorted(report.matched),
            "aliased": report.aliased,
            "unmatched": sorted(report.unmatched),
            "excluded": sorted(report.excluded),
        },
        state_mapping_version=STATE_MAPPING_VERSION,
        processed_output=str(processed_output),
        data_quality=data_quality,
    )


def write_state_reconciliation_report(
    report: StateReconciliationReport,
    output_path: Path,
) -> Path:
    """Write a compact audit trail for state/UT reconciliation outcomes."""
    rows: list[dict[str, str]] = []
    aliased_targets = set(report.aliased.values())
    for state in sorted(report.matched):
        aliases = sorted(alias for alias, target in report.aliased.items() if target == state)
        rows.append(
            {
                "canonical_state_ut": state,
                "status": "aliased" if state in aliased_targets else "matched",
                "alias_from": ";".join(aliases),
            }
        )
    rows.extend(
        {
            "canonical_state_ut": state,
            "status": "unmatched",
            "alias_from": "",
        }
        for state in sorted(report.unmatched)
    )
    rows.extend(
        {
            "canonical_state_ut": state,
            "status": "excluded",
            "alias_from": "",
        }
        for state in sorted(report.excluded)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["canonical_state_ut", "status", "alias_from"]).to_csv(
        output_path,
        index=False,
    )
    return output_path
