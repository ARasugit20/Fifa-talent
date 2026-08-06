# Architecture

This repository supports two related flows: a **local provenance-validated reproduce path**
for state/UT public sports infrastructure analytics, and an optional **AWS event-driven**
path for legacy CSV ETL and illustrative simulation uploads.

## Local reproduce flow

```mermaid
flowchart LR
  operator[Operator manual downloads] --> raw[data/raw/*]
  raw --> provenance[.provenance.json SHA-256]
  provenance --> validate[validate_required_raw_inputs]
  validate --> parse[source parsers]
  parse --> join[build_public_sports_infrastructure_frame]
  join --> parquet[public_sports_infrastructure.parquet]
  join --> quality[data_quality_report.json]
  join --> reconcile[state_reconciliation_report.csv]
  join --> manifest[run_manifest.json]
  join --> summaries[infrastructure_summaries.json]
```

Key properties:

- No dashboard scraping; only local files with sibling provenance metadata.
- Unmapped state/UT names fail the pipeline.
- Quality scorecard warnings are non-blocking by default.
- Simulation remains a separate, uncalibrated command (`iff-simulate`).

## AWS event-driven flow

```mermaid
flowchart LR
  upload[S3 raw/*.csv upload] --> notify[S3 ObjectCreated event]
  notify --> etl[Lambda ETL handler]
  etl --> idempotent{Processed for same ETag?}
  idempotent -->|yes| skip[Tag raw skipped-duplicate]
  idempotent -->|no| process[process_raw_file legacy CSV]
  process --> processed[S3 processed/*.parquet]
  process --> tag[Tag raw/processed iff:* metadata]
  simInvoke[Manual/async simulation invoke] --> simLambda[Lambda simulation handler]
  simLambda --> results[S3 results/scenario/*]
  processed --> athena[Athena / Glue catalog]
```

Idempotency rules for ETL:

- Before processing, the handler checks whether the target processed object exists and carries
  the same `iff:source-etag` tag as the incoming raw object.
- Duplicate uploads with unchanged content are tagged `iff:processing-status=skipped-duplicate`
  and return HTTP 200 without reprocessing.
- Successful runs tag both raw and processed objects with processing status and source ETag.

## Observability and cost guardrails

```mermaid
flowchart TB
  lambdaErrors[Lambda Errors metric] --> etlAlarm[CloudWatch etl-lambda-errors alarm]
  billing[AWS/Billing EstimatedCharges] --> costAlarm[CloudWatch estimated-monthly-charges alarm]
  etlAlarm --> sns[Optional SNS ops topic]
  costAlarm --> sns
  rawLifecycle[S3 raw/ Glacier transition] --> costControl[Lifecycle cost control]
  ecrLifecycle[ECR keep last 3 images] --> costControl
  logRetention[CloudWatch log retention 14d] --> costControl
```

Terraform resources:

- `infra/terraform/alarms.tf` — billing and Lambda error alarms
- `infra/terraform/s3.tf` — encrypted bucket, raw lifecycle, ETL notification
- `infra/terraform/tags.tf` — shared cost-allocation tags

## Module map

| Path | Role |
|---|---|
| `src/india_football_funnel/data/infrastructure_pipeline.py` | Primary reproduce build + manifest |
| `src/india_football_funnel/data/provenance.py` | Provenance validation and operator helpers |
| `src/india_football_funnel/data/quality_checks.py` | Runtime data-quality scorecard |
| `src/india_football_funnel/simulation/assumption_registry.py` | Versioned simulation assumption snapshot |
| `src/india_football_funnel/aws/lambda_handlers.py` | S3-triggered ETL + simulation handlers |
| `src/india_football_funnel/cli.py` | `iff-reproduce`, `iff-simulate`, `iff-provenance` |

See also: [metrics_glossary.md](metrics_glossary.md) · [data_inventory.md](data_inventory.md) · ADRs in [adr/](adr/)
