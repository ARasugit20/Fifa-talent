# India Football Funnel

Real-data migration: `iff-reproduce` now builds **state/UT public sports infrastructure**
descriptive analytics from manually downloaded official files with provenance validation.
Legacy associative regression and uncalibrated simulation remain available via separate
commands and test fixtures. AIFF CRS/CMS player-level data is not publicly accessible. See
[Data Availability Note](docs/data_availability_note.md) and [Data Inventory](docs/data_inventory.md).

## Local Setup

See [docs/SETUP.md](docs/SETUP.md) for environment variables, optional public-data clients, and the zero-cost workflow (`make setup`, `make test`, `make reproduce`).

## Architecture

```
Verified public data
      │
      ▼
┌─────────────┐     S3 raw/ prefix      ┌──────────────────┐
│  Clients    │ ──────────────────────► │  S3 Data Lake    │
│  (local/    │   8 inputs + manifest   │  (encrypted,     │
│   mocked CI)│                         │   lifecycle)     │
└─────────────┘                         └────────┬─────────┘
                                                 │ dataset-ready.json
                                                 ▼
                                        ┌──────────────────┐
                                        │  Lambda ETL      │
                                        │  (four-source    │
                                        │   infrastructure)│
                                        └────────┬─────────┘
                                                 │
                    ┌────────────────────────────┼────────────────────────┐
                    ▼                            ▼                        ▼
           S3 processed/                  Glue Catalog              Lambda Simulation
                    │                            │                   (Monte Carlo)
                    └────────────┬───────────────┘                        │
                                 ▼                                        ▼
                          ┌─────────────┐                        S3 results/
                          │   Athena    │
                          │  (ad-hoc    │
                          │   queries)  │
                          └─────────────┘
```

Deployment evidence (Terraform plan, ETL logs, Glue schema, Athena results) is captured via [docs/deployment_evidence/RUNBOOK.md](docs/deployment_evidence/RUNBOOK.md). Evidence from live runs is stored under `docs/deployment_evidence/runs/` or downloaded from GitHub Actions artifacts.

## How This Is Engineered

[![CI](https://github.com/ARasugit20/Fifa-talent/actions/workflows/ci.yml/badge.svg)](https://github.com/ARasugit20/Fifa-talent/actions/workflows/ci.yml)
[![Deploy](https://github.com/ARasugit20/Fifa-talent/actions/workflows/deploy.yml/badge.svg)](https://github.com/ARasugit20/Fifa-talent/actions/workflows/deploy.yml)

| Check | Status |
|-------|--------|
| Test coverage | **91%** on `src/india_football_funnel` |
| Type safety | mypy strict, zero errors |
| Lint | ruff |
| Tests | 119 passing (unit + integration + terraform checks) |

```bash
make setup       # one-command local env (no AWS cost)
make test        # ruff + mypy + pytest --cov
make reproduce   # regenerate all outputs from raw data
make simulate    # quick baseline illustrative scenario (uncalibrated, not a forecast)
make plan        # terraform plan (requires AWS_ACCOUNT_ID and ECR_IMAGE_TAG)
make plan-artifact  # save plan output under docs/deployment_evidence/runs/
make collect-evidence  # post-deploy smoke + logs (stack must be live)
make deploy      # stand up AWS stack (manual, billable)
make destroy     # tear down AWS stack
```

## Why These Design Choices

- **Lambda + S3 events over batch** — ETL runs only when new raw files arrive; no idle scheduler cost. [ADR 001](docs/adr/001-lambda-s3-events-over-batch.md)
- **Container Lambda over zip** — `numpy`/`scipy`/`statsmodels` exceed the 250 MB zip limit; ECR images remove that constraint. [ADR 002](docs/adr/002-container-lambda-over-zip.md)
- **Athena over database** — read-mostly Parquet analytics don't justify standing RDS/Redshift cost. [ADR 003](docs/adr/003-athena-over-database.md)

See also: [cost estimate](docs/cost_estimate.md) · [AWS deploy guide](docs/aws_deploy_guide.md)

## Data Sources

Only verified public sources are used in v1. Full source notes live in
[Data Provenance](docs/data_provenance.md).
Each `make reproduce` run also emits a non-blocking [data quality scorecard](docs/metrics_glossary.md) and reconciliation audit; simulation outputs record a versioned [assumption registry](docs/simulation_assumptions.md). See [architecture.md](docs/architecture.md) for local and AWS flows.

| Source | Use |
|--------|-----|
| Census of India 2011 | District youth population denominators (`census_year: 2011` on every row) |
| data.gov.in Khelo India | Medal tally, budget allocation, sports-sector resource discovery |
| kheloindia.gov.in / yas.gov.in | Official facility and programme documents; no secondary-source substitution |
| FIFA official documents | Manual, page-cited talent-development report extraction |
| AFC technical reports | Manual, page-cited youth tournament technical-report extraction |

AIFF CRS/CMS and Academy Accreditation portals are explicitly not scraped. See
`src/india_football_funnel/data/scrapers/_deprecated_unavailable/README.md`.

## Repo Map

```
src/india_football_funnel/
  config.py              # constants, thresholds, AWS resource names
  models.py              # Pydantic models (InvestmentOutcomeObservation, ScenarioParams, …)
  data/                  # Census/data.gov.in/PDF clients, loader, schema validation
  analysis/              # investment-outcome metrics, geospatial, associative regression
  simulation/            # uncalibrated Monte Carlo illustrative scenarios
  aws/                   # S3 client, Lambda handlers, Athena queries
  cli.py                 # reproduce / simulate entry points
infra/terraform/         # S3, Lambda, ECR, Glue, Athena, IAM
tests/                   # unit + integration + fixtures
docs/adr/                # architecture decision records
docs/cost_estimate.md    # monthly cost breakdown
.github/workflows/       # CI + manual deploy
```

## Cost Safety

Local development (`make setup`, `make test`, `make reproduce`) costs **$0** — no AWS resources are created. Deploy only when demonstrating; run `make destroy` immediately after. Expected idle cost if left running: ~$0.10–$0.20/month at portfolio data volumes.
