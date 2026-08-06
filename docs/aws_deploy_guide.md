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
export ECR_IMAGE_TAG=$(git rev-parse HEAD)   # immutable deploy tag
```

## Deploy (creates billable resources)

```bash
make setup          # local env only, no AWS cost
make docker-build   # build Lambda container locally
make plan           # preview Terraform changes (requires ECR_IMAGE_TAG)
make deploy         # apply infrastructure
```

`make plan`, `make deploy`, and `make destroy` pass `-var="ecr_image_tag=$(ECR_IMAGE_TAG)"`.
Set `ECR_IMAGE_TAG` to the git commit SHA that produced the pushed image.

After deploy, push the Docker image to ECR with the same immutable tag:

```bash
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker tag india-football-funnel:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/india-football-funnel:$ECR_IMAGE_TAG

docker push \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/india-football-funnel:$ECR_IMAGE_TAG
```

## S3 upload layout (manifest-triggered ETL)

Upload the eight validated raw inputs first, then upload the ready manifest **last** to trigger Lambda once:

```text
s3://<bucket>/raw/mdsd/state_wise_progress.csv
s3://<bucket>/raw/mdsd/state_wise_progress.csv.provenance.json
s3://<bucket>/raw/mdsd/grantee_amounts.csv
s3://<bucket>/raw/mdsd/grantee_amounts.csv.provenance.json
s3://<bucket>/raw/khelo_india/financial_assistance.csv
s3://<bucket>/raw/khelo_india/financial_assistance.csv.provenance.json
s3://<bucket>/raw/census/state_population_2011.csv
s3://<bucket>/raw/census/state_population_2011.csv.provenance.json
s3://<bucket>/raw/dataset-ready.json   # upload last
```

Example `dataset-ready.json`:

```json
{
  "dataset_version": "v1",
  "object_keys": [
    "raw/census/state_population_2011.csv",
    "raw/census/state_population_2011.csv.provenance.json",
    "raw/khelo_india/financial_assistance.csv",
    "raw/khelo_india/financial_assistance.csv.provenance.json",
    "raw/mdsd/grantee_amounts.csv",
    "raw/mdsd/grantee_amounts.csv.provenance.json",
    "raw/mdsd/state_wise_progress.csv",
    "raw/mdsd/state_wise_progress.csv.provenance.json"
  ]
}
```

The manifest `object_keys` set must match the configured required inputs exactly.

## Smoke Test

```bash
BUCKET=india-football-funnel-data-$AWS_ACCOUNT_ID

# Upload fixture tree (eight inputs)
aws s3 sync tests/fixtures/raw/ s3://$BUCKET/raw/ --exclude ".gitkeep"

# Upload ready manifest last
python - <<'PY'
import json
from india_football_funnel.aws.infrastructure_etl import build_default_dataset_ready_manifest
print(build_default_dataset_ready_manifest().model_dump_json(indent=2))
PY > /tmp/dataset-ready.json

aws s3 cp /tmp/dataset-ready.json s3://$BUCKET/raw/dataset-ready.json

# Invoke simulation Lambda
aws lambda invoke \
  --function-name iff-simulation-runner \
  --payload '{"scenario_name":"baseline","n_runs":10,"years":3,"rng_seed":42}' \
  /tmp/smoke-response.json

cat /tmp/smoke-response.json
```

Verify ETL artifacts:

```bash
aws s3 ls s3://$BUCKET/processed/
aws s3 ls s3://$BUCKET/results/
```

Re-uploading the same manifest with unchanged provenance should return a skipped-duplicate result.

## Athena Query

```sql
-- Run in Athena workgroup: iff-analytics
SELECT canonical_state_ut,
       projects_total,
       amount_released_inr,
       denominator_value
FROM iff_data_catalog.public_sports_infrastructure
ORDER BY canonical_state_ut;
```

The legacy `investment_outcome_observation` table remains in Glue for older schema references but is not populated by the manifest ETL.

## Alarms

Terraform provisions optional CloudWatch alarms for Lambda errors and estimated monthly charges. Subscribe an SNS topic in `infra/terraform/alarms.tf` when operating a shared environment.

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

After a successful deploy, capture proof using [deployment_evidence/RUNBOOK.md](deployment_evidence/RUNBOOK.md):

```bash
./scripts/collect_deploy_evidence.sh post-deploy
make destroy   # teardown to stay near idle cost estimate
```

Or trigger the **Terraform Plan** / **Deploy** GitHub Actions workflows and download artifacts from the run page.
