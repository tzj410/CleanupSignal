# Cloudflare deployment

Website: https://cleanupsignal.pages.dev/

Project `cleanupsignal`, account `3e68527f84aebe29967932d28ad2a2b4`. Existing static-only deployments remain available in deployment history.

## October 24 account-capable build

- Static public assets plus `public/_worker.js` and `_routes.json` for `/api/*`.
- D1 binding `DB`: `cleanupsignal-accounts`, ID `2ca28e18-0a14-4421-8dc5-0b8ca7f07065`.
- Initial schema is in `migrations/0001_accounts.sql` and has been applied to that separate CleanupSignal database.
- Authentication, Stripe and email variables are not supplied. Billing is disabled. The public site stays usable and company sign-in reports pending setup.
- Pages production and preview use fail-closed behavior for Function failures.

## Repeatable direct upload

Set `CLOUDFLARE_ACCOUNT_ID` and a scoped `CLOUDFLARE_API_TOKEN` in a protected deployment environment. Do not commit tokens. Then:

```sh
python3 scripts/build_worker.py
npm run check && npm test
python3 -m unittest discover -s tests -v
python3 scripts/deploy_pages.py --branch main
```

The script obtains a temporary upload token, uploads changed assets, and includes the API Worker, routes and security headers in the deployment. It prints the deployment URL and ID without credentials. Creating a deployment is not proof it succeeded: verify the final deploy stage, rendered public pages, `/api/config` and the account availability message.

`.github/workflows/deploy.yml` uses this same build/upload process after relevant main pushes, including data updates. It explicitly skips publishing if the Cloudflare token is missing. Automatic deployment is **not activated** merely by adding this workflow.

## Rollback

In the Cloudflare Pages project's deployment list, select the preceding known-good production deployment and use Rollback. Keep the recorded deployment ID for each release. Rolling back files does not roll back D1 schema or customer data. Initial migrations are additive; later changes must preserve compatibility with the preceding Worker so rollback remains possible. Never delete or recreate the customer database to roll back application code.

Before customers enroll, isolate preview data from production, test D1 restoration, verify email and billing callbacks, and complete the checks in [ACTIVATION.md](ACTIVATION.md). Chrome rendered the deployed release preview; local Chromium/WebKit downloads were unavailable, so no mobile/Safari pass is claimed.

### Live data path

`/api/signals.json` is a public, read-only Pages endpoint available without D1, login or billing. It chooses the newer valid dataset between the deployed asset and the server-fetched main-branch JSON. The remote URL uses a five-minute cache bucket; the public API response has a short cache lifetime. Invalid/future-dated upstream data is rejected and the last deployed dataset remains available with its original timestamp. No customer information is included. This makes routine data publication independent of the still-pending automatic code-deployment credential.
