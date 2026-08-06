"""Moto-backed integration tests for manifest-triggered AWS infrastructure ETL."""

from __future__ import annotations

import io
import json
from pathlib import Path

import boto3
import pandas as pd
import pytest
from moto import mock_aws
from tests.conftest import raw_fixture_root

from india_football_funnel.aws.infrastructure_etl import (
    build_default_dataset_ready_manifest,
    composite_source_fingerprint,
    run_infrastructure_etl_from_manifest,
)
from india_football_funnel.aws.lambda_handlers import etl_handler
from india_football_funnel.aws.s3_client import S3Client
from india_football_funnel.config import DATASET_READY_MANIFEST_KEY, Settings
from india_football_funnel.data.infrastructure_pipeline import (
    build_public_sports_infrastructure_frame,
)
from india_football_funnel.data.schema import PublicSportsInfrastructureSchema


def _create_bucket(client: boto3.client, bucket: str, region: str) -> None:
    if region == "us-east-1":
        client.create_bucket(Bucket=bucket)
    else:
        client.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": region},
        )


def _upload_fixture_tree(client: boto3.client, bucket: str, raw_root: Path) -> None:
    for path in raw_root.rglob("*"):
        if path.is_file():
            relative = path.relative_to(raw_root).as_posix()
            client.upload_file(str(path), bucket, f"raw/{relative}")


def _s3_event(bucket: str, key: str) -> dict[str, object]:
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": bucket},
                    "object": {"key": key},
                }
            }
        ]
    }


@pytest.mark.integration
@mock_aws
def test_aws_infrastructure_etl_publishes_artifacts_and_skips_duplicate() -> None:
    bucket = "iff-test-bucket"
    region = "ap-south-1"
    boto_client = boto3.client("s3", region_name=region)
    _create_bucket(boto_client, bucket, region)
    _upload_fixture_tree(boto_client, bucket, raw_fixture_root())

    manifest = build_default_dataset_ready_manifest()
    boto_client.put_object(
        Bucket=bucket,
        Key=DATASET_READY_MANIFEST_KEY,
        Body=manifest.model_dump_json().encode("utf-8"),
        ContentType="application/json",
    )

    settings = Settings(
        aws_region=region,
        s3_bucket_name=bucket,
        local_mode=False,
    )
    s3 = S3Client(settings, client=boto_client)

    _, _, local_hashes = build_public_sports_infrastructure_frame(raw_fixture_root())
    expected_fingerprint = composite_source_fingerprint(local_hashes)
    local_frame, _, _ = build_public_sports_infrastructure_frame(raw_fixture_root())
    expected_row_count = len(local_frame)

    result = run_infrastructure_etl_from_manifest(s3, DATASET_READY_MANIFEST_KEY)
    assert result.status == "processed"
    assert result.source_fingerprint == expected_fingerprint
    assert result.row_count == expected_row_count

    expected_keys = {
        "processed/public_sports_infrastructure.parquet",
        "processed/infrastructure_by_state.csv",
        "results/run_manifest.json",
        "results/data_quality_report.json",
        "results/state_reconciliation_report.csv",
        "results/analysis/infrastructure_summaries.json",
    }
    listed_keys = {
        item["Key"] for item in boto_client.list_objects_v2(Bucket=bucket).get("Contents", [])
    }
    assert expected_keys.issubset(listed_keys)

    parquet_obj = boto_client.get_object(
        Bucket=bucket,
        Key="processed/public_sports_infrastructure.parquet",
    )
    frame = pd.read_parquet(io.BytesIO(parquet_obj["Body"].read()))
    PublicSportsInfrastructureSchema.validate(frame)

    manifest_obj = boto_client.get_object(Bucket=bucket, Key="results/run_manifest.json")
    run_manifest = json.loads(manifest_obj["Body"].read().decode("utf-8"))
    assert run_manifest["source_hashes"] == local_hashes

    duplicate = run_infrastructure_etl_from_manifest(s3, DATASET_READY_MANIFEST_KEY)
    assert duplicate.status == "skipped_duplicate"
    assert duplicate.source_fingerprint == expected_fingerprint


@pytest.mark.integration
@mock_aws
def test_aws_infrastructure_etl_handler_validation_error_without_partial_outputs() -> None:
    bucket = "iff-test-bucket-missing"
    region = "ap-south-1"
    boto_client = boto3.client("s3", region_name=region)
    _create_bucket(boto_client, bucket, region)

    manifest = build_default_dataset_ready_manifest()
    boto_client.put_object(
        Bucket=bucket,
        Key=DATASET_READY_MANIFEST_KEY,
        Body=manifest.model_dump_json().encode("utf-8"),
    )

    settings = Settings(
        aws_region=region,
        s3_bucket_name=bucket,
        local_mode=False,
    )

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            "india_football_funnel.aws.lambda_handlers.get_settings",
            lambda: settings,
        )
        patch.setattr(
            "india_football_funnel.aws.lambda_handlers.S3Client",
            lambda s, client=None: S3Client(s, client=boto_client),
        )
        response = etl_handler(_s3_event(bucket, DATASET_READY_MANIFEST_KEY), None)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["status"] == "validation_error"
    assert "missing" in body["message"].lower()

    objects = boto_client.list_objects_v2(Bucket=bucket).get("Contents", [])
    keys = {item["Key"] for item in objects}
    assert "processed/public_sports_infrastructure.parquet" not in keys


@pytest.mark.integration
@mock_aws
def test_etl_handler_ignores_non_manifest_uploads() -> None:
    bucket = "iff-test-bucket-ignore"
    region = "ap-south-1"
    boto_client = boto3.client("s3", region_name=region)
    _create_bucket(boto_client, bucket, region)

    settings = Settings(
        aws_region=region,
        s3_bucket_name=bucket,
        local_mode=False,
    )

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            "india_football_funnel.aws.lambda_handlers.get_settings",
            lambda: settings,
        )
        patch.setattr(
            "india_football_funnel.aws.lambda_handlers.S3Client",
            lambda s, client=None: S3Client(s, client=boto_client),
        )
        response = etl_handler(_s3_event(bucket, "raw/mdsd/state_wise_progress.csv"), None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "ignored"
