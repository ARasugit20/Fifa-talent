"""Unit tests for provenance validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tests.conftest import raw_fixture_root

from india_football_funnel.data.provenance import (
    load_provenance,
    sha256_file,
    validate_raw_file_with_provenance,
)


def test_validate_raw_file_with_provenance_passes() -> None:
    raw_file = raw_fixture_root() / "mdsd/state_wise_progress.csv"
    provenance = validate_raw_file_with_provenance(raw_file)
    assert provenance.dataset_name.startswith("MD-SD")


def test_validate_raw_file_with_provenance_rejects_hash_mismatch(tmp_path: Path) -> None:
    raw_file = tmp_path / "sample.csv"
    raw_file.write_text("state,projects_total\nKerala,1\n", encoding="utf-8")
    provenance_path = raw_file.with_name("sample.csv.provenance.json")
    provenance_path.write_text(
        json.dumps(
            {
                "dataset_name": "test",
                "organization": "test",
                "source_page_url": "https://example.com",
                "download_url": "manual",
                "retrieved_at_utc": "2026-07-13T00:00:00Z",
                "source_published_or_updated_at": "2026-07-13",
                "geographic_grain": "state_ut",
                "time_coverage": "test",
                "license_or_terms_note": "test",
                "retrieval_method": "manual_official_download",
                "sha256": "deadbeef",
                "notes": "",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Provenance hash mismatch"):
        validate_raw_file_with_provenance(raw_file)


def test_load_provenance_requires_sibling_file(tmp_path: Path) -> None:
    raw_file = tmp_path / "missing.csv"
    raw_file.write_text("x", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="Missing provenance record"):
        load_provenance(raw_file)


def test_sha256_file_is_stable() -> None:
    raw_file = raw_fixture_root() / "census/state_population_2011.csv"
    provenance = load_provenance(raw_file)
    assert sha256_file(raw_file) == provenance.sha256
