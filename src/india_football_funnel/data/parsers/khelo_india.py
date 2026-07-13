"""Parser for manually downloaded Khelo India state/UT assistance exports."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from india_football_funnel.data.provenance import (
    RawDatasetProvenance,
    validate_raw_file_with_provenance,
)
from india_football_funnel.data.state_names import StateReconciliationReport, reconcile_state_name
from india_football_funnel.models import KheloIndiaAssistanceRecord

CRORE_TO_INR = 10_000_000


def parse_financial_assistance(
    path: Path,
    provenance: RawDatasetProvenance | None = None,
    report: StateReconciliationReport | None = None,
) -> list[KheloIndiaAssistanceRecord]:
    """Parse state/UT financial assistance from a local official CSV export."""
    provenance = provenance or validate_raw_file_with_provenance(path)
    report = report or StateReconciliationReport()
    frame = pd.read_csv(path)
    required = {"state", "financial_assistance", "source_unit"}
    missing = required.difference(frame.columns)
    if missing:
        msg = (
            f"{path.name} is missing required columns {sorted(missing)}. "
            "Normalize the manual export to the documented Khelo India CSV layout."
        )
        raise ValueError(msg)

    records: list[KheloIndiaAssistanceRecord] = []
    for row in frame.to_dict(orient="records"):
        canonical = reconcile_state_name(str(row["state"]), report)
        if canonical is None:
            continue
        source_unit = str(row["source_unit"]).strip().lower()
        assistance = float(row["financial_assistance"])
        if source_unit == "crore":
            assistance *= CRORE_TO_INR
        elif source_unit != "inr":
            msg = f"Unsupported source_unit '{source_unit}' in {path.name}"
            raise ValueError(msg)

        records.append(
            KheloIndiaAssistanceRecord(
                canonical_state_ut=canonical,
                reporting_period=provenance.time_coverage,
                financial_assistance_inr=assistance,
                source_unit=source_unit,
                source_file=path.name,
                source_url=provenance.source_page_url,
                retrieved_at_utc=provenance.retrieved_at_utc,
                provenance_sha256=provenance.sha256,
            )
        )
    return records
