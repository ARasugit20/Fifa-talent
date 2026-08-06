"""Regression checks for domain model cleanup."""

from __future__ import annotations

import importlib
import pkgutil

import pytest

import india_football_funnel
from india_football_funnel.config import get_settings
from india_football_funnel.models import DatasetReadyManifest, InfrastructureEtlResult


def test_dataset_ready_manifest_and_etl_result_models() -> None:
    manifest = DatasetReadyManifest(
        dataset_version="v1",
        object_keys=["raw/census/state_population_2011.csv"],
    )
    assert manifest.dataset_version == "v1"

    result = InfrastructureEtlResult(
        status="processed",
        manifest_key="raw/dataset-ready.json",
        row_count=10,
    )
    assert result.status == "processed"
    assert result.message == ""


def test_get_settings_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("IFF_S3_BUCKET", "env-bucket")
    settings = get_settings()
    assert settings.s3_bucket_name == "env-bucket"
    get_settings.cache_clear()


def test_funnel_observation_removed_from_models() -> None:
    models = importlib.import_module("india_football_funnel.models")
    assert not hasattr(models, "FunnelObservation")


def test_no_funnel_observation_imports_in_package() -> None:
    package = india_football_funnel
    for module_info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if module_info.name.startswith("india_football_funnel.tests"):
            continue
        module = importlib.import_module(module_info.name)
        source_path = getattr(module, "__file__", None)
        if source_path is None:
            continue
        with open(source_path, encoding="utf-8") as handle:
            contents = handle.read()
        assert "FunnelObservation" not in contents
