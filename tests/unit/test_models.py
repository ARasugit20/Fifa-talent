"""Regression checks for domain model cleanup."""

from __future__ import annotations

import importlib
import pkgutil

import india_football_funnel


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
