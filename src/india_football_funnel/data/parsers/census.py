"""Parser for manually downloaded Census 2011 denominator files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from india_football_funnel.config import CENSUS_YEAR
from india_football_funnel.data.provenance import (
    RawDatasetProvenance,
    validate_raw_file_with_provenance,
)
from india_football_funnel.data.state_names import (
    EXCLUDED_FROM_CENSUS_2011_DENOMINATOR,
    StateReconciliationReport,
    reconcile_state_name,
)
from india_football_funnel.models import CensusDenominatorRecord


def parse_state_denominators(
    path: Path,
    provenance: RawDatasetProvenance | None = None,
    report: StateReconciliationReport | None = None,
) -> list[CensusDenominatorRecord]:
    """Parse Census 2011 state/UT denominator values from a local CSV export."""
    provenance = provenance or validate_raw_file_with_provenance(path)
    report = report or StateReconciliationReport()
    frame = pd.read_csv(path)
    required = {"state", "denominator_value", "denominator_definition"}
    missing = required.difference(frame.columns)
    if missing:
        msg = (
            f"{path.name} is missing required columns {sorted(missing)}. "
            "Provide a Census 2011 state/UT denominator file with explicit definitions."
        )
        raise ValueError(msg)

    records: list[CensusDenominatorRecord] = []
    for row in frame.to_dict(orient="records"):
        canonical = reconcile_state_name(str(row["state"]), report)
        if canonical is None:
            continue
        if canonical in EXCLUDED_FROM_CENSUS_2011_DENOMINATOR:
            if canonical not in report.excluded:
                report.excluded.append(canonical)
            continue

        records.append(
            CensusDenominatorRecord(
                canonical_state_ut=canonical,
                denominator_value=int(row["denominator_value"]),
                denominator_definition=str(row["denominator_definition"]),
                denominator_year=CENSUS_YEAR,
                denominator_is_stale=True,
                source_file=path.name,
                source_url=provenance.source_page_url,
                retrieved_at_utc=provenance.retrieved_at_utc,
                provenance_sha256=provenance.sha256,
            )
        )
    return records
