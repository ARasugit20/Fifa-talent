"""Provenance validation for manually supplied official raw datasets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, field_validator

VALID_GEOGRAPHIC_GRAINS = frozenset({"state_ut", "national"})


class RawDatasetProvenance(BaseModel):
    """Metadata for one manually downloaded official raw file."""

    dataset_name: str
    organization: str
    source_page_url: str
    download_url: str
    retrieved_at_utc: str
    source_published_or_updated_at: str
    geographic_grain: str
    time_coverage: str
    license_or_terms_note: str
    retrieval_method: str
    sha256: str
    notes: str = ""

    @field_validator("geographic_grain")
    @classmethod
    def validate_geographic_grain(cls, value: str) -> str:
        if value not in VALID_GEOGRAPHIC_GRAINS:
            msg = f"geographic_grain must be one of {sorted(VALID_GEOGRAPHIC_GRAINS)}"
            raise ValueError(msg)
        return value


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def provenance_path_for(raw_file: Path) -> Path:
    """Return the sibling provenance JSON path for a raw file."""
    return raw_file.with_name(f"{raw_file.name}.provenance.json")


def load_provenance(raw_file: Path) -> RawDatasetProvenance:
    """Load and validate provenance metadata for a raw file."""
    provenance_file = provenance_path_for(raw_file)
    if not provenance_file.exists():
        msg = (
            f"Missing provenance record for {raw_file.name}. "
            f"Expected {provenance_file.name} alongside the raw file."
        )
        raise FileNotFoundError(msg)
    payload = json.loads(provenance_file.read_text(encoding="utf-8"))
    return RawDatasetProvenance.model_validate(payload)


def validate_raw_file_with_provenance(raw_file: Path) -> RawDatasetProvenance:
    """Ensure a raw file exists and its provenance hash matches the file contents."""
    if not raw_file.exists():
        msg = f"Required raw file not found: {raw_file}"
        raise FileNotFoundError(msg)

    provenance = load_provenance(raw_file)
    actual_hash = sha256_file(raw_file)
    if provenance.sha256 != actual_hash:
        msg = (
            f"Provenance hash mismatch for {raw_file.name}. "
            "Recompute sha256 and update the provenance record."
        )
        raise ValueError(msg)
    return provenance


def discover_validated_raw_files(
    source_dir: Path,
    pattern: str = "*",
) -> list[tuple[Path, RawDatasetProvenance]]:
    """Return validated raw files and provenance records under a source directory."""
    if not source_dir.exists():
        return []
    validated: list[tuple[Path, RawDatasetProvenance]] = []
    for raw_file in sorted(source_dir.glob(pattern)):
        if raw_file.name.endswith(".provenance.json"):
            continue
        if raw_file.is_file():
            validated.append((raw_file, validate_raw_file_with_provenance(raw_file)))
    return validated
