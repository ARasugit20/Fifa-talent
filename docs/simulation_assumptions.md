# Simulation Assumptions

The simulation is an illustrative, assumption-based and **uncalibrated** scenario model.
It does not estimate causal effects or forecast real-world outcomes. Every simulation JSON
summary records this registry and `assumption_registry_version: "v1"`.

| Assumption | Source | Unit | Rationale | Sensitivity range |
|---|---|---|---|---|
| `baseline_participation_rate` | scenario | share of youth population | Initial scenario participation share | 0–1 |
| `baseline_medals_per_participant` | scenario | medals per participant | Initial scenario medal yield | ≥0 |
| `budget_per_capita` | scenario | INR per person | Baseline investment level | ≥0 |
| `target_budget_per_capita` | scenario | INR per person | Optional intervention target | ≥0 / null |
| `growth_rate_override` | scenario | annual rate | Optional scenario override for growth | scenario-defined / null |
| `years` | scenario | years | Simulation horizon | 1–50 |
| `n_runs` | scenario | Monte Carlo runs | Number of seeded paths | 1–100,000 |
| `rng_seed` | scenario | seed | Reproducible random-generator seed | fixed per run |
| `PARTICIPATION_GROWTH_RATE_MEAN` | config | annual rate | Default participation growth, not observed-data calibrated | 0–0.10 |
| `PARTICIPATION_GROWTH_RATE_STD` | config | annual-rate standard deviation | Growth uncertainty | 0–0.05 |
| `BUDGET_EFFECT_MEAN` | config | participation-rate uplift | Intervention uplift; not a causal estimate | 0–0.20 |
| `BUDGET_EFFECT_STD` | config | uplift standard deviation | Intervention-effect uncertainty | 0–0.10 |

`assumption_registry_version` is a derived metadata entry. When a default, interpretation,
or registry shape changes, increment it so historical summaries remain interpretable.
