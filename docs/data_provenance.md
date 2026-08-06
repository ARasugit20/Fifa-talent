# Data Provenance

## Primary manual official inputs (iff-reproduce)

These sources power the default reproduction pipeline. Each file must exist locally with a
verified sibling `.provenance.json` (SHA-256, source URLs, retrieval timestamp).

| Dataset | Organization | Source page | Geographic grain | Retrieval | Limitations |
|---|---|---|---|---|---|
| MD-SD state-wise project progress | Sports Authority of India / MD-SD | https://mdsd.kheloindia.gov.in/state-wise-progress | state_ut | Manual official download | Beta dashboard; no automated scraping. Reporting period from provenance metadata. |
| MD-SD grantee amounts sanctioned/released | Sports Authority of India / MD-SD | https://mdsd.kheloindia.gov.in/gratee-type-wise-progress | state_ut | Manual official download | Monetary `source_unit` must be documented (`crore` or `inr`). |
| Khelo India state/UT financial assistance | Ministry of Youth Affairs and Sports | https://www.data.gov.in/resource/stateuts-wise-details-financial-assistance-provided-under-khelo-india-scheme-and-national | state_ut | Manual official download | Use the exact resource/download URL in provenance; do not invent resource IDs. |
| Census 2011 state/UT denominator | Registrar General & Census Commissioner | https://www.data.gov.in/catalog/primary-census-abstract-2011-india-and-states-0 | state_ut | Manual official download | Denominator definition is explicit per row; 2011 vintage flagged stale when paired with later years. |

Full inventory: [data_inventory.md](data_inventory.md).

## Optional national-context sources

| Source | URL | Use |
|---|---|---|
| Ministry annual reports | https://yas.nic.in/documents/annual-reports | Programme context / national total cross-check |
| Ministry budget / DDG documents | https://yas.nic.in/documents/budgets | National investment context |
| Khelo India operational guidelines | https://yas.nic.in/sports/khelo-india-national-programme-development-sports-0 | Scheme definitions |

## Legacy / optional API clients (not used by default reproduce)

| Source | URL | Access method | Notes |
|---|---|---|---|
| data.gov.in Khelo India medal tally | https://www.data.gov.in/ | `datagovindia` + `DATAGOVINDIA_API_KEY` | Legacy client; CI mocks API calls |
| data.gov.in Department of Sports budget | https://www.data.gov.in/ | `datagovindia` package | Legacy optional ingestion |
| Census API / tables | https://censusindia.gov.in/ | `census_client.py` | Not used by manual primary reproduce path |

## Unavailable / quarantined sources

| Source | Status | Reason |
|---|---|---|
| AIFF CRS/CMS / Academy Accreditation | Not used | Login-gated; no public API; minor-data risk |
| dashboard.kheloindia.gov.in live exports | Not scraped | Operator must supply downloaded artifacts |
| Kaggle ISL dataset | Blocked pending license verification | `isl_data.py` enforces license metadata |

## PDF / report ingestion (unchanged)

| Source | URL | Module |
|---|---|---|
| FIFA Global Talent Development India report | https://inside.fifa.com/official-documents | `fifa_afc_reports.py` |
| AFC technical reports | https://assets.the-afc.com/downloads/technical-reports/ | `fifa_afc_reports.py` |

## Output traceability

Processed infrastructure rows and `data/results/run_manifest.json` include:

- Source filename(s) and source page URL
- `retrieved_at_utc` from provenance
- `provenance_sha256` for each contributing raw file
- Explicit caveat: state/UT public sports infrastructure descriptive analytics; not football-specific

## Provenance JSON fields

Each raw file requires a sibling `<filename>.provenance.json` with:

| Field | Purpose |
|---|---|
| `dataset_name` | Human-readable dataset label |
| `organization` | Publishing organization |
| `source_page_url` | Official reference page used for the download |
| `download_url` | Exact download URL or `manual_official_download` |
| `retrieved_at_utc` | When the operator retrieved the file |
| `source_published_or_updated_at` | Source publication or update date |
| `geographic_grain` | Must be `state_ut` or `national` |
| `time_coverage` | Reporting period covered by the file |
| `license_or_terms_note` | License/terms summary |
| `retrieval_method` | Use `manual_official_download` for operator-supplied files |
| `sha256` | SHA-256 digest of the raw file bytes |
| `notes` | Optional operator notes |

Use `iff-provenance init|hash|verify <file>` to scaffold and validate these records locally.
