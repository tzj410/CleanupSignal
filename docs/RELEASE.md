# Release status — October 23, 2026

## Milestones

| Milestone | State | Evidence / remaining work |
| --- | --- | --- |
| Isolated CleanupSignal implementation | Released to GitHub main | Published to `tzj410/CleanupSignal` after explicit owner approval. No ArgoSphere changes. |
| Ten verified government project signals | Complete | Two EPA releases and EPA FY26 selection-list PDF. 10 funding selections, $15,690,876; no claimed open bids. |
| Working intelligence website and sample briefing | Live on Cloudflare Pages | Filters, search, project evidence dialog, local watchlist, CSV/Markdown exports and printable report. |
| Automated evidence refresh/report generation | Active; first hosted run passed | Daily 11:17 UTC public-runner workflow. First run completed October 23, 2026; EPA source checks, tests, dataset validation and refreshed report commit passed. |
| Federal procurement discovery | Secret configured; rate limited | Live SAM requests returned HTTP 429; 24-hour cooldown applied. Authentication remains unverified. |
| Public customer site | Live | https://cleanupsignal.pages.dev/ — static Pages deployment; see DEPLOYMENT.md. |
| First customer preparation | Drafts ready | 20 researched firms, $99/month pilot, onboarding and fulfillment SOP. Actual outreach, seller setup and billing are not activated. |
| Three paid customers / $297 MRR | Not achieved | Commercial target, never a completed claim. |

## Verification

Story: scheduled government evidence checks produce a validated public dataset and reports; the website loads that dataset, filters it, opens source-linked evidence, saves a browser-local watchlist, and exports a customer-ready draft.

- Eighteen Python tests pass: EPA evidence matching, unknown or expired SAM deadlines, location/type filters, conservative unconfirmed status, source failure retention, incomplete pagination, schema validation and output escaping.
- Five JavaScript tests pass: combined filters and empty DC state, expired/unverified bid status, CSV formula protection and source URL/HTML safety.
- Browser confirmed ten rendered records, exact $15.69M display, MD + Cleanup filtering to one Annapolis record, evidence dialog with exact amount and no invented deadline, saved watchlist persistence after reload.
- Live EPA refresh succeeded. SAM secret is configured; live authentication remains unverified because requests returned HTTP 429.
- Responsive CSS includes mobile layouts; browser verification used desktop viewport only.
- First hosted GitHub workflow passed: [run #1](https://github.com/tzj410/CleanupSignal/actions/runs/40004682558). Public customer sign-up, payment, authenticated private reports and email delivery are not implemented.

## Release decision

The owner explicitly approved publication to main and activation of free daily reporting on October 23, 2026. The repository was initialized and the tested implementation released through the connected GitHub API. The first run successfully committed refreshed reports at 18:36:52 UTC.

The owner provided cleanupsignal@gmail.com as the customer-facing contact address. Pilot inquiries open a prefilled email draft with a download fallback. The SAM secret is configured; live requests returned HTTP 429, so the collector applies a 24-hour cooldown and authentication remains unverified. The public website is live on Cloudflare Pages. Outreach, customer enrollment and billing have not started.

## Contractor discovery update

Added an original contractor-facing homepage, a service directory with three populated categories and nine clearly inactive coverage interests, browser-local geographic/service preferences, project matching, and Free versus proposed $99/month curated-pilot pricing. Jurisdiction selection carries into an inquiry without starting service or billing. Browser verified Maryland + Cleanup matching to one Annapolis record and pricing scope transfer. Existing source data, reporting pipeline, and ArgoSphere repositories are unchanged.

## State/local procurement and operating desk

Two bounded public bid-board collectors (Annapolis and Danville) now supplement EPA records. Annapolis explicitly showed no open postings at the first scan. Danville supplied four relevant administrative records; conflicting open/closed labels, bid tabs, notices of intent and a responders list remain unconfirmed rather than verified open solicitations. Current dataset: 14 records, 10 funding selections, zero verified open bids.

Added a state/local source directory with three manual gateway references (eMMA, eVA and Anne Arundel Harbor), daily comparisons that ignore verification-only updates, a source check ledger, visible source-failure and 48-hour dataset-age warnings, and GitHub job summaries. Added qualification research for Annapolis and Martinsville plus research questions/portal links for all ten funding selections. Browser-local follow-up stages and notes persist after reload and filter correctly. No outreach, reminder notifications or email alerting was activated.
