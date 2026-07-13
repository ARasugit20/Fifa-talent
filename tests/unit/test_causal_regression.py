"""Unit tests for causal regression."""

from __future__ import annotations

import pytest
from tests.conftest import load_fixture_csv

from india_football_funnel.analysis.causal_regression import (
    fit_retention_regression,
    run_default_regressions,
)


def test_fit_retention_regression() -> None:
    frame = load_fixture_csv("sample_funnel.csv")
    result = fit_retention_regression(frame, predictor="log_cohort")
    assert result.n_observations >= 10
    assert 0.0 <= result.p_value <= 1.0
    assert result.confidence_interval_lower <= result.coefficient
    assert result.coefficient <= result.confidence_interval_upper


def test_run_default_regressions() -> None:
    frame = load_fixture_csv("sample_funnel.csv")
    results = run_default_regressions(frame)
    assert len(results) >= 1


def test_insufficient_observations_raises() -> None:
    frame = load_fixture_csv("sample_funnel.csv").head(3)
    with pytest.raises(ValueError, match="Insufficient observations"):
        fit_retention_regression(frame)
