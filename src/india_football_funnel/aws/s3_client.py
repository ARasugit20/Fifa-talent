"""Thin S3 client wrapper."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import boto3

from india_football_funnel.config import PROCESSED_PREFIX, RAW_PREFIX, RESULTS_PREFIX, Settings

logger = logging.getLogger(__name__)


class S3Client:
    """Wrapper around boto3 S3 operations."""

    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        self.settings = settings
        self._client: Any = client or boto3.client("s3", region_name=settings.aws_region)

    @property
    def bucket(self) -> str:
        return self.settings.resolved_bucket_name

    def upload_file(self, local_path: Path, key: str) -> str:
        """Upload a local file to S3."""
        logger.info("Uploading %s to s3://%s/%s", local_path, self.bucket, key)
        self._client.upload_file(str(local_path), self.bucket, key)
        return f"s3://{self.bucket}/{key}"

    def download_file(self, key: str, local_path: Path) -> Path:
        """Download an S3 object to a local path."""
        local_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading s3://%s/%s to %s", self.bucket, key, local_path)
        self._client.download_file(self.bucket, key, str(local_path))
        return local_path

    def put_bytes(
        self,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload raw bytes to S3."""
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
        return f"s3://{self.bucket}/{key}"

    def list_objects(self, prefix: str) -> list[str]:
        """List object keys under a prefix."""
        paginator = self._client.get_paginator("list_objects_v2")
        keys: list[str] = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(str(obj["Key"]))
        return keys

    def raw_key(self, source: str, date_str: str, filename: str) -> str:
        return f"{RAW_PREFIX}/{source}/{date_str}/{filename}"

    def processed_key(self, filename: str) -> str:
        return f"{PROCESSED_PREFIX}/{filename}"

    def results_key(self, scenario: str, filename: str) -> str:
        return f"{RESULTS_PREFIX}/{scenario}/{filename}"

    def parse_s3_event(self, event: dict[str, Any]) -> tuple[str, str]:
        """Extract bucket and key from an S3 event notification."""
        record = event["Records"][0]
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        return bucket, key
