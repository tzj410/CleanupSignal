# Cloudflare deployment — October 23, 2026

Live website: https://cleanupsignal.pages.dev/

- Provider: Cloudflare Pages, static direct upload, no Functions.
- Project: `cleanupsignal` (`0a1810e4-4707-4489-9c5d-4df58b609e66`).
- Account: `3e68527f84aebe29967932d28ad2a2b4`.
- Production deployment: `a7f77e21-2fad-43b3-b562-731588f61d5e`.
- Deployed source: `tzj410/CleanupSignal` commit `96d54b04f3fa47f2f214d3474269cbe431e91a5b`, `public/`.
- Cloudflare reported deployment success at 19:36:48 UTC.
- Free static hosting only; no paid upgrade, purchased domain, database or paid service was added.

## Updates

The daily GitHub Actions evidence refresh remains active. The dashboard and printable report select the latest valid dataset from the bundled snapshot and public GitHub main, so data updates do not require a Pages code deployment. Bundled static report files retain their stamped generation date.

Automatic code deployments are not configured. Creating a Git-connected Pages project returned HTTP 401 with a Cloudflare Git installation error. This release uses direct upload instead. A future GitHub integration must authorize only CleanupSignal; no ArgoSphere repository may be modified. Until then, changed website code needs another direct upload.

## Verification

The public dashboard rendered ten records, $15.69M in announced funding selections and zero verified open solicitations. The pilot inquiry page displays cleanupsignal@gmail.com, the proposed $99/month pilot, an email-draft button and download fallback. No inquiry was sent. Cloudflare confirms `uses_functions: false`.

The shell environment could not independently fetch the public Pages URL (HTTP 403); the cloud browser loaded it successfully. Browser verification used a desktop viewport.

## Remaining launch work

SAM.gov remains rate limited; its configured secret has not yet been authenticated successfully. Seller identity, agreed service terms, delivery arrangements and a manually authorized invoicing process remain necessary before accepting paying customers. No customer outreach, enrollment or billing has occurred.
