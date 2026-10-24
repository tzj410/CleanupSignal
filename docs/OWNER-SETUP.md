# Remaining owner inputs — CleanupSignal

Sign-up/login, Stripe setup and customer pilot work are deliberately deferred. This file contains no credentials or personal seller information.

## Email delivery

No sending domain, Resend credentials or controlled test inbox are configured for CleanupSignal. The separate ArgoSphere domain and credentials must not be reused without instruction.

1. Choose a CleanupSignal domain you own and verify it with Resend. Publish only the DNS records that provider supplies; verify SPF/DKIM and configure DMARC for that domain.
2. Add `RESEND_API_KEY`, `EMAIL_FROM`, and `RESEND_WEBHOOK_SECRET` as Cloudflare Pages production secrets. Webhook URL: `https://cleanupsignal.pages.dev/api/email/webhook`; subscribe to delivered, bounced, complained, delivery_delayed and failed events.
3. Configure the existing automation token in Pages and the matching GitHub Actions secret. Do not put any key into this document or chat.
4. With a controlled, explicitly opted-in recipient, verify delivery, bounce/complaint suppression, unsubscribe and deadline delivery. Do not count mocked-provider tests as a live delivery pass.
5. Paid entitlement and verified-user checks remain in place. Deferring accounts and billing also defers customer enrollment in the paid email service.

Implemented: formatted HTML/text, matching, deadline reminders, source-age guards, leased retry queue, provider idempotency, signed event verification, complaint/bounce suppression, delivery-event audit history and retention. No customer emails were sent in this release.

## Automatic publishing

The Pages project currently uses direct uploads. A scoped deployment credential is absent from GitHub Actions, and the connected GitHub tool cannot set repository secrets. Existing automatic data collection operates independently of this missing code-deployment credential.

Create a Cloudflare API token scoped to this account's Pages edit permission and save it as the GitHub Actions repository secret `CLOUDFLARE_API_TOKEN`. Account ID is already configured. Then run **Deploy CleanupSignal to Pages** and verify its final publish stage. The workflow currently identifies missing activation explicitly; a green build with a skipped publish is not an automatic deployment pass. Release artifacts contain only public assets and are retained for seven days. Customer data, database dumps and secrets must never be uploaded as workflow artifacts.

Maintenance Worker changes are deployed separately; its D1 binding and daily cron are documented in `workers/maintenance.jsonc`. The worker is not exposed on workers.dev.

## Seller and legal information

Before paid launch, the owner must provide the legal seller name, business contact/address appropriate for publication, applicable registrations/tax treatment, and approved renewal/cancellation/refund policies. No identity, legal registration, tax status or refund promise has been invented. The current terms describe the free research and support service and label proposed subscriptions as unavailable.

## Statewide procurement access

- eMMA: public route returns a browser-check challenge. A sanctioned export/feed or portal-approved integration is needed; no challenge is bypassed.
- eVA: the government-linked public opportunity endpoint returns HTTP 403. A permitted public feed or approved API is needed.
- Anne Arundel/Harbor: official county link redirects to an Oracle application shell. No readable notice listing was confirmed. It remains a manual source.

These are access/coverage limitations. Additional municipal collectors do not replace statewide coverage. Official bid documents always control.
