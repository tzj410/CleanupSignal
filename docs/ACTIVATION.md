# Activate the company service

This release implements the backend, but provider-dependent capabilities must not be counted as operational until their live checks pass. It has not created paid subscriptions or sent customer emails.

## Current state (October 24, 2026)

- Public bid center and reports work without an account.
- Cloudflare D1 `cleanupsignal-accounts` is provisioned and schema applied. This is separate from ArgoSphere.
- Pages Worker handles `/api/*`. Workspace data is never placed in public JSON or GitHub.
- Supabase authentication is implemented but **not configured**. Only the unrelated ArgoSphere project was connected; it was not modified or reused.
- Stripe checkout, portal, signature-verified webhooks, provider-state reconciliation and paid access checks are implemented but **not configured**. `BILLING_ENABLED=false`.
- Per-user email consent, daily/weekly matching, 3-day deadline reminders, queue leases, retry limits, provider idempotency, source-freshness guards and unsubscribe are implemented but **not activated**.
- Company invitations use private links copied by the owner; invitations are not automatically emailed.
- Privacy and service-policy pages explain the current service. Commercial seller identity and final renewal/cancellation/refund policy still require completion before paid launch.

## 1. Authentication (managed Supabase Auth)

Create/select a **separate CleanupSignal Supabase project** in the user's chosen organization. Confirm its cost before accepting any nonzero charges. The existing `global-atlas-insight` project belongs to ArgoSphere and must remain untouched.

Set these Pages server variables:

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY` (public/publishable key, never service-role)

In Supabase Auth, enable email sign-in and email confirmation; disable anonymous sign-ins. Set Site URL to `https://cleanupsignal.pages.dev/account.html` and allow that exact redirect. If testing previews, explicitly allow only the actual preview redirect. The frontend exchanges the default email-link fragment for secure HttpOnly cookies and clears the fragment. For code entry, include `{{ .Token }}` in the email template. Configure a production-capable SMTP sender and rate/abuse protection before opening public registration. Supabase's default development sender is not production email delivery.

Passwordless email also serves account recovery; no password database or password-reset secret is maintained by CleanupSignal. Validate sign-up, verification, returning login, expired link, refresh, logout and recovery with a controlled test inbox before opening registration.

## 2. Database and deployment

Schema: `migrations/0001_accounts.sql`. It is idempotent for initial provisioning; use a new additive migration for later changes. All API queries bind parameters. D1 SQL triggers enforce membership and pending-invitation seats atomically. The company owner retains access after downgrade; excess members are suspended until removed or the plan is increased. Do not attach the production customer database to untrusted preview code after real customers enroll; create an isolated preview database then.

Build: `python3 scripts/build_worker.py`. The generated `public/_worker.js` is committed for direct uploads. Keep `_routes.json` (API routes), `_headers`, all static assets and the Worker in each Pages deployment. `wrangler.jsonc` describes the Pages binding. Never deploy only the static files after activating accounts.

## 3. Stripe

Complete the seller's Stripe onboarding outside this repository. Create six recurring USD Prices:

| Plan | Monthly | Annual | Company seats |
|---|---:|---:|---:|
| Starter | $19 | $190 | 1 |
| Team | $29 | $290 | 3 |
| Business | $49 | $490 | 8 |

Server variables: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and JSON `STRIPE_PRICES` mapping `starter_monthly`, `starter_yearly`, `team_monthly`, `team_yearly`, `business_monthly`, `business_yearly` to real `price_...` IDs. Prices are an allowlist; clients cannot choose arbitrary prices, customer IDs or company IDs. Enable Stripe Customer Portal cancellation and payment-method updates. Plan changes should take effect at the renewal boundary; avoid prorated immediate downgrades that leave excessive seats. Confirm seller details, commercial policies and prices, then test checkout, retries, duplicate events, failure, cancellation and both plan changes before setting `BILLING_ENABLED=true`.

