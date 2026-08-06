"""Unit tests for S3 client and Lambda handlers."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from india_football_funnel.aws.lambda_handlers import etl_handler, simulation_handler
from india_football_funnel.aws.s3_client import S3Client
from india_football_funnel.config import DATASET_READY_MANIFEST_KEY, Settings
from india_football_funnel.models import InfrastructureEtlResult


@pytest.fixture
def settings() -> Settings:
    return Settings(
        aws_region="ap-south-1",
        aws_account_id="123456789012",
        s3_bucket_name="test-bucket",
        local_mode=True,
    )


def test_s3_client_upload_download(settings: Settings, tmp_path: Path) -> None:
    mock_client = MagicMock()
    s3 = S3Client(settings, client=mock_client)

    local_file = tmp_path / "test.csv"
    local_file.write_text("a,b\n1,2", encoding="utf-8")

    uri = s3.upload_file(local_file, "raw/test/test.csv")
    assert uri == "s3://test-bucket/raw/test/test.csv"
    mock_client.upload_file.assert_called_once()

    s3.download_file("raw/test/test.csv", tmp_path / "downloaded.csv")
    mock_client.download_file.assert_called_once()


def test_s3_client_get_object_text(settings: Settings) -> None:
    mock_client = MagicMock()
    mock_client.get_object.return_value = {"Body": MagicMock(read=lambda: b'{"ok": true}')}
    s3 = S3Client(settings, client=mock_client)

    assert s3.get_object_text("raw/dataset-ready.json") == '{"ok": true}'


def test_s3_client_list_and_put(settings: Settings) -> None:
    mock_client = MagicMock()
    mock_client.get_paginator.return_value.paginate.return_value = [
        {"Contents": [{"Key": "raw/test.csv"}]}
    ]
    s3 = S3Client(settings, client=mock_client)

    keys = s3.list_objects("raw/")
    assert keys == ["raw/test.csv"]

    uri = s3.put_bytes("processed/test.parquet", b"data")
    assert uri == "s3://test-bucket/processed/test.parquet"


def test_s3_parse_event_decodes_url_encoded_key(settings: Settings) -> None:
    s3 = S3Client(settings, client=MagicMock())
    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {"key": "raw/dataset-ready.json"},
                }
            }
        ]
    }
    bucket, key = s3.parse_s3_event(event)
    assert bucket == "test-bucket"
    assert key == DATASET_READY_MANIFEST_KEY


def test_s3_client_object_exists_and_tags(settings: Settings) -> None:
    mock_client = MagicMock()
    mock_client.head_object.return_value = {"ETag": '"etag-123"'}
    mock_client.get_object_tagging.return_value = {
        "TagSet": [{"Key": "iff:source-fingerprint", "Value": "abc123"}]
    }
    s3 = S3Client(settings, client=mock_client)

    assert s3.object_exists("processed/data.parquet") is True
    assert s3.get_object_etag("raw/data.csv") == "etag-123"
    assert s3.get_object_tags("processed/data.parquet") == {"iff:source-fingerprint": "abc123"}

    s3.put_object_tags("raw/data.csv", {"iff:processing-status": "processed"})
    mock_client.put_object_tagging.assert_called_once()


def test_s3_client_artifact_key_helpers(settings: Settings) -> None:
    s3 = S3Client(settings, client=MagicMock())
    assert s3.raw_key("mdsd", "2024-06-01", "data.csv") == "raw/mdsd/2024-06-01/data.csv"
    assert s3.processed_infrastructure_key() == "processed/public_sports_infrastructure.parquet"
    assert s3.results_artifact_key("run_manifest.json") == "results/run_manifest.json"
    assert s3.results_key("baseline", "summary.json") == "results/baseline/summary.json"


def test_settings_s3_prefix_properties() -> None:
    settings = Settings(
        aws_account_id="123456789012",
        s3_bucket_name="custom-bucket",
    )
    assert settings.resolved_bucket_name == "custom-bucket"
    assert settings.raw_s3_prefix == "s3://custom-bucket/raw"
    assert settings.processed_s3_prefix == "s3://custom-bucket/processed"
    assert settings.results_s3_prefix == "s3://custom-bucket/results"


def test_s3_client_object_exists_returns_false_for_missing_key(settings: Settings) -> None:
    mock_client = MagicMock()
    mock_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}},
        "HeadObject",
    )
    s3 = S3Client(settings, client=mock_client)
    assert s3.object_exists("raw/missing.csv") is False


def test_s3_client_object_exists_reraises_unexpected_client_error(settings: Settings) -> None:
    mock_client = MagicMock()
    mock_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "403", "Message": "Forbidden"}},
        "HeadObject",
    )
    s3 = S3Client(settings, client=mock_client)
    with pytest.raises(ClientError):
        s3.object_exists("raw/forbidden.csv")


def test_s3_client_upload_with_tags(settings: Settings, tmp_path: Path) -> None:
    mock_client = MagicMock()
    s3 = S3Client(settings, client=mock_client)
    local_file = tmp_path / "processed.parquet"
    local_file.write_bytes(b"parquet")

    s3.upload_file(
        local_file,
        "processed/public_sports_infrastructure.parquet",
        tags={"iff:source-fingerprint": "abc123"},
    )
    mock_client.upload_file.assert_called_once()
    assert "Tagging" in mock_client.upload_file.call_args.kwargs["ExtraArgs"]


@patch("india_football_funnel.aws.lambda_handlers.run_infrastructure_etl_from_manifest")
@patch("india_football_funnel.aws.lambda_handlers.S3Client")
def test_etl_handler_processed_manifest(
    mock_s3_cls: MagicMock,
    mock_run: MagicMock,
) -> None:
    mock_s3 = MagicMock()
    mock_s3.parse_s3_event.return_value = ("test-bucket", DATASET_READY_MANIFEST_KEY)
    mock_s3_cls.return_value = mock_s3
    mock_run.return_value = InfrastructureEtlResult(
        status="processed",
        manifest_key=DATASET_READY_MANIFEST_KEY,
        source_fingerprint="abc",
        processed_key="processed/public_sports_infrastructure.parquet",
        row_count=36,
    )

    response = etl_handler(
        {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": DATASET_READY_MANIFEST_KEY},
                    }
                }
            ]
        },
        None,
    )

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "processed"
    mock_run.assert_called_once_with(mock_s3, DATASET_READY_MANIFEST_KEY)


@patch("india_football_funnel.aws.lambda_handlers.run_infrastructure_etl_from_manifest")
@patch("india_football_funnel.aws.lambda_handlers.S3Client")
def test_etl_handler_skips_duplicate_manifest(
    mock_s3_cls: MagicMock,
    mock_run: MagicMock,
) -> None:
    mock_s3 = MagicMock()
    mock_s3.parse_s3_event.return_value = ("test-bucket", DATASET_READY_MANIFEST_KEY)
    mock_s3_cls.return_value = mock_s3
    mock_run.return_value = InfrastructureEtlResult(
        status="skipped_duplicate",
        manifest_key=DATASET_READY_MANIFEST_KEY,
        source_fingerprint="abc",
        processed_key="processed/public_sports_infrastructure.parquet",
    )

    response = etl_handler(
        {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": DATASET_READY_MANIFEST_KEY},
                    }
                }
            ]
        },
        None,
    )

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "skipped_duplicate"


@patch("india_football_funnel.aws.lambda_handlers.run_infrastructure_etl_from_manifest")
@patch("india_football_funnel.aws.lambda_handlers.S3Client")
def test_etl_handler_returns_validation_error(
    mock_s3_cls: MagicMock,
    mock_run: MagicMock,
) -> None:
    mock_s3 = MagicMock()
    mock_s3.parse_s3_event.return_value = ("test-bucket", DATASET_READY_MANIFEST_KEY)
    mock_s3_cls.return_value = mock_s3
    mock_run.side_effect = FileNotFoundError("Required raw object missing in S3: raw/foo.csv")

    response = etl_handler(
        {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": DATASET_READY_MANIFEST_KEY},
                    }
                }
            ]
        },
        None,
    )

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["status"] == "validation_error"


@patch("india_football_funnel.aws.lambda_handlers.S3Client")
def test_simulation_handler(mock_s3_cls: MagicMock) -> None:
    mock_s3 = MagicMock()
    mock_s3.results_key.side_effect = lambda scenario, name: f"results/{scenario}/{name}"
    mock_s3_cls.return_value = mock_s3

    event = {
        "scenario_name": "baseline",
        "n_runs": 10,
        "years": 3,
        "rng_seed": 42,
    }
    response = simulation_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["scenario_name"] == "baseline"
    assert body["final_medals_mean"] > 0
