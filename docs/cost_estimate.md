# Cost Estimate

Estimated monthly cost for portfolio-scale data volumes, assuming brief deploy-verify-destroy cycles.

| Service | Usage Assumption | Est. Monthly Cost |
|---------|------------------|-------------------|
| S3 Standard | < 1 GB raw + processed + results | < $0.05 |
| S3 Glacier | Raw data after 90-day lifecycle | < $0.01 |
| Lambda ETL | ~10 invocations/month, 512 MB, 30s | < $0.01 |
| Lambda Simulation | ~20 invocations/month, 1024 MB, 60s | < $0.05 |
| ECR | 1 container image (~500 MB) | < $0.05 |
| Glue Data Catalog | 2 tables | Free tier |
| Athena | < 100 MB scanned/month | < $0.01 |
| CloudWatch Logs | 14-day retention, low volume | < $0.01 |

**Total (deployed briefly):** ~$0.10–$0.20/month if left running idle.

**Recommended practice:** Run `make deploy` only when demonstrating; run `make destroy` immediately after. Local development (`make setup`, `make test`, `make reproduce`) costs **$0**.

## Cost Guardrails Built Into the Repo

- No AWS resources created by CI tests or `make reproduce`
- Deploy workflow requires manual `workflow_dispatch` approval
- S3 lifecycle transitions raw data to Glacier after 90 days
- ECR lifecycle keeps only the last 3 images
- CloudWatch log retention set to 14 days
- IAM policies scoped to specific bucket prefixes, not `*`
