# Deployment Evidence Runbook

This runbook captures **real** proof that the Terraform stack deploys and the manifest-triggered ETL pipeline works. Do not commit fabricated logs — only artifacts from an actual AWS run.

## Why credentials stay out of automatic CI

`terraform plan` calls `aws_caller_identity` and refreshes provider state, so a full plan requires live AWS credentials. Automatic push CI runs `terraform validate` only (no secrets). Full plan output is collected via:

- **Manual:** `make plan-artifact` or `scripts/collect_deploy_evidence.sh`
- **GitHub Actions:** [Terraform Plan workflow](../../.github/workflows/terraform-plan.yml) (`workflow_dispatch`, uses `production` environment secrets)

## Prerequisites

```bash
export AWS_ACCOUNT_ID=123456789012
export AWS_REGION=ap-south-1
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export ECR_IMAGE_TAG=$(git rev-parse HEAD)
```

Also install: Terraform >= 1.5, AWS CLI v2, Docker (for image push before apply).

## Step 1 — Plan only (no billable apply)

Save plan output locally or via CI artifact:

```bash
make plan-artifact
# or
./scripts/collect_deploy_evidence.sh plan
```

Expected output: `docs/deployment_evidence/runs/<timestamp>/terraform_plan.txt`

## Step 2 — Deploy stack (billable)

Follow [aws_deploy_guide.md](../aws_deploy_guide.md):

```bash
make docker-build
# push image to ECR with tag $ECR_IMAGE_TAG
make deploy
```

Or trigger the [Deploy workflow](../../.github/workflows/deploy.yml) via `workflow_dispatch` (runs tests, pushes image, applies Terraform).

## Step 3 — Post-deploy evidence capture

After the stack is live and the ECR image is pushed:

```bash
./scripts/collect_deploy_evidence.sh post-deploy
```

This script:

1. Syncs `tests/fixtures/raw/` to S3 (eight inputs + provenance)
2. Uploads `raw/dataset-ready.json` to trigger ETL Lambda
3. Captures CloudWatch log excerpt from `iff-etl-processor`
4. Runs `aws glue get-table` for `iff_data_catalog.public_sports_infrastructure`
5. Runs an Athena query and saves CSV result
6. Lists `processed/` and `results/` S3 keys

Evidence lands in `docs/deployment_evidence/runs/<timestamp>/`.

## Step 4 — Commit evidence (optional, after redaction)

Review files for account IDs, ARNs, or internal URLs. Redact if sharing publicly, then:

```bash
git add docs/deployment_evidence/runs/<timestamp>/
git commit -m "Add deployment evidence from <date> run."
```

Link the run directory from [README.md](../../README.md) architecture section.

## Step 5 — Teardown (keep cost near idle estimate)

```bash
# Empty bucket if destroy fails on non-empty bucket
aws s3 rm s3://india-football-funnel-data-$AWS_ACCOUNT_ID --recursive
make destroy
```

Expected idle cost if left running: ~$0.10–$0.20/month per [cost_estimate.md](../cost_estimate.md).

## Expected evidence files

| File | Source |
|------|--------|
| `terraform_plan.txt` | `terraform plan` |
| `terraform_apply_output.txt` | Deploy workflow or manual `make deploy` |
| `etl_lambda_log.txt` | CloudWatch `/aws/lambda/iff-etl-processor` |
| `glue_public_sports_infrastructure.json` | `aws glue get-table` |
| `athena_query.sql` | Smoke query text |
| `athena_query_result.csv` | Athena execution output |
| `s3_artifact_listing.txt` | `aws s3 ls` on processed/results |
| `dataset-ready.json` | Manifest uploaded to trigger ETL |

## GitHub Actions artifacts

- **Terraform Plan workflow:** uploads `terraform_plan.txt` (30-day retention)
- **Deploy workflow:** uploads `deploy-evidence/` bundle after smoke tests (when deploy succeeds)

Download artifacts from the Actions run page and copy into `docs/deployment_evidence/runs/` if you want them in git.
