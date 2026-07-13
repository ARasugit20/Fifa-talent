# AWS Deploy and Destroy Guide

## Prerequisites

- AWS account with programmatic access
- Terraform >= 1.5
- Docker (for building Lambda container image)
- Environment variables:

```bash
export AWS_ACCOUNT_ID=123456789012
export AWS_REGION=ap-south-1
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

## Deploy (creates billable resources)

```bash
make setup          # local env only, no AWS cost
make docker-build   # build Lambda container locally
make plan           # preview Terraform changes
make deploy         # apply infrastructure
```

After deploy, push the Docker image to ECR:

```bash
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker tag india-football-funnel:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/india-football-funnel:latest

docker push \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/india-football-funnel:latest
```

## Smoke Test

```bash
# Upload raw fixture to trigger ETL
aws s3 cp tests/fixtures/sample_funnel.csv \
  s3://india-football-funnel-data-$AWS_ACCOUNT_ID/raw/state_registry/2024-06-01/sample_funnel.csv

# Invoke simulation Lambda
aws lambda invoke \
  --function-name iff-simulation-runner \
  --payload '{"scenario_name":"baseline","n_runs":10,"years":3,"rng_seed":42}' \
  /tmp/smoke-response.json

cat /tmp/smoke-response.json
```

## Athena Query

```sql
-- Run in Athena workgroup: iff-analytics
SELECT state, AVG(retention_rate) AS avg_retention
FROM iff_data_catalog.processed_funnel
GROUP BY state;
```

## Destroy (removes all resources)

```bash
make destroy
```

If S3 bucket deletion fails due to remaining objects:

```bash
aws s3 rm s3://india-football-funnel-data-$AWS_ACCOUNT_ID --recursive
make destroy
```

## Evidence Template

After a successful deploy, capture proof in `docs/deployment_evidence/`:

- `etl_lambda_log.txt` — CloudWatch log excerpt showing processed parquet write
- `simulation_lambda_response.json` — smoke test output
- `athena_query_result.csv` — screenshot or CSV export of an Athena query
- `terraform_apply_output.txt` — `terraform apply` summary

These artifacts let reviewers verify deployment without AWS account access.
