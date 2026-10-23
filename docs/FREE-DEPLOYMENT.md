# Free-only launch and SAM handoff

Checked October 23, 2026. These are deployment instructions, not evidence that a deployment or account connection has occurred.

## Cost boundary

| Component | Initial operating choice | Charge prevention |
| --- | --- | --- |
| Site | Static files on Cloudflare Pages Free, using its provided subdomain | Keep Free; no Workers Functions, paid add-ons or domain purchase. |
| Refresh/report | Standard GitHub-hosted Linux Actions for this public repository | Keep repository public; no larger runners or paid execution products. |
| Government sources | Public EPA pages; optional SAM public API | No purchased data feeds; bounded requests and fail on throttling. |
| Storage | Versioned public source data and generated public sample reports | No customer data or credentials in git. |
| Customer delivery | Owner-reviewed reports and approved manual business correspondence | No paid mail provider, automatic sends, or enrichment subscriptions. |
| Billing | Not integrated | Do not activate a processor or incur transaction fees without owner instruction. |

Recurring infrastructure target is $0, not a promise that future plan terms cannot change. Check account billing settings before enabling a service; stop rather than upgrade when a free limit is reached. No custom domain, paid AI, database, scraping vendor, or payment subscription is needed for this pilot. Human review requires owner time.

## Cloudflare Pages static deployment

1. In a Free Cloudflare account, open Workers & Pages → Create application → Pages → Connect to Git.
2. Authorize only `tzj410/CleanupSignal`. Do not grant or alter ArgoSphere repository access.
3. Select the reviewed production branch. Set framework to None, leave build command blank, use repository root, and output directory `public`.
4. Deploy on the provided `pages.dev` subdomain. Record URL and commit. Check dashboard, filters, source links, report downloads, and narrow-screen view.
5. Keep the deployment static. Do not add Functions or buy a domain. Git pushes can trigger future deployments; confirm automated data commits produce a fresh site. Check failure logs if the report date does not advance.

This is an alternative manual deployment path if the main project is delivered through Sites. Do not create duplicate hosting projects unnecessarily.

Official references: [Git integration](https://developers.cloudflare.com/pages/get-started/git-integration/), [Free limits](https://developers.cloudflare.com/pages/platform/limits/), [Static asset pricing](https://developers.cloudflare.com/pages/functions/pricing/). Pages documents a Free allowance of 500 builds/month; one scheduled update daily plus development should fit if the account's other projects do not consume the allowance.

## Optional SAM.gov source activation

The feed must show SAM as unconfigured until a successful authorized request. EPA-only collection remains usable without a SAM key.

1. Sign into a personal account on [SAM.gov](https://sam.gov/). Open Profile → Account Details and request/view the Public API Key. GSA says viewing it requires account-password confirmation. Complete authentication yourself; do not send passwords or the key in chat.
2. In **CleanupSignal only**, open GitHub Settings → Secrets and variables → Actions → New repository secret. Name it `SAM_API_KEY`; enter the key as the secret value.
3. Run the repository's refresh workflow manually. Check source-health output; confirm at least one successful API response and any imported notices against SAM. A valid empty result can mean no matches, not failure.
4. If credentials fail or rate limits apply, leave the source unavailable; do not relabel seed records as current SAM data. Rotate any exposed key and remove it from logs/history.

The documented production endpoint is `https://api.sam.gov/opportunities/v2/search`. GSA requires a key, date filters and pagination; daily request limits depend on account role. See [official Get Opportunities API](https://open.gsa.gov/api/get-opportunities-public-api/). Keep credentials only in the job environment, never in browser JavaScript, report links, URLs printed in logs, or committed files.

## First customer activation

Owner tasks: confirm a CleanupSignal reply address and seller identity, review the pilot scope/terms, keep the customer tracker private, and select an authorized delivery and manual billing method. The public site is not a payment gate. Do not claim three paid customers until payment and accepted scopes are recorded. No customer outreach or charging has occurred.

GitHub reference: [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions). Standard hosted runners in public repositories are free; larger runners are not. Avoid storing Actions artifacts/caches unnecessarily, since storage has separate billing considerations. This kit uses versioned small public report files rather than customer-report artifact storage.
