# Deployment status

Last reviewed: 25 October 2026

## Current release scope

The live Vercel deployment is an early-stage **public-source discovery MVP**, not a complete Gĩkũyũ corpus.

Implemented in the frontend:
- Public-source search against Kikuyu Wikipedia, Kikuyu Wiktionary and English Wikipedia.
- Source detail pages link to original publishers and show a rights reminder.
- Device-local saved-reference list (browser local storage; no account sync).
- Clear about, privacy and source-concern pages; responsive navigation and custom not-found page.
- Same-origin API routes with input validation, source-host allow-listing, outbound request timeouts and short-lived caching.
- Health endpoint at `/api/health`.
- GitHub Actions uses a committed lockfile and `npm ci`; workflow permissions are read-only.

## Not production-enabled

- Persistent archive database or object storage.
- Account registration, sign-in or role-based access control.
- Audio recording/upload, community transcript submission, review queues or moderation.
- Private takedown intake, audit log and formal removal workflow.
- Curated, licence-verified CSV/JSONL exports.
- Scheduled crawlers, production alerts, backup/recovery testing or full end-to-end tests against provisioned services.

The Python FastAPI service under `backend/` is not connected to the Vercel deployment. It expects configured services and secrets (database, Redis, S3-compatible storage, Meilisearch and secret settings). No production credentials or paid services were created during this work.

## Rights and privacy

- Public-source discovery does not mean that a page is free to reuse or approved for AI training.
- Review each original page's licence and terms before reuse.
- The site does not accept audio submissions in this release.
- Saved references stay in the visitor's browser local storage and can be lost when site data is cleared.
- The source-concern page does not claim that a private removal request has been received or actioned.
- Do not add credentials to source control.

## Security and dependencies

- Next.js is pinned to 15.5.28 and React to 19.0.9.
- The last previously verified dependency audit reported three moderate advisories in the Tailwind/PostCSS selector-parsing dependency chain and no high or critical findings. Recheck audit output on the latest CI run before making a current security claim.
- The CI workflow was hardened to read-only repository permissions and now uses the committed lockfile with `npm ci`; it no longer commits files back to the main branch.

## Verification

Previously verified:
- GitHub Actions run `40229105184` passed 15 backend tests, frontend typecheck, lint, production build and local production-mode API smoke tests.
- Vercel production deployment `dpl_38AMyttQE9Q1tht8DiSnb69qpGT1` reached `READY` for commit `80c7ab76d6179bf059def23e199441fa11a3d252`.

Those checks predate the latest UI, policy-page and CI changes. The new commit must pass CI and Vercel deployment before the updated release can be considered verified. Direct public-site HTTP checks have not been independently run from this environment, whose outbound network access is restricted.
