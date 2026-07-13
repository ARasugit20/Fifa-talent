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
make simulate   # baseline illustrative scenario only (uncalibrated, not a forecast)
```

`make setup` creates a virtual environment, installs dev dependencies, and registers pre-commit hooks.

## Environment variables

Copy the example file and fill in values only when you need legacy API clients or AWS deploy:

```bash
cp .env.example .env
```

| Variable | Required for | Notes |
|----------|--------------|-------|
| `DATAGOVINDIA_API_KEY` | Legacy data.gov.in client pulls | Not used by default `make reproduce` |
| `AWS_ACCOUNT_ID` | `make plan` / `make deploy` | 12-digit AWS account ID |
| `AWS_REGION` | AWS deploy | Defaults to `ap-south-1` |
| `IFF_LOCAL_MODE` | Local runs | Keep `true` to avoid accidental AWS calls |

Local tests do **not** require API keys. `make reproduce` requires manually downloaded official raw files (see below).

## Primary reproduce workflow (manual official downloads)

1. Download the four required files listed in [data_inventory.md](data_inventory.md).
2. Place them under `data/raw/mdsd/`, `data/raw/khelo_india/`, and `data/raw/census/`.
3. Create sibling `<filename>.provenance.json` files with matching SHA-256 checksums.
4. Run `make reproduce`.

If files are missing, `iff-reproduce` fails with the expected path, role, and official source page URL.

CI uses redacted fixtures under `tests/fixtures/raw/`; those fixtures are not a substitute for operator-supplied `data/raw/` files.

## Optional public-data clients

Install optional ingestion dependencies when using legacy Census Excel fallbacks, data.gov.in APIs, or FIFA/AFC PDFs:

```bash
pip install -e ".[public-data]"
```

## Fixture data

- **Infrastructure pipeline tests** — `tests/fixtures/raw/` (MD-SD, Khelo India, Census layouts with provenance JSON)
- **Legacy associative regression / simulation tests** — `tests/fixtures/sample_investment_outcomes.csv` (10-state sample tagged with `census_year: 2011`)

## Reproduce outputs

```bash
make reproduce
```

Writes:

- `data/processed/public_sports_infrastructure.parquet`
- `data/processed/infrastructure_by_state.csv`
- `data/results/analysis/infrastructure_summaries.json`
- `data/results/run_manifest.json`

Outputs are gitignored and regenerated locally.

## Next steps

- [Data Inventory](data_inventory.md) — required raw files and schema
- [Data Provenance](data_provenance.md) — verified source list
- [Data Availability Note](data_availability_note.md) — what is and is not publicly accessible
- [AWS Deploy Guide](aws_deploy_guide.md) — manual, billable stack setup
