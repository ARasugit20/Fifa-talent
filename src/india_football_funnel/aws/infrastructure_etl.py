"""Manifest-triggered AWS infrastructure ETL orchestration."""

from __future__ import annotations

import hashlib
import json
import logging
import tempfile
from pathlib import Path

from india_football_funnel.aws.s3_client import S3Client
from india_football_funnel.config import (
    DATASET_READY_MANIFEST_KEY,
    DATASET_READY_VERSION,
    REQUIRED_RAW_FILES,
)
from india_football_funnel.data.infrastructure_pipeline import (
    PROCESSED_INFRASTRUCTURE_FILENAME,
    build_public_sports_infrastructure_frame,
)
from india_football_funnel.data.reproduce_artifacts import write_reproduce_artifacts
from india_football_funnel.models import DatasetReadyManifest, InfrastructureEtlResult

logger = logging.getLogger(__name__)

TAG_SOURCE_FINGERPRINT = "iff:source-fingerprint"
TAG_PROCESSING_STATUS = "iff:processing-status"
TAG_MANIFEST_OUTPUT_KEY = "iff:manifest-output-key"
STATUS_PROCESSED = "processed"
STATUS_SKIPPED = "skipped-duplicate"


def expected_object_keys(raw_prefix: str = "raw") -> list[str]:
    """Return the eight required S3 object keys for infrastructure ETL."""
    keys: list[str] = []
    for relative_path in sorted(REQUIRED_RAW_FILES):
        csv_key = f"{raw_prefix}/{relative_path}"
        keys.append(csv_key)
        keys.append(f"{csv_key}.provenance.json")
    return keys


def relative_path_from_object_key(object_key: str, raw_prefix: str = "raw") -> str:
    """Map an S3 object key back to a local raw relative path."""
    prefix = f"{raw_prefix}/"
    if not object_key.startswith(prefix):
        msg = f"Object key {object_key} is outside the expected {raw_prefix}/ prefix."
        raise ValueError(msg)
    return object_key.removeprefix(prefix)


def build_default_dataset_ready_manifest(raw_prefix: str = "raw") -> DatasetReadyManifest:
    """Build the canonical ready manifest for the configured raw inputs."""
    return DatasetReadyManifest(
        dataset_version=DATASET_READY_VERSION,
        object_keys=expected_object_keys(raw_prefix),
    )


def validate_dataset_ready_manifest(manifest: DatasetReadyManifest) -> None:
    """Ensure the ready manifest declares the exact required object set."""
    if manifest.dataset_version != DATASET_READY_VERSION:
        msg = (
            f"Unsupported dataset_version {manifest.dataset_version!r}. "
            f"Expected {DATASET_READY_VERSION!r}."
        )
        raise ValueError(msg)
    expected = set(expected_object_keys())
    actual = set(manifest.object_keys)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        msg = "dataset-ready.json object_keys mismatch. " f"missing={missing} extra={extra}"
        raise ValueError(msg)


