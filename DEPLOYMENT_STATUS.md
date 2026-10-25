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

## Verification status

The new public-source API was added in commit `a86d68575a87053d9d7c8c22d2df7945c8236391`. At the time of this note, Vercel's production build was still running and GitHub Actions frontend and backend checks were in progress. A green result must be confirmed from those systems before the change is considered verified.
