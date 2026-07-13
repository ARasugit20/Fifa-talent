# ADR 001: Lambda + S3 Events over Scheduled Batch

## Status
Accepted

## Context
Raw funnel data arrives sporadically from state registry uploads. A scheduled batch job would poll S3 or run on a fixed cadence regardless of whether new data exists.

## Decision
Trigger ETL via S3 object-created events on the `raw/` prefix. Each upload is validated and written to `processed/` independently.

## Consequences
- **Pros:** Event-driven, scales horizontally with upload volume, no idle compute cost.
- **Cons:** Requires S3 notification wiring and idempotent ETL design. Cold starts add latency for infrequent uploads.
- **Cost:** Pay only when files arrive; no always-on scheduler.
