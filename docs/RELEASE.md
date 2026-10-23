# Release status — October 23, 2026

## Milestones

| Milestone | State | Evidence / remaining work |
| --- | --- | --- |
| Isolated CleanupSignal implementation | Released to GitHub main | Published to `tzj410/CleanupSignal` after explicit owner approval. No ArgoSphere changes. |
| Ten verified government project signals | Complete | Two EPA releases and EPA FY26 selection-list PDF. 10 funding selections, $15,690,876; no claimed open bids. |
| Working intelligence website and sample briefing | Built and verified; see the delivery message for deployment status | Filters, search, project evidence dialog, local watchlist, CSV/Markdown exports and printable report. |
| Automated evidence refresh/report generation | Active; first hosted run passed | Daily 11:17 UTC public-runner workflow. First run completed October 23, 2026; EPA source checks, tests, dataset validation and refreshed report commit passed. |
| Federal procurement discovery | Adapter implemented, disconnected | Operator must place free SAM key in repository Actions secret. No key in chat or source. |
| Public customer site | Not launched | Owner-only Sites review version; optional Cloudflare Pages Free public hosting guide provided. |
| First customer preparation | Drafts ready | 20 researched firms, $99/month pilot, onboarding and fulfillment SOP. Actual outreach, seller/contact setup and billing are not activated. |
| Three paid customers / $297 MRR | Not achieved | Commercial target, never a completed claim. |

## Verification

Story: scheduled government evidence checks produce a validated public dataset and reports; the website loads that dataset, filters it, opens source-linked evidence, saves a browser-local watchlist, and exports a customer-ready draft.

- Ten Python tests pass: EPA evidence matching, unknown or expired SAM deadlines, location/type filters, conservative unconfirmed status, source failure retention, incomplete pagination, schema validation and output escaping.
- Four JavaScript tests pass: combined filters and empty DC state, expired/unverified bid status, CSV formula protection and source URL/HTML safety.
- Browser confirmed ten rendered records, exact $15.69M display, MD + Cleanup filtering to one Annapolis record, evidence dialog with exact amount and no invented deadline, saved watchlist persistence after reload.
- Live EPA refresh succeeded. Optional live SAM integration is not verified without key.
- Responsive CSS includes mobile layouts; browser verification used desktop viewport only.
- First hosted GitHub workflow passed: [run #1](https://github.com/tzj410/CleanupSignal/actions/runs/40004682558). Public customer sign-up, payment, authenticated private reports and email delivery are not implemented.

## Release decision

The owner explicitly approved publication to main and activation of free daily reporting on October 23, 2026. The repository was initialized and the tested implementation released through the connected GitHub API. The first run successfully committed refreshed reports at 18:36:52 UTC.

Next operator inputs are the free SAM.gov API key as an Actions secret and a customer-facing CleanupSignal contact address. Public customer launch, outreach and billing remain separate from this private review release.
