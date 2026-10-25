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
- The latest observed dependency audit reported three moderate advisories in the Tailwind/PostCSS selector-parsing dependency chain. No high or critical findings were reported in that audit; re-run the audit before making a current security claim.
- The CI workflow was hardened to read-only repository permissions and now uses the committed lockfile with `npm ci`; it no longer commits files back to the main branch.
- Vercel still reports some deprecated transitive build-tool packages. These warnings do not by themselves indicate a failed build, but should be addressed during dependency maintenance.

## Verification

- Vercel production deployment `dpl_3qiaMkNyVFwop3f3GNrBJRjP2ewv` reached `READY` for commit `965f90f8c37658cae77d0a096b4245edd9708efc`.
- Its build logs confirm `npm ci`, successful Next.js compilation, lint/type validation and static generation of 19/19 pages.
- GitHub Actions run `40229105184` previously passed 15 backend tests, frontend typecheck, lint, production build and local production-mode API smoke tests. That run predates the latest UI and CI changes, so it is not evidence that the complete current branch passed every CI job.
- The public site's HTTP responses have not been independently verified from this environment because direct external requests are restricted. A successful Vercel build is not proof that every live route or third-party search is reachable from every network.
