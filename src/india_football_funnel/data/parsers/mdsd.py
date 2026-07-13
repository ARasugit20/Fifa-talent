"""Parser for manually downloaded MD-SD Khelo India infrastructure exports."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from india_football_funnel.data.provenance import (
    RawDatasetProvenance,
    validate_raw_file_with_provenance,
)
from india_football_funnel.data.state_names import StateReconciliationReport, reconcile_state_name
from india_football_funnel.models import MdsdProjectProgressRecord, MdsdSanctionRecord

CRORE_TO_INR = 10_000_000


def _require_columns(frame: pd.DataFrame, required: set[str], source_file: Path) -> None:
    missing = required.difference(frame.columns)
    if missing:
        msg = (
            f"{source_file.name} is missing required columns {sorted(missing)}. "
            "Normalize the manual export to the documented MD-SD CSV layout."
        )
        raise ValueError(msg)


def parse_state_wise_progress(
    path: Path,
    provenance: RawDatasetProvenance | None = None,
    report: StateReconciliationReport | None = None,
) -> list[MdsdProjectProgressRecord]:
    """Parse MD-SD state/UT project progress counts from a local CSV export."""
    provenance = provenance or validate_raw_file_with_provenance(path)
    report = report or StateReconciliationReport()
    frame = pd.read_csv(path)
    _require_columns(
        frame,
        {
            "state",
            "projects_to_be_started",
            "projects_under_progress",
            "projects_completed",
            "projects_total",
        },
        path,
    )

    records: list[MdsdProjectProgressRecord] = []
    for row in frame.to_dict(orient="records"):
        canonical = reconcile_state_name(str(row["state"]), report)
        if canonical is None:
            continue
        records.append(
            MdsdProjectProgressRecord(
                canonical_state_ut=canonical,
                reporting_period=provenance.time_coverage,
                projects_to_be_started=int(row["projects_to_be_started"]),
                projects_under_progress=int(row["projects_under_progress"]),
                projects_completed=int(row["projects_completed"]),
                projects_total=int(row["projects_total"]),
                source_file=path.name,
                source_url=provenance.source_page_url,
                retrieved_at_utc=provenance.retrieved_at_utc,
                provenance_sha256=provenance.sha256,
            )
        )
    return records


def parse_grantee_amounts(
    path: Path,
    provenance: RawDatasetProvenance | None = None,
    report: StateReconciliationReport | None = None,
) -> list[MdsdSanctionRecord]:
    """Parse MD-SD amount sanctioned/released values from a local CSV export."""
    provenance = provenance or validate_raw_file_with_provenance(path)
    report = report or StateReconciliationReport()
    frame = pd.read_csv(path)
    _require_columns(
        frame,
        {"state", "amount_sanctioned", "amount_released", "source_unit"},
        path,
    )

    records: list[MdsdSanctionRecord] = []
    for row in frame.to_dict(orient="records"):
        canonical = reconcile_state_name(str(row["state"]), report)
        if canonical is None:
            continue
        source_unit = str(row["source_unit"]).strip().lower()
        sanctioned = float(row["amount_sanctioned"])
        released = float(row["amount_released"])
        if source_unit == "crore":
            sanctioned *= CRORE_TO_INR
            released *= CRORE_TO_INR
        elif source_unit != "inr":
            msg = f"Unsupported source_unit '{source_unit}' in {path.name}"
            raise ValueError(msg)

        records.append(
            MdsdSanctionRecord(
                canonical_state_ut=canonical,
                reporting_period=provenance.time_coverage,
                amount_sanctioned_inr=sanctioned,
                amount_released_inr=released,
                source_unit=source_unit,
                source_file=path.name,
                source_url=provenance.source_page_url,
                retrieved_at_utc=provenance.retrieved_at_utc,
                provenance_sha256=provenance.sha256,
            )
        )
    return records
