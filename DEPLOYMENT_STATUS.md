# Deployment status

Last reviewed: 25 October 2026

## What is currently implemented

- Next.js frontend deployed through the connected Vercel project.
- Same-origin API routes for health, public-source search, and reference-page details.
- Public-source discovery queries Wikimedia sites (Kikuyu Wikipedia, Kikuyu Wiktionary, and English Wikipedia) and links results to their original pages.
- Source responses are cached briefly and outbound requests have timeouts.
- Search input is validated server-side and source hosts are allow-listed when resolving a result ID.
- Health endpoint: `/api/health`.
- Uploads and dataset exports return explicit service-unavailable responses rather than pretending to save or export data.
- A committed `frontend/package-lock.json` now pins the frontend dependency tree; Vercel's install command has been changed to `npm ci` for reproducible installs.

## What is not yet production-enabled

- Persistent database for archive records, accounts, transcripts, takedowns, and audit logs.
- Persistent object storage for contributed audio.
- Production authentication and role-based access control.
- Community recording upload and transcription workflows.
- Curated, licence-verified CSV/JSONL exports.
- Scheduled crawling, monitoring alerts, and end-to-end tests against provisioned services.

The Python FastAPI service in `backend/` is not connected to this Vercel deployment. Its existing configuration expects database, Redis, S3-compatible storage, Meilisearch, and secret settings. No production values for those services were configured during this review.

## Important rights and privacy rules

- Public-source search is discovery, not a claim that material is free to reuse or approved for AI training.
- Users should check each original source's licence and terms before reuse.
- The deployed contribution page does not record or upload audio.
- Do not add real credentials to the repository. Configure secrets only in the relevant hosting provider.
- Do not claim the project is a complete archive until persistence, authentication, deletion/takedown handling, and upload tests have been verified.

## Security and dependency status

- Next.js is pinned to the patched 15.5.28 release and React to 19.0.9.
- The CI audit currently reports three moderate advisories in the Tailwind/PostCSS selector-parsing dependency chain. The project pins the patched `postcss-selector-parser` 6.x backport at 6.1.5; the audit database still reports the advisory against that major-version range. No high or critical findings were reported by the CI audit for the committed lockfile.
- A larger Tailwind 4 migration has not been undertaken solely to silence advisory metadata because it would be a breaking CSS/configuration change; the pinned backport is used instead.

## Verification status

- GitHub Actions run `40228931646` passed backend tests, frontend typecheck, lint, production build, and API smoke tests. That run generated and tested the exact lockfile subsequently committed as `e93937daf1395ca09e2d3b8e0f0f917fdf614b53`.
- The Vercel production deployment for that lockfile commit reached `READY`.
- Vercel's install command has since been changed to `npm ci`. A follow-up deployment is being triggered by this documentation update so the install-command change can be verified from the build logs.
- The external production API was not independently requested from this environment because outbound network access is unavailable here. The API routes were smoke-tested against a local production-mode Next.js server in CI.