Webhook: `https://cleanupsignal.pages.dev/api/billing/webhook`. Subscribe to `checkout.session.completed`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`. API version pinned in `server/billing.js` is `2025-06-30.basil`. Match the webhook endpoint version and verify in test mode. Renewal entitlements use current subscription state and a future paid-through period, never the checkout return URL. Paid access expires if provider events stop. Replay a current subscription event after restoring the endpoint to reconcile missed renewals.

A per-company checkout reservation prevents opening multiple concurrent subscriptions. A failed provider call retains the reservation for up to 30 minutes, preventing duplicate creation under uncertain network outcomes. No card information touches CleanupSignal.

## 4. Opted-in email delivery

Set `RESEND_API_KEY` and `EMAIL_FROM` for a sender domain verified with the delivery provider. Set a cryptographically random `AUTOMATION_TOKEN` in Pages and the same value in GitHub secret `CLEANUPSIGNAL_AUTOMATION_TOKEN`. Do not paste keys in source, public forms or chat.

`.github/workflows/alerts.yml` invokes the bounded queue twice daily. It skips delivery when no secret is configured. Each user chooses daily/weekly or off. Alerts are paid-plan-only; only verified open notices checked within 48 hours are eligible. No new matches means no digest. The worker rereads the latest dataset before sending and cancels withdrawn/expired notices. Weekly digests wait at least seven days since the user's last successful digest.

Provider idempotency keys prevent duplicate sends during retries within the provider's 24-hour window. Queue items stop retrying before that window ends (23 hours), after at most four attempts. Investigate failed items; do not blindly replay older items with the same key. A company member who has unsubscribed must not be opted back in by an owner. Source-health failures remain in the existing GitHub job summary. Email-failure history appears in the signed-in workspace; `job_runs` stores automation failures. External operator paging is still to be configured.

## 5. Launch checks still required

- Test two actual controlled accounts across companies, 1/3/8-seat limits and revoked-member access.
- Test monthly/yearly payment flows in Stripe test mode, including cancellation, renewal failure and portal changes.
- Verify real email delivery, unsubscribe and recovery; add SPF/DKIM/DMARC through the sender provider.
- Run mobile Chrome and Safari QA. The environment could not install its local browser binaries; deployed Chrome inspection was used. No Safari pass is claimed.
- Exercise D1 backup/recovery and manual deletion/support requests. Establish retention periods and a support process.
- Complete seller identity, final commercial terms, business records and conversion analytics.
- Increase verified Maryland and Virginia bid coverage; eMMA's browser check and eVA's 403 still block direct automated ingestion. SAM authentication and ingestion succeeded in the October 24 hosted refresh; continue monitoring quota use and source health.

## Sources used for implementation

- Cloudflare D1: https://developers.cloudflare.com/d1/worker-api/d1-database/
- Cloudflare Pages advanced Worker: https://developers.cloudflare.com/pages/functions/advanced-mode/
- Supabase Auth API: https://github.com/supabase/auth/blob/master/openapi.yaml
- Supabase email authentication: https://supabase.com/docs/guides/auth/auth-email-passwordless
- Stripe webhooks: https://docs.stripe.com/events/manage-webhook-endpoints
- SAM API: https://open.gsa.gov/api/get-opportunities-public-api/


### Hosted verification update — October 24, 2026, 6:09 p.m. Eastern

The main-branch refresh authenticated to SAM.gov successfully using the reduced-request collector. It added two federal notices, both closed, so the current dataset is 20 records with 4 verified open solicitations. Source status is verified. Earlier statements that SAM recovery still needed confirmation are superseded by this result. The new Pages deployment workflow completed its checks but skipped automatic publishing because the scoped deployment token is missing; this release was published by direct upload.


## Current user scope: defer sign-up/login and Stripe

The latest user instruction defers authentication and Stripe setup. Public briefing, support and source status are usable without them. The formatted email template and safer delivery queue are implemented, but subscriber sending remains off: it still needs a verified sender, provider API key and the deferred account/paid entitlement infrastructure. No account-free subscription list or anonymous bulk-email endpoint was added.

A real public matched briefing is now available at `/briefing.html`; this supersedes the earlier image-only email design preview. Source-failure monitoring and an editorial correction-hold process are operational in the code. D1 bookmark availability and an isolated schema restore were verified; production customer-data restoration was not performed.

## Operational release update — October 24, 2026

Read `OWNER-SETUP.md` for the remaining external inputs. Online private support is implemented and enabled for production after migration `0002_operations.sql`; sign-up/login and billing remain disabled. Signed Resend events and bounce/complaint suppression are implemented; live email sending is still unavailable without the owner’s domain/provider setup. Maintenance retention is deployed separately as a daily Worker. GitHub source incidents are maintained by an independent hourly workflow. A full-data synthetic recovery drill passes; no production restore was performed. Automated code publication still awaits the scoped GitHub Actions deployment secret.

The earlier note claiming Safari could not be tested is superseded by the prior release's 20 successful desktop/mobile Chromium and WebKit scenarios. This release adds new support/evidence scenarios, with its actual hosted result recorded in the PR.
