# Data Availability Note

The original project design aimed to measure an individual player registration funnel:
grassroots → academy → semipro → professional → national team.

That design depended on AIFF CRS/CMS and Academy Accreditation data. A source audit found
those systems are login-gated, have no public API or bulk export, and include data about
minors. The project therefore does **not** scrape or approximate AIFF CRS/CMS records.

The v1 public-data funnel is now:

1. Public sports infrastructure investment
2. Youth population denominator from Census 2011
3. Khelo India participation / medal-tally participation proxies
4. Competitive outcomes such as medals and verified tournament results

This changes the outcome from "player retention to professional/national-team status" to
"public investment and facility exposure as predictors of participation and competitive
outcomes." The regression and simulation machinery remains structurally similar, but the
grain is state/district-year aggregate data rather than individual player records.

The README headline is intentionally marked in progress until the new public-source pipeline
runs against live data.gov.in and Census inputs with a user-provided API key.
