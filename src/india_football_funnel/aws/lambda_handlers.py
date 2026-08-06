"""AWS Lambda entry points."""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Any

from india_football_funnel.aws.infrastructure_etl import run_infrastructure_etl_from_manifest
from india_football_funnel.aws.s3_client import S3Client
from india_football_funnel.config import get_settings
from india_football_funnel.simulation.run_simulation import run_simulation, write_simulation_outputs
from india_football_funnel.simulation.scenarios import get_scenario_by_name

logger = logging.getLogger(__name__)


def etl_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler: process dataset-ready manifest and publish infrastructure outputs."""
    _ = context
    settings = get_settings()
    s3 = S3Client(settings)

    bucket, key = s3.parse_s3_event(event)
    logger.info("ETL triggered for s3://%s/%s", bucket, key)

    try:
        result = run_infrastructure_etl_from_manifest(s3, key)
    except (FileNotFoundError, ValueError) as exc:
        logger.warning("Infrastructure ETL validation failed: %s", exc)
        return {
            "statusCode": 400,
            "body": json.dumps({"status": "validation_error", "message": str(exc)}),
        }

    return {
        "statusCode": 200,
        "body": result.model_dump_json(),
    }


def simulation_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler: run one Monte Carlo scenario and write results to S3."""
    _ = context
    settings = get_settings()
    s3 = S3Client(settings)

    scenario_name = str(event.get("scenario_name", "baseline"))
    n_runs = int(event.get("n_runs", 100))
    years = int(event.get("years", 10))
    rng_seed = int(event.get("rng_seed", 42))

    logger.info(
        "Simulation triggered: scenario=%s runs=%d years=%d",
        scenario_name,
        n_runs,
        years,
    )

    params = get_scenario_by_name(scenario_name, rng_seed=rng_seed)
    params = params.model_copy(update={"n_runs": n_runs, "years": years})

    result = run_simulation(params)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        parquet_path, json_path = write_simulation_outputs(result, output_dir)

        parquet_key = s3.results_key(scenario_name, parquet_path.name)
        json_key = s3.results_key(scenario_name, json_path.name)
        s3.upload_file(parquet_path, parquet_key)
        s3.upload_file(json_path, json_key)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "scenario_name": scenario_name,
                "parquet_key": parquet_key,
                "json_key": json_key,
                "final_medals_mean": result.final_medals_mean,
            }
        ),
    }
