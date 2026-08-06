"""Unit tests for manifest-triggered AWS infrastructure ETL."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from india_football_funnel.aws.infrastructure_etl import (
    build_default_dataset_ready_manifest,
    composite_source_fingerprint,
    expected_object_keys,
    load_dataset_ready_manifest,
    relative_path_from_object_key,
    run_infrastructure_etl_from_manifest,
    validate_dataset_ready_manifest,
)
from india_football_funnel.config import DATASET_READY_MANIFEST_KEY, DATASET_READY_VERSION
from india_football_funnel.models import DatasetReadyManifest


def test_expected_object_keys_include_csv_and_provenance_pairs() -> None:
    keys = expected_object_keys()
    assert len(keys) == 8
    assert all(key.startswith("raw/") for key in keys)
    assert "raw/mdsd/state_wise_progress.csv" in keys
    assert "raw/mdsd/state_wise_progress.csv.provenance.json" in keys


def test_validate_dataset_ready_manifest_rejects_version_mismatch() -> None:
    manifest = DatasetReadyManifest(
        dataset_version="v0",
        object_keys=expected_object_keys(),
    )
    with pytest.raises(ValueError, match="Unsupported dataset_version"):
        validate_dataset_ready_manifest(manifest)


def test_validate_dataset_ready_manifest_rejects_key_mismatch() -> None:
    manifest = DatasetReadyManifest(
        dataset_version=DATASET_READY_VERSION,
        object_keys=["raw/mdsd/state_wise_progress.csv"],
    )
    with pytest.raises(ValueError, match="object_keys mismatch"):
        validate_dataset_ready_manifest(manifest)


def test_relative_path_from_object_key() -> None:
    assert relative_path_from_object_key("raw/census/state_population_2011.csv") == (
        "census/state_population_2011.csv"
    )


def test_relative_path_from_object_key_rejects_outside_raw_prefix() -> None:
    with pytest.raises(ValueError, match="outside the expected raw/ prefix"):
        relative_path_from_object_key("processed/public_sports_infrastructure.parquet")


def test_composite_source_fingerprint_is_deterministic() -> None:
    hashes = {
        "census/state_population_2011.csv": "aaa",
        "mdsd/state_wise_progress.csv": "bbb",
    }
    first = composite_source_fingerprint(hashes)
    second = composite_source_fingerprint(dict(reversed(list(hashes.items()))))
    assert first == second
    assert len(first) == 64


def test_build_default_dataset_ready_manifest() -> None:
    manifest = build_default_dataset_ready_manifest()
    validate_dataset_ready_manifest(manifest)
    assert manifest.dataset_version == DATASET_READY_VERSION


def test_load_dataset_ready_manifest_from_s3() -> None:
    manifest = build_default_dataset_ready_manifest()
    mock_s3 = MagicMock()
    mock_s3.get_object_text.return_value = manifest.model_dump_json()
    loaded = load_dataset_ready_manifest(mock_s3, DATASET_READY_MANIFEST_KEY)
    assert loaded.object_keys == manifest.object_keys


def test_run_infrastructure_etl_ignores_non_manifest_keys() -> None:
    mock_s3 = MagicMock()
    result = run_infrastructure_etl_from_manifest(mock_s3, "raw/mdsd/state_wise_progress.csv")
    assert result.status == "ignored"
    mock_s3.get_object_text.assert_not_called()


def test_run_infrastructure_etl_raises_when_required_object_missing() -> None:
    manifest = build_default_dataset_ready_manifest()
    mock_s3 = MagicMock()
    mock_s3.get_object_text.return_value = manifest.model_dump_json()
    mock_s3.object_exists.return_value = False

    with pytest.raises(FileNotFoundError, match="Required raw object missing"):
        run_infrastructure_etl_from_manifest(mock_s3, DATASET_READY_MANIFEST_KEY)


def test_run_infrastructure_etl_skips_duplicate_fingerprint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.conftest import raw_fixture_root

    manifest = build_default_dataset_ready_manifest()
    mock_s3 = MagicMock()
    mock_s3.get_object_text.return_value = manifest.model_dump_json()
    mock_s3.object_exists.return_value = True
    mock_s3.processed_infrastructure_key.return_value = (
        "processed/public_sports_infrastructure.parquet"
    )
    mock_s3.results_artifact_key.side_effect = lambda path: f"results/{path}"

    fingerprint = "deadbeef" * 8

    def fake_fingerprint(_: dict[str, str]) -> str:
        return fingerprint

    monkeypatch.setattr(
        "india_football_funnel.aws.infrastructure_etl.composite_source_fingerprint",
        fake_fingerprint,
    )

    def fake_download(key: str, local_path: Path) -> Path:
        source = raw_fixture_root() / key.removeprefix("raw/")
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(source.read_bytes())
        return local_path

    mock_s3.download_file.side_effect = fake_download
    mock_s3.get_object_tags.return_value = {"iff:source-fingerprint": fingerprint}

    result = run_infrastructure_etl_from_manifest(mock_s3, DATASET_READY_MANIFEST_KEY)
    assert result.status == "skipped_duplicate"
    assert result.source_fingerprint == fingerprint
    mock_s3.upload_file.assert_not_called()
