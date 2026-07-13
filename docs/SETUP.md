# Local Setup

This guide covers zero-cost local development for the India Football Funnel project.

## Prerequisites

- Python 3.11 or 3.12
- `make` (macOS/Linux) or run the equivalent commands manually on Windows

## Quick start

```bash
make setup
make test
make reproduce
```

`make setup` creates a virtual environment, installs dev dependencies, and registers pre-commit hooks.

## Environment variables

Copy the example file and fill in values only when you need live public-data ingestion or AWS deploy:

```bash
cp .env.example .env
```

| Variable | Required for | Notes |
|----------|--------------|-------|
| `DATAGOVINDIA_API_KEY` | Live Khelo India pulls | Free key from [data.gov.in](https://data.gov.in/) |
| `AWS_ACCOUNT_ID` | `make plan` / `make deploy` | 12-digit AWS account ID |
| `AWS_REGION` | AWS deploy | Defaults to `ap-south-1` |
| `IFF_LOCAL_MODE` | Local runs | Keep `true` to avoid accidental AWS calls |

Local tests and `make reproduce` do **not** require API keys.

## Optional public-data clients

Install optional ingestion dependencies when pulling Census Excel fallbacks, data.gov.in APIs, or FIFA/AFC PDFs:

```bash
pip install -e ".[public-data]"
```

## Fixture data

Integration and unit tests use `tests/fixtures/sample_investment_outcomes.csv`, a 10-state public-data shaped sample tagged with `census_year: 2011`.

## Reproduce outputs

```bash
make reproduce
```

This writes processed parquet and analysis artifacts under `data/processed/` and `data/results/` (gitignored).

## Next steps

- [Data Provenance](data_provenance.md) — verified source list
- [Data Availability Note](data_availability_note.md) — what is and is not publicly accessible
- [AWS Deploy Guide](aws_deploy_guide.md) — manual, billable stack setup
