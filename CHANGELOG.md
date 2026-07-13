# Changelog

## Unreleased

### Fixed
- **Deploy ordering and image traceability** — Reordered `.github/workflows/deploy.yml` so Docker images are built and pushed before Terraform apply. Lambda images now use immutable git-SHA tags via `ecr_image_tag` in `infra/terraform/main.tf` instead of mutable `:latest`.
- **Deprecated model validation** — Removed unused `FunnelObservation`, which validated legacy player stages against the new public-data funnel constants.
- **Simulation participation trajectory** — `participation_rate` now carries forward year-over-year in `simulation/talent_flow_model.py` instead of resetting each iteration.

### Changed
- **Associative regression labeling** — Renamed `analysis/causal_regression.py` to `analysis/associative_regression.py` and relabeled docs/logs/README to describe exploratory associations, not causal inference.
- **Uncalibrated simulation labeling** — Added `assumption_based` and `uncalibrated` fields to simulation JSON/Parquet outputs and clarified CLI/README wording that scenarios are illustrative, not forecasts.

### Added
- **MIT LICENSE** — Added root `LICENSE` file for the MIT license declared in `pyproject.toml` (`Copyright (c) 2026 Aditya Ranjan`).
