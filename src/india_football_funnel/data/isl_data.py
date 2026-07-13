"""Indian Super League data ingestion with license gate."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def verify_isl_license(license_name: str | None, last_updated: str | None) -> bool:
    """Return True only when Kaggle license and update date were manually recorded."""
    if not license_name or not last_updated:
        logger.warning("ISL dataset license or last-updated date is missing; disabling ISL layer")
        return False
    restricted_tokens = ("unknown", "unclear", "all rights reserved", "non-commercial")
    return not any(token in license_name.lower() for token in restricted_tokens)


def load_isl_snapshot(
    snapshot_path: Path,
    license_name: str | None,
    last_updated: str | None,
) -> pd.DataFrame:
    """Load a static ISL snapshot only after license provenance is explicit."""
    if not verify_isl_license(license_name, last_updated):
        msg = "ISL snapshot is disabled until Kaggle license and last-updated date are verified"
        raise PermissionError(msg)
    frame = pd.read_csv(snapshot_path)
    frame["source_license"] = license_name
    frame["source_last_updated"] = last_updated
    return frame


def isl_layer_status(license_name: str | None, last_updated: str | None) -> str:
    """Document whether the optional ISL layer can be used in v1."""
    if verify_isl_license(license_name, last_updated):
        return "available"
    return "dropped_until_license_verified"
