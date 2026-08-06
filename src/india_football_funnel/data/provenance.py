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
        msg = (
            f"Required raw file not found: {raw_file}. "
            "See docs/data_inventory.md for required inputs and placement."
        )
        raise FileNotFoundError(msg)

    provenance = load_provenance(raw_file)
    actual_hash = sha256_file(raw_file)
    if provenance.sha256 != actual_hash:
        msg = (
            f"Provenance hash mismatch for {raw_file.name}. "
            f"Expected {provenance.sha256}, computed {actual_hash}. "
            "Run `iff-provenance hash <file>` to update the provenance record."
        )
        raise ValueError(msg)
    return provenance


def init_provenance_template(raw_file: Path, **overrides: str) -> Path:
    """Write a sibling provenance JSON template for a raw file."""
    if not raw_file.exists():
        msg = f"Cannot initialize provenance for missing raw file: {raw_file}"
        raise FileNotFoundError(msg)

    provenance_file = provenance_path_for(raw_file)
    if provenance_file.exists():
        msg = f"Provenance record already exists: {provenance_file.name}"
        raise FileExistsError(msg)

    payload = {
        "dataset_name": overrides.get("dataset_name", raw_file.stem.replace("_", " ")),
        "organization": overrides.get("organization", ""),
        "source_page_url": overrides.get("source_page_url", ""),
        "download_url": overrides.get("download_url", "manual_official_download"),
        "retrieved_at_utc": overrides.get("retrieved_at_utc", ""),
        "source_published_or_updated_at": overrides.get("source_published_or_updated_at", ""),
        "geographic_grain": overrides.get("geographic_grain", "state_ut"),
        "time_coverage": overrides.get("time_coverage", ""),
        "license_or_terms_note": overrides.get("license_or_terms_note", ""),
        "retrieval_method": overrides.get("retrieval_method", "manual_official_download"),
        "sha256": sha256_file(raw_file),
        "notes": overrides.get("notes", ""),
    }
    provenance_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return provenance_file


def update_provenance_sha256(raw_file: Path) -> RawDatasetProvenance:
    """Recompute and persist the SHA-256 digest in the sibling provenance record."""
    provenance_file = provenance_path_for(raw_file)
    if not provenance_file.exists():
        msg = (
            f"Missing provenance record for {raw_file.name}. "
            "Run `iff-provenance init <file>` first."
        )
        raise FileNotFoundError(msg)

    payload = json.loads(provenance_file.read_text(encoding="utf-8"))
    payload["sha256"] = sha256_file(raw_file)
    provenance_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return RawDatasetProvenance.model_validate(payload)


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
