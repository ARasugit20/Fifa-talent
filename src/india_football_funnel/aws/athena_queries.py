"""Example Athena SQL queries for analytics."""

from __future__ import annotations

AVERAGE_PARTICIPATION_BY_STATE = """
SELECT
    state,
    AVG(participation_rate) AS avg_participation_rate,
    AVG(budget_per_capita) AS avg_budget_per_capita,
    COUNT(*) AS observation_count
FROM investment_outcome_observation
GROUP BY state
ORDER BY avg_participation_rate DESC;
"""

SCENARIO_COMPARISON_SUMMARY = """
SELECT
    scenario_name,
    MAX(final_medals_mean) AS final_mean_medals,
    MAX(final_medals_std) AS final_std_medals
FROM simulation_results
GROUP BY scenario_name
ORDER BY final_mean_medals DESC;
"""

BUDGET_OUTCOME_BY_STATE = """
SELECT
    state,
    SUM(budget_allocation_inr) AS total_budget_inr,
    SUM(youth_population_10_17) AS youth_population_10_17,
    SUM(medals) AS medals
FROM investment_outcome_observation
GROUP BY state
ORDER BY medals DESC;
"""

YEARLY_SIMULATION_TREND = """
SELECT
    scenario_name,
    year,
    AVG(mean_medals) AS avg_medals,
    AVG(p10_medals) AS p10_medals,
    AVG(p90_medals) AS p90_medals
FROM simulation_results
GROUP BY scenario_name, year
ORDER BY scenario_name, year;
"""

ALL_QUERIES: dict[str, str] = {
    "average_participation_by_state": AVERAGE_PARTICIPATION_BY_STATE,
    "scenario_comparison_summary": SCENARIO_COMPARISON_SUMMARY,
    "budget_outcome_by_state": BUDGET_OUTCOME_BY_STATE,
    "yearly_simulation_trend": YEARLY_SIMULATION_TREND,
}
