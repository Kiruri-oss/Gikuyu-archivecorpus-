# Deployment and product status

Last reviewed: 25 October 2026

## Product objective

Build the largest practical Gĩkũyũ language library and grow the underlying platform into a major African language library. The long-term product includes persistent language profiles, texts, oral recordings, transcripts, translations, annotations, reviewer workflows and permissioned datasets for language research and AI.

## Current web release

The latest code adds an initial directory of 20 African language profiles and language-aware public-reference search. It searches the selected language's Wikipedia and English Wikipedia; the Kikuyu search also checks Kikuyu Wiktionary. Search results remain third-party references and are not records stored by this project. Coverage varies by source and language.

Other web features include device-local saved references, source detail pages, About/Privacy/Source Concerns pages, same-origin API routes with input validation and outbound timeouts, and a health endpoint.

## Not yet enabled in the deployed frontend

- Persistent archive database and private object storage.
- Contributor accounts, access control and identity lifecycle.
- Audio uploads and storage, text contribution forms, time-aligned transcription and annotation workflows.
- Review queues, private takedown intake and auditable moderation.
- Licence-aware CSV/JSONL corpus exports and dataset cards.
- Production backups, restore tests, monitoring and full end-to-end testing against provisioned services.

The Python FastAPI backend contains groundwork for authentication, media upload, transcript segments, reviewer verification and exports but is not connected to Vercel. It expects database, Redis, S3-compatible storage, Meilisearch and secret configuration. Do not claim community contributions are being stored by the current live site.

## Rights and data governance

Public-source discovery does not grant redistribution or AI-training rights. Each record in the future corpus should carry source provenance, licence, consent/use permissions, language/dialect metadata and review state. Sensitive community knowledge requires an access policy; user data must be deletable; commercial or AI-training use must be explicit in contributor terms.

## Security and dependencies

- Frontend uses a committed lockfile and `npm ci`.
- GitHub Actions repository permissions are read-only.
- The latest previously observed dependency audit reported three moderate advisories in the Tailwind/PostCSS selector-parsing dependency chain. Re-run the audit before making a current claim.
- No production secrets or paid services were created as part of this work.

## Verification

Previously, the project passed backend unit tests, frontend typecheck/lint/build and local production-mode API smoke tests. That earlier run predates the latest multilingual directory changes. The Vercel deployments for the new commits were still queued/pending at the time of this update, so the new multilingual release must not be considered verified until the latest build and CI results are checked.

Direct public-site HTTP testing is restricted from the current environment. A successful deployment build alone does not verify every live route or external Wikimedia endpoint.
