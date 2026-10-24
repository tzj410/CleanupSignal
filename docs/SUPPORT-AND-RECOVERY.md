# Support, correction and recovery process

Customer registration and Stripe activation are deferred at the user's request. No business identity, tax registration or commercial policy is invented by this release.

## Public support

`/support.html` prepares an email to `cleanupsignal@gmail.com` or downloads a text request. The requester must review and send it. It does not collect server-side tickets, automatically notify staff or promise a response time. Do not publish an unattended “ticket received” claim. Requests arriving in the mailbox require an operator to review them.

Triage into: data correction; source outage/missing coverage; website/accessibility; privacy/correction/deletion; general question. Keep requester addresses and correspondence outside GitHub and public datasets. A private tracker can record date, request category, relevant public record ID, owner, investigation and resolution. Do not include credentials, payment details or identification documents.

## Incorrect deadline or bid status

1. Open the government notice and amendments. Procurement-authority instructions control, not CleanupSignal's summary.
2. If a published open status cannot be substantiated, prepare an editorial hold:

```sh
python3 scripts/review_record.py --hold RECORD_ID --reason 'Closing date requires amendment review' --review-after YYYY-MM-DD
```

The reason is PUBLIC; never include requester identity. Commit the reviewed `data/reviews.json`, refresh reports and deploy. A hold forces unconfirmed/needs-review status and survives successful automatic collection. It cannot promote a notice to open. The review date is a follow-up target, not an automatic release date.
3. Fix source parsing when necessary and add a representative parser test. Retain official evidence/provenance, including whether only a government listing or full notice was checked.
4. Once resolved, remove the hold with `--resolve RECORD_ID`, refresh from the official source, validate and deploy. Removing a hold alone is not evidence of an open solicitation.
5. Reply to the requester through the mailbox with the outcome and official link. No messages were sent during implementation.

## Privacy requests

Verify the requester's relationship to the requested data using the original support email/account email when accounts become active. Do not request identity documents through the public form. Browser-only profiles/notes can be cleared by the visitor in browser site-data settings. Shared company records require ownership review; do not delete other members' company data simply because one person asks.

When accounts are activated, use an authorized private operation to remove the applicable database/auth records after verifying scope. Revoke active sessions first. Check provider records and backups separately. Record completion privately. Public policy pages describe the current prototype; legal seller details, formal retention periods and final commercial cancellation/refund terms must be finalized before paid launch.

## Monitoring

`/status.html` evaluates the newest valid dataset on page load. `public/data/source-health.json` stores the scheduled public aggregate report and a capped daily history. It includes no customer data. Manual references are not counted as integrated sources. An empty or stale feed is not proof that a region has no bids.

`python3 scripts/check_health.py` exits unsuccessfully for overdue data or a total automatic-source outage. Partial failures remain visible without hiding successful sources. The reporting workflow writes its health summary and commits retained/degraded source state before the critical check. GitHub's owner notifications depend on the owner's notification settings; no automatic operator email/paging is claimed.

## D1 recovery

On October 24, 2026, the Cloudflare API returned an available Time Travel bookmark for CleanupSignal's D1 database. A schema-only export was downloaded privately and restored into an isolated local SQLite database; all 13 application tables, including company, membership and delivery tables, were present. **No production restore was performed, and this does not test recovery of future customer data.**

Cloudflare's supported recovery tools:

- Bookmark: `GET /accounts/{account_id}/d1/database/{database_id}/time_travel/bookmark`.
- Export: `POST .../export` with `output_format: polling`; poll the returned bookmark when necessary, then download the signed export URL privately.
- Restore: `POST .../time_travel/restore`. Read the current API schema and available recovery window before a real restore. Record a current bookmark/export first and verify which writes will be lost.

Never place SQL dumps, signed export URLs, email payloads or customer backups in this public repository or public GitHub workflow artifacts. `.customer-data/` is gitignored for local recovery exercises; it is not a production backup destination. Keep real backups encrypted in an owner-controlled private location. Do not run a destructive recovery as part of a routine health check.

Before real customers enroll, rehearse a full data export/import in a separate non-production database, verify row counts and membership isolation, and document the recovery point and recovery time. A code rollback does not restore the database.

Source: https://developers.cloudflare.com/d1/reference/time-travel/ and https://developers.cloudflare.com/d1/best-practices/import-export-data/

## Operations release — October 24, 2026

This supersedes the draft-only support description above. `/support` now offers an online private request queue in D1, in addition to the existing mail draft and text-download fallbacks. Submission requires contact email and description, same-origin JSON, an enabled server configuration, and trusted Cloudflare IP metadata. Salted hourly IP keys enforce five requests per IP per hour; a transactional insert caps the entire service at 200 requests daily. The public API has no support-list or ticket-read endpoint. A random reference identifies a successful save; no email acknowledgement or response time is promised.

Operators review `support_requests` through the authenticated Cloudflare D1 console. Use parameterized SQL in a private session to select pending requests and update `status` to `investigating` or `resolved`, setting `updated_at=unixepoch()`. Do not copy requester addresses/messages into public issues. Respond through the support mailbox after investigation; technical storage is not a promise that every request is already resolved.

`cleanupsignal-maintenance` is deployed with a daily `31 7 * * *` UTC cron, a private D1 binding and no public route. It removes open requests after 90 days and resolved requests 30 days after their last update, cleans operational retention records, and writes a private publication-freshness check. The schedule was configured, and the maintenance logic is covered by a database test; the first scheduled execution is not claimed until observed.

The independent hourly `monitor.yml` workflow opens one public `source-monitor` issue per failed collector or dataset older than three hours, and closes it after recovery. Only public source metadata is included. GitHub controls whether the owner receives email/push notifications. Direct email paging remains unconfigured.

A **full** export of the existing production database (13 application tables, zero rows at export time) was restored to isolated SQLite successfully. Separately, `scripts/recovery_drill.py` exported and restored all 17 application tables with eight synthetic company/member/preference/watchlist/support/delivery rows. Full table checksums, foreign keys and restored seat triggers passed. This is a pre-enrollment rehearsal, not a restore of live customer data. Production was never rolled back. Cloudflare Time Travel remains the provider backup mechanism; an encrypted off-account customer backup destination has not been selected.

Run `python3 scripts/recovery_drill.py --private-export PRIVATE_SQL_PATH` for a private export rehearsal. Never commit a dump or place it under `public/`. Recovery point for an actual incident must be selected from available provider bookmarks; this rehearsal does not establish a production recovery-time SLA.
