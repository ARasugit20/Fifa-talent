# Changelog

## Unreleased

### Added
- **Phase C CLI coverage** — Added argparse error, all `--skip-*` interactions, explicit-option precedence, provenance subcommand dispatch, unknown filename, and console-entry-point tests; `cli.py` now has 98% focused coverage.
- **Phase B deployment evidence** — Manual runbook, `collect_deploy_evidence.sh`, Terraform Plan workflow (artifact upload), Deploy workflow ETL/Glue/Athena evidence capture, and `make plan-artifact` / `make collect-evidence` targets.
- **Phase 3 Lambda pipeline alignment** — Manifest-triggered four-source infrastructure ETL on `raw/dataset-ready.json`, shared `write_reproduce_artifacts()` for local/AWS parity, provenance SHA-256 fingerprint idempotency, Glue `public_sports_infrastructure` table, moto integration tests, and updated deploy documentation.
- **Phase 2 pipeline gaps** — CLI `--skip-*` reproduce flags, `iff-provenance` helper commands, Lambda S3 tagging/idempotency, Terraform cost/error alarms, and docs for metrics/architecture.
- **Runtime quality scorecard** — `iff-reproduce` now writes a non-blocking data-quality report and a state/UT reconciliation CSV, both referenced by the run manifest.
- **Simulation assumption registry** — Simulation JSON and Parquet outputs now snapshot versioned scenario and config assumptions; see `docs/simulation_assumptions.md`.
- **Primary public-data migration** — Manual-download-first infrastructure pipeline with provenance-validated raw inputs (`data/provenance.py`, `data/parsers/*`, `data/infrastructure_pipeline.py`).
- **State/UT reconciliation** — Canonical mapping and alias handling in `data/state_names.py`; unmapped names fail the pipeline.
- **Test fixtures** — Redacted official-layout CSVs and provenance JSON under `tests/fixtures/raw/`.
- **Documentation** — `docs/data_inventory.md`; updated `docs/data_availability_note.md` and `docs/data_provenance.md`.

### Changed
- **AWS ETL** — Replaced legacy per-CSV `process_raw_file()` Lambda path with manifest-triggered infrastructure pipeline aligned to `iff-reproduce`.
- **`iff-reproduce`** — Builds state/UT public sports infrastructure descriptive outputs only; no synthetic fixture fallback.
- **Scope labeling** — Processed metrics are explicitly not football-specific; Census 2011 denominators flagged stale when paired with later reporting years.

### Removed
- **`scrape_state_registry_stub`** — Deleted synthetic state registry fixture generator.

### Fixed
- **Deploy ordering and image traceability** — Reordered `.github/workflows/deploy.yml` so Docker images are built and pushed before Terraform apply. Lambda images now use immutable git-SHA tags via `ecr_image_tag` in `infra/terraform/main.tf` instead of mutable `:latest`.
- **Deprecated model validation** — Removed unused `FunnelObservation`, which validated legacy player stages against the new public-data funnel constants.
- **Simulation participation trajectory** — `participation_rate` now carries forward year-over-year in `simulation/talent_flow_model.py` instead of resetting each iteration.

### Changed
- **Associative regression labeling** — Renamed `analysis/causal_regression.py` to `analysis/associative_regression.py` and relabeled docs/logs/README to describe exploratory associations, not causal inference.
- **Uncalibrated simulation labeling** — Added `assumption_based` and `uncalibrated` fields to simulation JSON/Parquet outputs and clarified CLI/README wording that scenarios are illustrative, not forecasts.

### Added
- **MIT LICENSE** — Added root `LICENSE` file for the MIT license declared in `pyproject.toml` (`Copyright (c) 2026 Aditya Ranjan`).
