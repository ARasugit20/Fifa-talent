# Deployment evidence

Proof that the Terraform stack deploys and the manifest-triggered ETL pipeline runs end-to-end.

**Do not commit fabricated output.** Only add files from a real AWS run after redacting sensitive identifiers.

## Quick links

- [RUNBOOK.md](RUNBOOK.md) — step-by-step plan, deploy, capture, teardown
- [scripts/collect_deploy_evidence.sh](../../scripts/collect_deploy_evidence.sh) — automated evidence collector
- [Terraform Plan workflow](../../.github/workflows/terraform-plan.yml) — manual CI plan artifact (requires AWS secrets)
- [Deploy workflow](../../.github/workflows/deploy.yml) — full deploy + smoke tests

## Directory layout

```text
docs/deployment_evidence/
  RUNBOOK.md
  runs/
    <timestamp>/          # one directory per evidence capture run
      terraform_plan.txt
      etl_lambda_log.txt
      glue_public_sports_infrastructure.json
      athena_query_result.csv
      ...
```

Runs under `runs/` are gitignored until you explicitly `git add` a redacted run directory.

## Populate evidence

```bash
export AWS_ACCOUNT_ID=...
export AWS_REGION=ap-south-1
make plan-artifact                    # plan only
make deploy                           # billable apply
./scripts/collect_deploy_evidence.sh post-deploy
make destroy                          # teardown
```

See [aws_deploy_guide.md](../aws_deploy_guide.md) for full deploy prerequisites.
