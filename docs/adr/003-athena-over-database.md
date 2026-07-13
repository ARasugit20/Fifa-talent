# ADR 003: Athena over Standing Database

## Status
Accepted

## Context
Processed funnel data and simulation outputs are read-mostly Parquet files. Query patterns are ad-hoc analytics (retention by state, scenario comparison), not transactional OLTP.

## Decision
Register S3 Parquet prefixes in the Glue Data Catalog and query via Athena. No RDS or Redshift.

## Consequences
- **Pros:** Zero standing database cost; schema-on-read fits exploratory analytics; integrates with existing S3 layout.
- **Cons:** Query latency higher than indexed DB; per-scan pricing requires partition discipline at scale.
- **Cost:** Near-zero at portfolio data volumes; pay per TB scanned.
