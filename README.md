# CleanupSignal

Environmental project intelligence for Maryland, Virginia and Washington, DC. A dependency-free static website, government evidence refresh pipeline, downloadable briefings, and founding-customer pilot kit.

## Current release

- Ten EPA FY2026 brownfield **funding selections**, $15,690,876 total (2 Maryland, 8 Virginia). These are not open bids, confirmed contract budgets or guaranteed work.
- Search, service/jurisdiction/status filters, sorting, source details, local watchlist, CSV and personalized Markdown brief export.
- Source-health desk and browser-printable briefing. No paid API, database, AI model, account or payment service.
- Daily GitHub Actions workflow active on `main` in public `tzj410/CleanupSignal`, scheduled for 11:17 UTC (7:17 a.m. EDT / 6:17 a.m. EST). It will not run while the repository is private. The first hosted run passed on October 23, 2026: tests, live EPA verification, data validation and refreshed report commit all succeeded.
- SAM.gov adapter prepared, **not connected**: add a free `SAM_API_KEY` repository secret. EPA refresh checks registered releases; discovering new releases still requires editorial onboarding.
- Twenty researched prospect firms and a proposed $99/month one-month pilot. No outreach, customer enrollment, billing or subscription has occurred.

## Run and verify

Serve `public/` with any static HTTP server (Python 3 example):

```sh
python3 -m http.server 8000 --directory public
```

Open http://localhost:8000. There are no dependencies to install. Node 20+ and Python 3.11+ are sufficient for checks:

```sh
node --test tests/ui-core.test.js
node --check public/app.js
node --check public/report.js
python3 -m unittest discover -s tests -v
python3 scripts/pipeline.py --check
python3 scripts/pipeline.py --offline
```

Live refresh (bounded public EPA requests and optional SAM requests):

```sh
python3 scripts/pipeline.py
```

The UI loads the newest valid dataset between its bundled snapshot and `tzj410/CleanupSignal/main/public/data/signals.json` on GitHub. This allows the hosted review version to receive daily data after main is activated, without separate site deployments. If GitHub is unavailable it retains the bundled snapshot and shows its date, with an overdue warning after 48 hours. The HTML report uses the same loader; downloadable Markdown and CSV are generated from the displayed dataset. Static exports in `public/reports/` represent their stamped generation time.

## Deployment and operations

- [Source register and limitations](data/SOURCES.md)
- [Free-only deployment and SAM setup](docs/FREE-DEPLOYMENT.md)
- [Pilot offer and customer readiness](docs/PILOT-LAUNCH.md)
- [Manual fulfillment and corrections SOP](docs/OPERATIONS.md)
- [20 researched prospects](docs/PROSPECTS.md)
- [Release status and verification](docs/RELEASE.md)

`public/` can deploy directly to Cloudflare Pages Free, framework None, no build command. Its `_headers` declares security headers. Sites uses `python3 scripts/build_site.py` to copy `public/` into its supported `dist/` output directory. No existing ArgoSphere repository or service is used.

## Privacy and commercial limits

All records and reports in this repository are public government information. Watchlists stay in the browser, are not authenticated or synced, and are not a paid-content gate. The pilot form prepares an email to the owner-provided contact address, cleanupsignal@gmail.com, with a local download fallback. Visitors review and send the email themselves; the site does not transmit inquiries to a backend or start subscriptions. Confirmed seller identity, reviewed service terms, delivery channel and a manually authorized invoicing process are needed before taking paying customers. Keep actual customer details outside this public repository, in a private tracker. Never commit credentials or customer reports.

This is a working evidence-backed MVP, not comprehensive procurement coverage. DC is not populated yet; no customer pipeline or revenue is claimed. Do not label funding selections as open solicitations or available contractor funds. Review official amendments, dates and contractor status before every customer brief.
