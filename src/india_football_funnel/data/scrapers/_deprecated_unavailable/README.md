# Deprecated Unavailable AIFF Scrapers

This folder is reserved for old or proposed AIFF-dependent scrapers such as:

- `aiff_youth_scraper.py`
- `isl_academy_scraper.py`
- `aiff_national_team_scraper.py`

They are not implemented or used in v1.

The source audit found AIFF CRS/CMS and Academy Accreditation systems are login-gated,
have no public API or bulk export, and are not legally scrapable. Much of the underlying
registration data concerns minors, so automated scraping would be inappropriate even if
technically possible.

The project now uses only verified public sources: Census 2011, data.gov.in Khelo India
resources, official Khelo India/YAS documents, and traceable FIFA/AFC PDF reports.
