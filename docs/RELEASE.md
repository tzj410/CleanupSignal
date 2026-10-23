# Release status — October 23, 2026

## Milestones

| Milestone | State | Evidence / remaining work |
| --- | --- | --- |
| Isolated CleanupSignal implementation | Built locally | Only the empty `tzj410/CleanupSignal` repository was cloned. No ArgoSphere changes. |
| Ten verified government project signals | Complete | Two EPA releases and EPA FY26 selection-list PDF. 10 funding selections, $15,690,876; no claimed open bids. |
| Working intelligence website and sample briefing | Built and verified; see the delivery message for deployment status | Filters, search, project evidence dialog, local watchlist, CSV/Markdown exports and printable report. |
| Automated evidence refresh/report generation | Implemented; activation pending | Daily workflow prepared; GitHub repository is empty. Main bootstrap requires release approval after automatic review rejected direct default-branch push. |
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
- Hosted GitHub workflow has not run. Public customer sign-up, payment, authenticated private reports and email delivery are not implemented.

## Release decision

The first `main` commit and activation of the daily public-runner workflow are the specific next approval. There is no existing main history or pull-request base in the empty GitHub repository. The terminal cannot authenticate to GitHub; use the connected GitHub API after release approval to initialize main, then put reviewed implementation changes through a branch/PR. Do not bypass the rejected default-branch push.
