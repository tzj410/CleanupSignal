# State/local procurement and operating desk

## Collection contract

`data/procurement.json` registers two HTML listing collectors and three manual portal references. `scripts/operations.py` checks the public Annapolis and Danville boards, deduplicates bid IDs, filters relevant environmental titles, and fetches at most ten relevant detail pages per board. An explicit empty listing is required to confirm zero listings; an unknown layout fails closed. A failed or missing source record cannot remain a verified open invitation. Administrative postings, responder lists, bid tabs, award intents and conflicting source labels are never classified as open bids. Local municipal dates are interpreted in America/New_York, including daylight saving transitions. Review official amendments before acting.

The eMMA and eVA gateways are reference links, not connected statewide feeds. eVA's Open Data page describes historical data: https://eva.virginia.gov/eva-open-data.html . Anne Arundel's current county page points to Harbor for opportunities after July 6, 2026: https://www.aacounty.org/central-services/purchasing/doing-business-county . No portal accounts or paid data services were created.

## Research provenance

- Annapolis public listing: https://www.annapolis.gov/bids.aspx — first scan explicitly showed no open postings.
- Danville public listing: https://www.danville-va.gov/bids.asp — four relevant administrative records imported, none promoted to open bids.
- Example conflict: https://www.danville-va.gov/bids.aspx?bidID=4232 — the page labels status Open but category Responders - Closed and describes a responders list. CleanupSignal suppresses open status and its ambiguous response deadline.
- Annapolis funding context: https://www.annapolis.gov/m/newsflash/Home/Detail/2166 — identifies 932/937 Spa Road and prior involvement of Haley & Aldrich. This is not proof of an exclusive award or available scope.
- Martinsville program context: https://www.martinsville-va.gov/377/Brownfields — includes older site-status material, not a FY2026 procurement schedule. Department contact directory: https://www.martinsville-va.gov/m/directory/department?did=42 .

All ten EPA records have a research plan in `data/followups.json`. Only Annapolis and Martinsville have additional project/program findings in this update; the other records contain unresolved questions and statewide portal references. No project owners were contacted.

## Reporting and monitoring

Every live pipeline run compares against the previous published dataset. New IDs and changes to business fields are counted; a changed verification timestamp alone is not a project update. The initial editorial follow-up enrichment is excluded from project-change counts. The comparison is the latest run, not a rolling historical archive. Approaching deadlines only include verified open notices within seven days and are evaluated when the page opens.

Daily operations shows source failures, last attempts, last successful local scans and manual-only sources. Dataset age is evaluated in the browser; more than 48 hours triggers an overdue warning. The GitHub job summary runs even if an earlier step fails, and labels its dataset timestamp. It may therefore describe retained data from the last successful write. There is no automatic email alert delivery. Existing 11:17 UTC reporting schedule remains unchanged.

Private contractor stages, notes and reminder dates stay in localStorage and local exports. They are never written into the public repository or shared reports. Reminder dates do not schedule notifications. Public reports contain the editorial research context only.

## Validation

18 Python and 5 JavaScript tests pass. Tests cover failed-vs-empty listings, duplicate links, irrelevant assessment titles, administrative conflicts, expired deadlines, timezone transitions, prior-record downgrades and meaningful change comparisons. Desktop browser verified the operating desk and saved local follow-up notes after reload. Broader state feeds, mobile browser verification, private team sync and email alerts remain outside this release.


## October 24 expansion

The registry now includes six CivicPlus municipal/county boards and a D.C. public API collector, plus the three manual portal references. `scripts/dc_procurement.py` uses the public search API exposed by the OCP portal at `https://contracts.ocp.dc.gov/solicitations/search`, confirms its open-status filter, deduplicates solicitation IDs, then independently retrieves matching notice details. It checks schema, exact IDs, status and Eastern closing times. The feed does not cover all independent District agencies.

Live D.C. details verified:

- https://contracts.ocp.dc.gov/solicitations/details?id=Doc841623 — parkland stormwater retrofits, November 24, 2026, 2 p.m. Eastern.
- https://contracts.ocp.dc.gov/solicitations/details?id=Doc846899 — leaf disposal, October 27, 2026, 2 p.m. Eastern; portal market is Set Aside, so eligibility must be reviewed.
- https://contracts.ocp.dc.gov/solicitations/details?id=Doc852234 — stormwater-retention credits, October 28, 2026, 2 p.m. Eastern.
- https://www.lynchburgva.gov/bids.aspx?bidID=249 — CSO 70 sewer improvements, December 8, 2026, 3 p.m. Eastern. The public notice also lists a November 3 pre-bid meeting; review the official documents for whether attendance is mandatory.

The CivicPlus parser now handles omitted closing `td` tags. Previously, it could misread the following heading as a description or deadline and conservatively leave a valid invitation unconfirmed. Tests cover this real markup case.

Maryland eMMA presented a browser-check/CAPTCHA to this collector; eVA's linked public VBO endpoint returned HTTP 403. No bypass was attempted and neither is reported as an automated statewide feed. New municipal sources are not a substitute for statewide coverage. Municipal-only pages reporting no open notices do not prove no opportunities exist elsewhere in those jurisdictions.

SAM now performs one national query per NAICS 541620/562910 and filters returned place-of-performance to MD/VA/DC. Typical first-page request count drops from six to two, with a hard ten-request pagination budget. Failed and cooldown-period SAM records cannot remain verified open. Authentication and rate-limit recovery must be confirmed by a hosted refresh that can access the existing secret.

At this release: 18 records, 4 verified open bids, 10 funding signals, and 4 unconfirmed administrative records. Source failures retain the old evidence date and downgrade open status; timestamp refreshes alone are not treated as new procurement activity.


### Hosted verification update — October 24, 2026, 6:09 p.m. Eastern

The main-branch refresh authenticated to SAM.gov successfully using the reduced-request collector. It added two federal notices, both closed, so the current dataset is 20 records with 4 verified open solicitations. Source status is verified. Earlier statements that SAM recovery still needed confirmation are superseded by this result. The new Pages deployment workflow completed its checks but skipped automatic publishing because the scoped deployment token is missing; this release was published by direct upload.
