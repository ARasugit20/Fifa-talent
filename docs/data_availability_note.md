# Data Availability Note

## Scope

The primary `iff-reproduce` pipeline now produces **state/UT public sports infrastructure and
investment descriptive analytics**. It is **not** football-player analytics and must not be
read as football-specific performance measurement.

## What is available

| Category | Status | Notes |
|---|---|---|
| MD-SD state/UT project progress & amounts | **Manual official download required** | Place exports in `data/raw/mdsd/` with provenance JSON. Do not scrape the beta dashboard. |
| Khelo India state/UT financial assistance | **Manual official download required** | Typically from data.gov.in resource pages; record the exact download URL in provenance. |
| Census 2011 state/UT denominators | **Manual official download required** | Denominator definition must be explicit in the CSV (e.g. total population 2011). A 10–17 youth band is **not** assumed unless the supplied file documents it. |
| Ministry DDG / annual reports | Optional context | National-level validation only; not a state-level substitute. |
| Legacy investment/outcome fixture CSV | Test/legacy path only | `sample_investment_outcomes.csv` supports associative regression and simulation tests; not used by default `iff-reproduce`. |

## What is not available

- **AIFF CRS/CMS / Academy Accreditation player records** — login-gated, no public bulk export, minor-data risk. Not scraped or approximated.
- **Live dashboard scraping** — `mdsd.kheloindia.gov.in` and `dashboard.kheloindia.gov.in` are reference pages only; the pipeline reads local files supplied by the operator.
- **Automated data.gov.in fetch in reproduce** — API clients remain for optional/legacy workflows; `iff-reproduce` does not call them.

## Analytic posture

- **Associative regression** (`analysis/associative_regression.py`) — exploratory associations only; not causal inference. Not run by default `iff-reproduce`.
- **Simulation** (`simulate` / `iff-simulate`) — illustrative, assumption-based, **uncalibrated** scenarios; not forecasts.
- **Census denominators** — 2011 vintage; flagged `denominator_is_stale` when joined to later infrastructure reporting periods.

## Running locally

1. Download official files listed in [data_inventory.md](data_inventory.md).
2. Add sibling `.provenance.json` files with SHA-256 checksums.
3. Run `make reproduce`.

CI uses redacted fixtures under `tests/fixtures/raw/`; it does **not** prove live official retrieval.

See also: [data_provenance.md](data_provenance.md) · [data_inventory.md](data_inventory.md)
