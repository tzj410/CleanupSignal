# Analyst delivery and customer operations

## Before first sale

Set a CleanupSignal reply address owned by the operator; do not reuse ArgoSphere branding or credentials. Identify the legal seller, invoice information, and locally applicable business/tax obligations before accepting payment. Those business decisions remain for the owner; no entity registration or paid service has been performed.

Store private customer information outside this public GitHub repository. Copy `customer-tracker-template.csv` into a private owner-controlled location before entering data. Never commit contact addresses, payment status, tailoring notes, or customer reports here.

## Weekly fulfillment SOP

1. Review the latest source-health status and the last successful collection time. If a source failed, disclose reduced coverage. A successful HTTP check does not establish a new procurement status.
2. Match service and geography to the customer's agreed profile. Keep funding signals separate from solicitations. Exclude expired or archived bids from the actionable section.
3. Open each shortlisted official source. Verify buyer/recipient, location, scope, date, deadline and time zone, amendments, notice type, and set-aside requirements. Consult the original procurement portal and attachments before calling a notice actionable.
4. Record the official ID and exact URL. Use “unknown” for absent data. Do not estimate a deadline or turn grant funding into a contractor budget.
5. Add a concise relevance explanation and next step. Label analyst interpretation. Use at most 5–10 relevant items; report “no newly verified matches” when appropriate.
6. Produce a dated report. Check source links, duplicate IDs, classification, material changes since last report, and correct customer profile. Review rendered HTML and exported CSV.
7. Deliver only to an explicitly authorized customer address through an owner-approved channel. The repository automation generates public sample files; it does not send customer emails or invoices.
8. Log delivery privately, note corrections, and ask which items were useful. Recheck imminent deadlines before any follow-up.

## Report release gate

- All items traceable to official records with retrieval/check dates.
- Title and status reflect source notice type; awards, sources-sought and funding selections are not open solicitations.
- Every open bid has a still-future, sourced deadline, or a conspicuous “deadline not confirmed—verify” note. Date-only deadlines are not interpreted as midnight without evidence.
- Values describe their units and meaning. Combined program totals are not summed again with their component grants.
- Old records retain original dates. A failed fetch never relabels old evidence as newly verified.
- No secrets, customer information, unsupported claims, duplicated leads, or broken links.
- If no new items exist, say so; never fabricate a fresh lead to fill space.

## Draft pilot terms for owner review

This is proposed operational wording, not a legally approved contract. Complete seller identity and contact details before presenting it.

CleanupSignal supplies public-source research for business development. The proposed pilot costs $99 for one agreed monthly period and includes one manually reviewed report each week, limited to the customer's agreed services and MD/VA/DC geography. The report can include early funding signals, which do not establish a procurement opportunity. Public information may change, be incomplete, or be withdrawn. Customers must independently verify requirements and deadlines and remain responsible for bids and compliance. No contract award or exclusive access is guaranteed.

Start and end dates, delivery address, scope, and price must be accepted in writing before invoicing. No automatic renewal or card authorization. Send a renewal offer before the end date; renew only after affirmative acceptance. Customers may cancel future renewal at any time through the confirmed reply address. If CleanupSignal fails to deliver an agreed report and cannot promptly cure the failure, offer an appropriate refund for the undelivered portion. Record any separately agreed refund arrangement in writing.

## Privacy and retention draft

The static public dashboard requires no account and collects no payment credentials. Host access logs may be processed by the hosting provider. Browser bookmarks/preferences, if enabled, stay on the device. Customer correspondence is handled separately by the operator; request only a business contact, service/geographic profile, and delivery preferences. Do not request passwords, tax identifiers, banking details, private bid files, or sensitive personal information through the site.

Use customer details only for agreed delivery, billing administration, and support. Restrict access to the owner and expressly authorized staff. Delete unnecessary prospect notes after 90 days; delete canceled-customer tailoring details after 90 days unless needed for an active issue. Retain financial records only as required by applicable obligations, separately and securely. Honor contact suppression requests; keep the minimum suppression record required to avoid contacting the person again. No advertising trackers or resale of customer data.

## Billing boundary

Billing is not integrated. No payment account, paid subscription, transaction, invoice send, or charge has been initiated. Payment processors may charge transaction fees even without a monthly plan, so enabling one would require a new owner decision. The owner can first agree a manual invoice and payment method with each pilot; do not publish bank details or collect cards in this repository.

### Collector speed and freshness

Procurement collection uses up to four independent source workers. Each source retains its existing bounded detail requests, backoff and conservative failure status. `collectionDurationMs` measures a successful scan; it is not publication-to-discovery latency. The hourly schedule is unchanged and does not guarantee immediate detection.

`source-health.json` reports per-source evidence age, expected interval, freshness and scan duration. Hourly sources become overdue after three hours without a success; daily sources after 49 hours. Dataset generation alone cannot reset source evidence age. Missing timestamps do not count as successful evidence. The independent incident monitor includes overdue source checks.

After reporting completes on main, the deploy workflow tests the latest main tree, preserves a release bundle and publishes if a scoped Pages token exists. This avoids relying on a push event from the reporting workflow's built-in GitHub token. If the token is absent, the workflow explicitly reports that publishing was skipped. The public live-data endpoint remains the fallback for fresh data independently of static redeployment.
