"""AWS Lambda entry points."""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Any

from india_football_funnel.aws.s3_client import S3Client
from india_football_funnel.config import get_settings
from india_football_funnel.data.loader import process_raw_file
from india_football_funnel.simulation.run_simulation import run_simulation, write_simulation_outputs
from india_football_funnel.simulation.scenarios import get_scenario_by_name

logger = logging.getLogger(__name__)


def etl_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler: validate raw S3 upload and write processed parquet."""
    _ = context
    settings = get_settings()
    s3 = S3Client(settings)

    bucket, key = s3.parse_s3_event(event)
    logger.info("ETL triggered for s3://%s/%s", bucket, key)

    with tempfile.TemporaryDirectory() as tmpdir:
        local_raw = Path(tmpdir) / Path(key).name
        s3.download_file(key, local_raw)
        processed_local = Path(tmpdir) / f"{local_raw.stem}.parquet"
        process_raw_file(local_raw, processed_local)

        processed_key = s3.processed_key(processed_local.name)
        s3.upload_file(processed_local, processed_key)

    return {
        "statusCode": 200,
        "body": json.dumps({"processed_key": processed_key}),
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
