"""Unit tests for S3 client and Lambda handlers."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tests.conftest import fixture_path

from india_football_funnel.aws.lambda_handlers import etl_handler, simulation_handler
from india_football_funnel.aws.s3_client import S3Client
from india_football_funnel.config import Settings


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


def test_s3_parse_event(settings: Settings) -> None:
    s3 = S3Client(settings, client=MagicMock())
    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {"key": "raw/state_registry/2024-06-01/data.csv"},
                }
            }
        ]
    }
    bucket, key = s3.parse_s3_event(event)
    assert bucket == "test-bucket"
    assert key == "raw/state_registry/2024-06-01/data.csv"


def test_s3_client_object_exists_and_tags(settings: Settings) -> None:
    mock_client = MagicMock()
    mock_client.head_object.return_value = {"ETag": '"etag-123"'}
    mock_client.get_object_tagging.return_value = {
        "TagSet": [{"Key": "iff:source-etag", "Value": "etag-123"}]
    }
    s3 = S3Client(settings, client=mock_client)

    assert s3.object_exists("processed/data.parquet") is True
    assert s3.get_object_etag("raw/data.csv") == "etag-123"
    assert s3.get_object_tags("processed/data.parquet") == {"iff:source-etag": "etag-123"}

    s3.put_object_tags("raw/data.csv", {"iff:processing-status": "processed"})
    mock_client.put_object_tagging.assert_called_once()


@patch("india_football_funnel.aws.lambda_handlers.S3Client")
@patch("india_football_funnel.aws.lambda_handlers.process_raw_file")
def test_etl_handler_skips_duplicate_source(
    mock_process: MagicMock,
    mock_s3_cls: MagicMock,
) -> None:
    mock_s3 = MagicMock()
    mock_s3.parse_s3_event.return_value = ("test-bucket", "raw/data.csv")
    mock_s3.processed_key.return_value = "processed/data.parquet"
    mock_s3.object_exists.return_value = True
    mock_s3.get_object_etag.return_value = "etag-123"
    mock_s3.get_object_tags.return_value = {"iff:source-etag": "etag-123"}
    mock_s3_cls.return_value = mock_s3

    response = etl_handler(
        {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "raw/data.csv"},
                    }
                }
            ]
        },
        None,
    )

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["skipped"] is True
    mock_process.assert_not_called()
    mock_s3.put_object_tags.assert_called_once()


@patch("india_football_funnel.aws.lambda_handlers.S3Client")
@patch("india_football_funnel.aws.lambda_handlers.process_raw_file")
def test_etl_handler(
    mock_process: MagicMock,
    mock_s3_cls: MagicMock,
    settings: Settings,
    tmp_path: Path,
) -> None:
    mock_s3 = MagicMock()
    mock_s3.parse_s3_event.return_value = ("test-bucket", "raw/data.csv")
    mock_s3.processed_key.return_value = "processed/data.parquet"
    mock_s3.object_exists.return_value = False
    mock_s3.get_object_etag.return_value = "etag-123"

    def fake_download(key: str, local_path: Path) -> Path:
        import shutil

        shutil.copy(fixture_path("sample_investment_outcomes.csv"), local_path)
        return local_path

    mock_s3.download_file.side_effect = fake_download
    mock_s3_cls.return_value = mock_s3
    mock_process.return_value = tmp_path / "data.parquet"

    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {"key": "raw/data.csv"},
                }
            }
        ]
    }
    response = etl_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["skipped"] is False
    assert "processed_key" in body


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
