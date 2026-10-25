# Deployment and product status

Last reviewed: 25 October 2026

## Product objective

Build the largest practical Gĩkũyũ language library and grow the underlying platform into a major African language library. The core product is a corpus: texts, oral recordings, transcripts, translations, annotations, reviewed sources and permissioned research datasets—not a language-directory demo.

## Current public release

The deployed frontend currently offers Gĩkũyũ-focused public-reference discovery, source detail pages, device-local saved references, and project/privacy/source-concern information. Search results point to their original publishers; they are not records stored by this project. A small orthography suggestion tool is being added in the current engineering branch, but it is not live until that branch is merged and successfully deployed.

## Implemented in the repository, not yet production-connected

- A scheduled FastAPI corpus hunter that traverses only configured seed hosts, obeys robots.txt, bounds page size and redirects, rejects obvious private/local URL targets, and only extracts pages with explicit accepted open-licence evidence.
- Unlicensed pages may be used for link discovery only; their page text is not extracted into the archive.
- Eligible Gĩkũyũ candidates are stored in the existing source/text models as pending records with source URL, licence declaration, discovery time, language confidence and reuse flags. Human review is required before public listing.
- Source and content deduplication, configurable seed hosts and permission-aware research exports.
- CSV export now selects the source row correctly and includes source URL, discovery time and licence URL; JSONL exports preserve the same provenance.
- A conservative orthography suggestion API and web tool for a small initial set of spellings such as `mucii → mũciĩ`. Suggestions are not silently applied or saved and must be confirmed by fluent speakers.

The hunter accepts explicit CC0, attribution-only CC BY 3.0/4.0, dedicated public-domain declarations and an explicit Kenya Open Data licence declaration. ShareAlike, NonCommercial, unknown and ambiguous licence evidence is not accepted for automatic ingestion. A site being governmental, old or publicly accessible is not by itself proof of reuse rights.

## Still not production-enabled

- The FastAPI service is not connected to the Vercel frontend.
- Persistent production database, private object storage, Redis and Meilisearch configuration are not provisioned for the live deployment.
- Contributor accounts, secure audio uploads, consent recording, time-aligned transcription/annotation UI and moderation workflows are not connected to a production archive.
- Production backups, restore tests, alerts and full end-to-end tests against provisioned services remain outstanding.

The crawler has not been run against a production database. No community submission should be described as stored until the backend and persistent services are deployed and tested. No paid service or production credential was created.

## Rights and data governance

Public-source discovery does not grant redistribution or AI-training rights. Every archived record must retain its source, licence evidence, attribution, discovery time, dialect metadata and review state. CC0/CC BY candidates carry the reuse flags implied by those licences but remain pending review; Kenya open-data candidates default to research-only until their terms are reviewed. Contributor recordings must have explicit permission and consent before ingestion. Takedown requests require an auditable, tested workflow before any removal-time guarantee is advertised.

## Security and dependencies

- Frontend uses a committed lockfile and `npm ci`.
- GitHub Actions repository permissions are read-only.
- The latest previously observed dependency audit reported three moderate advisories in the Tailwind/PostCSS selector-parsing dependency chain. Re-run the audit before making a current security claim.
- The crawler enforces robots.txt even if the legacy configuration flag is disabled.
- No production secrets or paid services were created as part of this work.

## Verification and deployment

The last completed branch run before the current merge-with-main check passed 36 backend tests, frontend typecheck, lint, production build and local production-mode API smoke tests. The current branch adds the orthography UI smoke test and is being checked again; consult GitHub Actions for the exact latest result.

Vercel has recently blocked deployment attempts due to its daily deployment-rate limit. The newest source commits are not confirmed deployed. A successful build is not proof that external Wikimedia search or every live route is reachable. Direct public-site HTTP testing is restricted from this environment.
