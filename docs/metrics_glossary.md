# Metrics Glossary

Definitions for metrics emitted by the public sports infrastructure pipeline,
legacy investment/outcome analytics, quality scorecard, and illustrative simulation.

## Infrastructure metrics (`iff-reproduce`)

| Metric | Definition | Unit | Source |
|---|---|---|---|
| `projects_total` | Total MD-SD infrastructure projects reported for a state/UT | count | MD-SD progress export |
| `projects_completed` | Projects marked completed in the MD-SD export | count | MD-SD progress export |
| `completion_rate` | `projects_completed / projects_total` | ratio (0–1) | Derived in `infrastructure_metrics.py` |
| `amount_sanctioned_inr` | Sanctioned amount converted to INR when source unit is crore | INR | MD-SD grantee amounts |
| `amount_released_inr` | Released amount converted to INR when source unit is crore | INR | MD-SD grantee amounts |
| `financial_assistance_inr` | Khelo India / NSDF financial assistance converted to INR | INR | Khelo India export |
| `amount_released_per_capita` | `amount_released_inr / denominator_value` | INR per person | Derived |
| `financial_assistance_per_capita` | `financial_assistance_inr / denominator_value` | INR per person | Derived |
| `denominator_value` | Explicit Census 2011 denominator supplied by operator | persons | Census CSV |
| `denominator_definition` | Human-readable denominator label (e.g. `total_population_2011_state_ut`) | text | Census CSV |
| `denominator_year` | Census vintage for the denominator | year | Fixed to 2011 |
| `denominator_is_stale` | True when denominator vintage is older than the reporting period | boolean | Derived |

## Data quality scorecard

| Metric | Definition | Blocking? |
|---|---|---|
| `census_staleness_years` | Reference year minus `denominator_year` | No |
| `missing_canonical_states` | Canonical states/UTs absent from joined output (excluding Ladakh) | No |
| `states_dropped_from_join` | Reconciled states present in sources but absent after join | No |
| `rows_per_state_min` / `rows_per_state_max` | Row-count sanity for one-row-per-state grain | No |
| `stale_denominator_count` | Rows flagged with stale Census denominators | No |
| `blocking` | Reserved for hard failures; currently always false in scorecard | — |

Hard failures (empty join, unmapped state names) still abort the pipeline before scorecard emission.

## Legacy investment/outcome metrics

| Metric | Definition | Unit |
|---|---|---|
| `budget_allocation_inr` | Public sports budget allocation for a state/district-year | INR |
| `budget_per_capita` | `budget_allocation_inr / youth_population_10_17` | INR per youth |
| `participation_count` | Reported participation proxy | count |
| `participation_rate` | `participation_count / youth_population_10_17` | ratio |
| `medals_per_participant` | `medals / participation_count` | medals per participant |
| `facility_density` | `khelo_india_centres / youth_population_10_17` when centres are available | centres per youth |

## Simulation outputs (uncalibrated)

| Metric | Definition | Notes |
|---|---|---|
| `mean_medals` | Mean medals across Monte Carlo runs for a scenario year | Illustrative only |
| `p10_medals` / `p90_medals` | 10th / 90th percentile medal counts | Not calibrated to observed data |
| `mean_participation_rate` | Scenario baseline participation rate carried in summaries | Not a live estimate |
| `assumption_based` | Always true; marks manual scenario/config inputs | See `docs/simulation_assumptions.md` |
| `uncalibrated` | Always true; outputs are not forecasts | — |

See also: [simulation_assumptions.md](simulation_assumptions.md) · [architecture.md](architecture.md)
