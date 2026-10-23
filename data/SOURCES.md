# CleanupSignal source register

## Verified initial edition

10 records were checked against two EPA releases on October 23, 2026:

- [Maryland selections](https://www.epa.gov/newsreleases/epa-announces-55-million-brownfields-grants-revitalize-communities-maryland): 2 records, published June 24, 2026.
- [Virginia selections](https://www.epa.gov/newsreleases/epa-announces-over-101-million-brownfields-grants-revitalize-communities-virginia): 8 records, published June 24, 2026.

Amounts are EPA-selected grant amounts, **not** contractor budgets, available bid values or proof of executed grant awards. EPA states awards follow legal and administrative requirements. No bid deadlines were inferred. Agency fields identify grant recipients. Next steps are CleanupSignal editorial recommendations. Localities are display context; validate the exact service area with each recipient.

The initial edition has no verified DC records and no open federal solicitation records. Zero records must never be represented as zero market activity.

## Collection contract

`python3 scripts/pipeline.py` checks the two registered EPA pages and regenerates the report. Recipient and amount evidence must match nearby page text. Missing evidence is flagged `needs-review`. A network failure retains existing records and their old verification dates with a `stale` flag. A successful page check confirms published evidence, not present procurement status. New EPA releases must be reviewed and added to `data/seed.json`; discovery of new EPA releases is not automated in this edition.

`python3 scripts/pipeline.py --offline` regenerates outputs without refreshing evidence. `--check` validates the current dataset. `python3 -m unittest discover -s tests -v` runs offline checks.

## Optional SAM.gov federal discovery

[Official API documentation](https://open.gsa.gov/api/get-opportunities-public-api/).

A free public API key from the operator's SAM.gov account is required. Set the repository Actions secret `SAM_API_KEY`; never place it in public files, browser JavaScript, command arguments or reports. Without a key the source panel says `needs-key`. Collection runs server-side and never logs keyed request URLs. No paid API or AI service is used.

The adapter searches the last 90 days in MD/VA/DC, up to five 1,000-record pages per state. It filters solicitation types and environmental NAICS/title terms; award notices are excluded. Unknown or timezone-less deadlines cannot become an `open-solicitation` record. Unknown deadlines, missing notices, unavailable source checks and unknown active flags use the distinct `unconfirmed` status. `closed` requires a passed verified deadline or an explicit inactive flag. Missing records or failed collection are not allowed to remain advertised as open. Always follow the government link for amendments and current status.

This bounded keyword/NAICS feed is incomplete by design. A truncated page, quota or network error fails the source check and retains old records with a stale flag. No confidential contacts, attachments or customer data are collected.

## Reporting and free operations

The scheduled GitHub workflow runs daily at 11:17 UTC on public-repository standard Linux runners. GitHub schedules can be delayed or disabled; inspect Actions and the dashboard timestamps. It is restricted to this repository and requires the repository to remain public. It uses Python's standard library and GitHub's public Actions allowance; no paid services or billing configuration.

Outputs: `public/data/signals.json`, `public/reports/latest.html`, `public/reports/latest.md`, `public/reports/signals.csv`. The HTML brief is printable and links original sources. CSV cells are protected against spreadsheet formula execution; report HTML is escaped. Reports are generated for download, with no automatic email delivery or customer messages.

Secondary evidence: [EPA FY2026 selected-applications PDF, page 4](https://www.epa.gov/system/files/documents/2026-06/fy26-mac-rlf-supp-funding-selections.pdf#page=4), independently inspected October 23, 2026. This PDF is a static secondary reference, not re-fetched by the daily HTML evidence adapter. Records carry `fundingStage: selected` and `amountBasis` explicitly; do not label them awarded.
