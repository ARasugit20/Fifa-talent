-- Primary v1 analysis grain: public investment/outcome observations.
CREATE TABLE investment_outcome_observation (
    state TEXT NOT NULL,
    district TEXT,
    year INTEGER NOT NULL,
    census_year INTEGER NOT NULL CHECK (census_year = 2011),
    youth_population_10_17 INTEGER NOT NULL,
    budget_allocation_inr DOUBLE PRECISION NOT NULL,
    budget_per_capita DOUBLE PRECISION NOT NULL,
    khelo_india_centres DOUBLE PRECISION,
    facility_density DOUBLE PRECISION,
    participation_count INTEGER NOT NULL,
    participation_rate DOUBLE PRECISION NOT NULL,
    medals INTEGER NOT NULL,
    medals_per_participant DOUBLE PRECISION NOT NULL,
    tournament_results_score DOUBLE PRECISION,
    facility_data_status TEXT NOT NULL,
    source_file TEXT NOT NULL
);

-- Deprecated concept only; do not reuse this name for the public-data grain.
-- funnel_observation represented an unavailable player-level AIFF CRS/CMS funnel.