def composite_source_fingerprint(source_hashes: dict[str, str]) -> str:
    """Build a deterministic fingerprint from validated provenance SHA-256 values."""
    payload = json.dumps(sorted(source_hashes.items()), separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_dataset_ready_manifest(s3: S3Client, manifest_key: str) -> DatasetReadyManifest:
    """Download and validate the dataset-ready manifest from S3."""
    payload = json.loads(s3.get_object_text(manifest_key))
    manifest = DatasetReadyManifest.model_validate(payload)
    validate_dataset_ready_manifest(manifest)
    return manifest


def sync_manifest_objects_to_local(
    s3: S3Client,
    manifest: DatasetReadyManifest,
    raw_root: Path,
) -> None:
    """Download manifest-listed objects into a local raw tree."""
    for object_key in manifest.object_keys:
        relative_path = relative_path_from_object_key(object_key)
        destination = raw_root / relative_path
        s3.download_file(object_key, destination)


def should_skip_duplicate_run(s3: S3Client, processed_key: str, fingerprint: str) -> bool:
    """Return True when processed output already exists for the same fingerprint."""
    if not s3.object_exists(processed_key):
        return False
    tags = s3.get_object_tags(processed_key)
    return tags.get(TAG_SOURCE_FINGERPRINT) == fingerprint


def upload_reproduce_artifacts(s3: S3Client, artifacts: dict[str, Path]) -> dict[str, str]:
    """Upload local reproduction artifacts to their canonical S3 keys."""
    uploaded: dict[str, str] = {}
    key_map = {
        "processed": s3.processed_infrastructure_key(),
        "csv_export": s3.processed_key("infrastructure_by_state.csv"),
        "manifest": s3.results_artifact_key("run_manifest.json"),
        "quality": s3.results_artifact_key("data_quality_report.json"),
        "reconciliation": s3.results_artifact_key("state_reconciliation_report.csv"),
        "summaries": s3.results_artifact_key("analysis/infrastructure_summaries.json"),
    }
    for artifact_name, local_path in artifacts.items():
        s3_key = key_map[artifact_name]
        s3.upload_file(local_path, s3_key)
        uploaded[artifact_name] = s3_key
    return uploaded


def run_infrastructure_etl_from_manifest(
    s3: S3Client,
    manifest_key: str,
) -> InfrastructureEtlResult:
    """Process a dataset-ready manifest and publish infrastructure artifacts to S3."""
    if manifest_key != DATASET_READY_MANIFEST_KEY:
        return InfrastructureEtlResult(
            status="ignored",
            message=f"Ignoring non-manifest key: {manifest_key}",
        )

    manifest = load_dataset_ready_manifest(s3, manifest_key)
    for object_key in manifest.object_keys:
        if not s3.object_exists(object_key):
            msg = f"Required raw object missing in S3: {object_key}"
            raise FileNotFoundError(msg)

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_root = Path(tmpdir) / "raw"
        processed_dir = Path(tmpdir) / "processed"
        results_dir = Path(tmpdir) / "results"
        sync_manifest_objects_to_local(s3, manifest, raw_root)

        frame, report, source_hashes = build_public_sports_infrastructure_frame(raw_root)
        fingerprint = composite_source_fingerprint(source_hashes)
        processed_key = s3.processed_infrastructure_key()

        if should_skip_duplicate_run(s3, processed_key, fingerprint):
            s3.put_object_tags(
                manifest_key,
                {
                    TAG_PROCESSING_STATUS: STATUS_SKIPPED,
                    TAG_SOURCE_FINGERPRINT: fingerprint,
                    TAG_MANIFEST_OUTPUT_KEY: s3.results_artifact_key("run_manifest.json"),
                },
            )
            logger.info("Skipping duplicate infrastructure ETL for fingerprint %s", fingerprint)
            return InfrastructureEtlResult(
                status="skipped_duplicate",
                manifest_key=manifest_key,
                source_fingerprint=fingerprint,
                processed_key=processed_key,
                message="Processed output already exists for this source fingerprint.",
            )

        artifacts = write_reproduce_artifacts(
            frame,
            report,
            source_hashes,
            processed_dir,
            results_dir,
        )
        uploaded = upload_reproduce_artifacts(s3, artifacts)
        s3.upload_file(
            artifacts["processed"],
            processed_key,
            tags={
                TAG_SOURCE_FINGERPRINT: fingerprint,
                TAG_PROCESSING_STATUS: STATUS_PROCESSED,
                TAG_MANIFEST_OUTPUT_KEY: uploaded["manifest"],
            },
        )
        s3.put_object_tags(
            manifest_key,
            {
                TAG_PROCESSING_STATUS: STATUS_PROCESSED,
                TAG_SOURCE_FINGERPRINT: fingerprint,
                TAG_MANIFEST_OUTPUT_KEY: uploaded["manifest"],
            },
        )

        return InfrastructureEtlResult(
            status="processed",
            manifest_key=manifest_key,
            source_fingerprint=fingerprint,
            processed_key=processed_key,
            manifest_output_key=uploaded["manifest"],
            row_count=len(frame),
            message=f"Published {PROCESSED_INFRASTRUCTURE_FILENAME} and reproduction artifacts.",
        )
