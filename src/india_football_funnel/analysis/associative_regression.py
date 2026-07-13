"""Exploratory associative regression for public-data outcomes.

This module does NOT support causal inference: there is no control group, no
identification strategy, and sample sizes are small. Treat outputs as descriptive
associations only, not evidence of causal effects.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import statsmodels.api as sm

from india_football_funnel.config import REGRESSION_CONFIDENCE_LEVEL, REGRESSION_MIN_OBSERVATIONS
from india_football_funnel.models import RegressionResult

logger = logging.getLogger(__name__)


def prepare_regression_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Build regression-ready features from processed public data.

    Facility density is used only when verified centre data is present; otherwise
    the covariate is dropped and surfaced in RegressionResult.
    """
    working = frame.copy()
    working["log_youth_population"] = np.log1p(working["youth_population_10_17"])
    working["budget_allocation_per_capita"] = working["budget_allocation_inr"] / working[
        "youth_population_10_17"
    ].replace(0, pd.NA)
    if "participation_rate" not in working.columns:
        working["participation_rate"] = working["participation_count"] / working[
            "youth_population_10_17"
        ].replace(0, pd.NA)
    if "facility_density" not in working.columns and "khelo_india_centres" in working.columns:
        working["facility_density"] = working["khelo_india_centres"] / working[
            "youth_population_10_17"
        ].replace(0, pd.NA)
    return working.dropna(subset=["medals", "participation_rate", "log_youth_population"])


def fit_outcome_regression(
    frame: pd.DataFrame,
    outcome: str = "medals",
) -> RegressionResult:
    """Fit exploratory OLS associations between outcomes and covariates."""
    data = prepare_regression_frame(frame)
    if len(data) < REGRESSION_MIN_OBSERVATIONS:
        msg = f"Insufficient observations: {len(data)} < {REGRESSION_MIN_OBSERVATIONS}"
        raise ValueError(msg)

    candidate_covariates = [
        "facility_density",
        "budget_allocation_per_capita",
        "log_youth_population",
        "participation_rate",
    ]
    covariates_used: list[str] = []
    covariates_dropped: list[str] = []
    for covariate in candidate_covariates:
        if covariate in data.columns and data[covariate].notna().any():
            covariates_used.append(covariate)
        else:
            covariates_dropped.append(covariate)

    base_covariates = list(covariates_used)
    state_dummies = pd.get_dummies(data["state"], prefix="state", drop_first=True, dtype=float)
    if len(data) <= len(base_covariates) + len(state_dummies.columns) + 1:
        covariates_dropped.append("state_fixed_effects_insufficient_n")
        state_dummies = pd.DataFrame(index=data.index)
    covariates_used.extend(state_dummies.columns.tolist())

    y = data[outcome].astype(float)
    x = pd.concat([data[base_covariates].astype(float), state_dummies], axis=1)
    x = sm.add_constant(x)
    model = sm.OLS(y, x).fit()

    alpha = 1.0 - REGRESSION_CONFIDENCE_LEVEL
    conf_int = model.conf_int(alpha=alpha)
    primary = "budget_allocation_per_capita"
    coef = float(model.params[primary])
    lower = float(conf_int.loc[primary, 0])
    upper = float(conf_int.loc[primary, 1])

    logger.info(
        "Associative regression complete: outcome=%s primary=%s coef=%.4f n=%d r2=%.3f dropped=%s",
        outcome,
        primary,
        coef,
        len(data),
        float(model.rsquared),
        covariates_dropped,
    )

    return RegressionResult(
        predictor=primary,
        coefficient=coef,
        std_error=float(model.bse[primary]),
        p_value=float(model.pvalues[primary]),
        confidence_interval_lower=lower,
        confidence_interval_upper=upper,
        n_observations=len(data),
        r_squared=float(model.rsquared),
        covariates_used=covariates_used,
        covariates_dropped=covariates_dropped,
    )


def fit_retention_regression(
    frame: pd.DataFrame,
    predictor: str = "budget_allocation_per_capita",
) -> RegressionResult:
    """Backward-compatible wrapper for tests/callers; use fit_outcome_regression."""
    _ = predictor
    return fit_outcome_regression(frame, outcome="medals")


def run_default_regressions(frame: pd.DataFrame) -> list[RegressionResult]:
    """Run exploratory outcome and participation regressions for public-data inputs."""
    outcomes = ["medals", "participation_rate"]
    results: list[RegressionResult] = []
    for outcome in outcomes:
        try:
            results.append(fit_outcome_regression(frame, outcome=outcome))
        except ValueError as exc:
            logger.warning("Skipping outcome %s: %s", outcome, exc)
    return results
