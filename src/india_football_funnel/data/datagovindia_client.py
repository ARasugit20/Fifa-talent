"""data.gov.in client wrapper for Khelo India public resources."""

from __future__ import annotations

import importlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Protocol, cast

from india_football_funnel.aws.s3_client import S3Client
from india_football_funnel.config import (
    KHELO_INDIA_BUDGET_RESOURCE,
    KHELO_INDIA_MEDAL_TALLY_RESOURCE,
    KHELO_INDIA_RAW_PREFIX,
)

logger = logging.getLogger(__name__)


class DataGovClientProtocol(Protocol):
    """Small protocol for the datagovindia package client."""

    def get_data(self, resource_id: str, **kwargs: Any) -> Any: ...

    def search(self, query: str, **kwargs: Any) -> Any: ...


def get_datagovindia_api_key() -> str:
    """Read the free data.gov.in API key from the environment."""
    api_key = os.getenv("DATAGOVINDIA_API_KEY", "")
    if not api_key:
        msg = "Set DATAGOVINDIA_API_KEY before calling data.gov.in resources"
        raise RuntimeError(msg)
    return api_key


def create_datagovindia_client(api_key: str | None = None) -> DataGovClientProtocol:
    """Instantiate the optional datagovindia package client."""
    module = importlib.import_module("datagovindia")
    key = api_key or get_datagovindia_api_key()
    client_cls = getattr(module, "DataGovIndia", None) or getattr(module, "Client", None)
    if client_cls is None:
        msg = "datagovindia package does not expose a supported client class"
        raise RuntimeError(msg)
    return cast(DataGovClientProtocol, client_cls(api_key=key))


def fetch_resource(
    client: DataGovClientProtocol,
    resource_id: str,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Fetch a resource and normalize common response shapes."""
    logger.info("Fetching data.gov.in resource %s", resource_id)
    payload = client.get_data(resource_id, **(filters or {}))
    if isinstance(payload, dict):
        records = payload.get("records", payload.get("data", []))
    else:
        records = payload
    if not isinstance(records, list):
        msg = f"Unexpected data.gov.in payload for {resource_id}"
        raise ValueError(msg)
    return [record for record in records if isinstance(record, dict)]


def search_sports_resources(
    client: DataGovClientProtocol,
    query: str = "Khelo India Department of Sports",
) -> list[dict[str, Any]]:
    """Search sports-sector data.gov.in resources."""
    payload = client.search(query)
    if isinstance(payload, dict):
        records = payload.get("records", payload.get("data", []))
    else:
        records = payload
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def cache_raw_response_to_s3(
    s3_client: S3Client,
    resource_name: str,
    records: list[dict[str, Any]],
) -> str:
    """Cache raw API response under raw/khelo_india before processing."""
    key = f"{KHELO_INDIA_RAW_PREFIX}/{resource_name}.json"
    body = json.dumps({"records": records}, indent=2, default=str).encode("utf-8")
    return s3_client.put_bytes(key, body, content_type="application/json")


def cache_raw_response_locally(
    output_dir: Path,
    resource_name: str,
    records: list[dict[str, Any]],
) -> Path:
    """Local equivalent of the raw S3 cache for reproduce/tests."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{resource_name}.json"
    path.write_text(json.dumps({"records": records}, indent=2, default=str), encoding="utf-8")
    return path


def fetch_khelo_india_resources(
    client: DataGovClientProtocol,
) -> dict[str, list[dict[str, Any]]]:
    """Fetch core Khelo India public resources."""
    return {
        "medal_tally": fetch_resource(client, KHELO_INDIA_MEDAL_TALLY_RESOURCE),
        "budget_allocation": fetch_resource(client, KHELO_INDIA_BUDGET_RESOURCE),
        "sports_sector_search": search_sports_resources(client),
    }
