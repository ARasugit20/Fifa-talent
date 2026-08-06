"""CLI option models for reproduce workflows."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReproduceOptions:
    """Optional skips for partial local reproduction runs."""

    skip_summaries: bool = False
    skip_quality: bool = False
    skip_reconciliation: bool = False
    skip_manifest: bool = False
    skip_csv_export: bool = False
