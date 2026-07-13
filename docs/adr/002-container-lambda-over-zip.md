# ADR 002: Container-Image Lambda over Zip Deployment

## Status
Accepted

## Context
The analysis stack depends on `numpy`, `pandas`, `scipy`, `statsmodels`, and `pyarrow`. Combined, these exceed AWS Lambda's 250 MB unzipped deployment package limit.

## Decision
Package Lambda functions as container images stored in ECR, using the AWS Lambda Python 3.11 base image.

## Consequences
- **Pros:** No dependency size constraints; identical environment to local Docker builds.
- **Cons:** Slightly higher cold-start time; requires ECR push in deploy pipeline.
- **Cost:** ECR storage is pennies/month for a single image; lifecycle policy keeps last 3 tags.
