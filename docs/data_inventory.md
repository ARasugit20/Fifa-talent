# Data Inventory

This file lists **actual** raw inputs the pipeline can consume. A source is listed only when
the corresponding artifact and sibling `.provenance.json` exist (or when a committed test
fixture mirrors the official layout).

## Operator workflow

1. Manually download original official files — do **not** scrape `mdsd.kheloindia.gov.in` or
   `dashboard.kheloindia.gov.in`.
2. Place files under `data/raw/<source>/`.
3. Create `<filename>.provenance.json` beside each file with a matching SHA-256 digest.
4. Run `make reproduce` (or `iff-reproduce`).

If any required file or provenance record is missing, `iff-reproduce` fails with the expected
path, file role, and official source page URL.

## Required primary inputs

| Relative path | Role | Official source page | Status in repo |
|---|---|---|---|
| `mdsd/state_wise_progress.csv` | MD-SD state/UT infrastructure project status counts | https://mdsd.kheloindia.gov.in/state-wise-progress | **Test fixture only** under `tests/fixtures/raw/mdsd/` |
| `mdsd/grantee_amounts.csv` | MD-SD amount sanctioned/released by state/UT | https://mdsd.kheloindia.gov.in/gratee-type-wise-progress | **Test fixture only** |
| `khelo_india/financial_assistance.csv` | State/UT financial assistance under Khelo India / NSDF | https://www.data.gov.in/resource/stateuts-wise-details-financial-assistance-provided-under-khelo-india-scheme-and-national | **Test fixture only** |
| `census/state_population_2011.csv` | Census 2011 denominator at state/UT grain | https://www.data.gov.in/catalog/primary-census-abstract-2011-india-and-states-0 | **Test fixture only** |

## Optional national-context inputs

| Relative path | Role | Notes |
|---|---|---|
| `ministry_reports/*.pdf` | DDG / annual-report cross-check | Not required for `iff-reproduce`; use only for national total validation |

No ministry report artifacts are committed in this repository.

## Test fixtures (redacted excerpts)

Committed under `tests/fixtures/raw/` for CI and local integration tests:

- `mdsd/state_wise_progress.csv` + `.provenance.json`
- `mdsd/grantee_amounts.csv` + `.provenance.json`
- `khelo_india/financial_assistance.csv` + `.provenance.json`
- `census/state_population_2011.csv` + `.provenance.json`

Fixture values are illustrative excerpts shaped like official exports. They are **not** a
substitute for operator-supplied production raw files in `data/raw/`.

## Schema notes (verified against fixtures)

| File | Required columns | Units / grain |
|---|---|---|
| MD-SD progress | `state`, `projects_to_be_started`, `projects_under_progress`, `projects_completed`, `projects_total` | State/UT counts; reporting period from provenance `time_coverage` |
| MD-SD amounts | `state`, `amount_sanctioned`, `amount_released`, `source_unit` | `source_unit` must be `crore` or `inr`; crore converted to INR in processing |
| Khelo India assistance | `state`, `financial_assistance`, `source_unit` | Same unit handling as MD-SD amounts |
| Census denominator | `state`, `denominator_value`, `denominator_definition` | Explicit definition required (e.g. `total_population_2011_state_ut`); flagged stale when paired with later reporting years |

## Processed outputs

`iff-reproduce` writes:

- `data/processed/public_sports_infrastructure.parquet`
- `data/processed/infrastructure_by_state.csv`
- `data/results/analysis/infrastructure_summaries.json`
- `data/results/run_manifest.json`

Every row carries source filename, source URL, retrieval timestamp, and provenance SHA-256.
