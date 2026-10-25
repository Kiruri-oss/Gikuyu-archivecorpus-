# Deployment and product status

Last reviewed: 25 October 2026

## Product objective

Build the largest practical Gĩkũyũ (Kikuyu, ISO 639-3: kik) language library. This product is exclusively for Gĩkũyũ. Material in other languages is outside the corpus scope. The core product is a corpus: texts, oral recordings, transcripts, translations, annotations, reviewed sources and permissioned research datasets—not a search wrapper.

## Current live release

The deployed frontend currently provides Gĩkũyũ-focused public-reference discovery, source detail pages, device-local saved references, and project/privacy/source-concern information. Search results point to their original publishers; they are not records stored by this project.

The orthography suggestion API and web UI are merged into the repository, but are not confirmed live because Vercel rejected the deployment associated with the latest merge due to its build-rate limit. Do not assume the public site includes those latest changes until a new deployment reaches READY.

## Implemented in the repository, not yet production-connected

- A scheduled FastAPI corpus hunter that traverses configured Gĩkũyũ discovery seeds, obeys robots.txt, enforces a per-host delay, bounds page size and redirects, rejects obvious private/local URL targets, and only extracts pages with explicit accepted open-licence evidence. The default catalogue includes Gĩkũyũ Wikimedia sources plus targeted discovery pages at Internet Archive, Open Library, Project Gutenberg, Library of Congress and Wikimedia Commons; each crawl is capped at 500 pages and scheduled every six hours when the backend runs in production.
- Unlicensed pages may be used for link discovery only; their page text is not extracted into the archive.
- Eligible Gĩkũyũ candidates are stored in the existing source/text models as pending records with source URL, licence declaration, discovery time, language confidence and reuse flags. Human review is required before public listing.
- Source and content deduplication, configurable seed hosts and permission-aware research exports.
- CSV export selects the source row correctly and includes source URL, discovery time and licence URL; JSONL exports preserve the same provenance.
- A conservative orthography suggestion API and web tool for a small initial set of spellings such as `mucii → mũciĩ`. Suggestions are not silently applied or saved and must be confirmed by fluent speakers.
- A curated Gĩkũyũ source catalogue registers dataset metadata as pending; it does not download gated datasets or bypass access controls.

The hunter accepts explicit CC0, attribution-only CC BY 3.0/4.0, dedicated public-domain declarations and an explicit Kenya Open Data licence declaration. ShareAlike, NonCommercial, unknown and ambiguous licence evidence is not accepted for automatic ingestion. A site being governmental, old or publicly accessible is not by itself proof of reuse rights.

## Additional implementation in the current repository

- The Hunter's default seed catalogue now includes targeted Gĩkũyũ discovery entry points at the Gĩkũyũ Wikimedia projects, Internet Archive, Open Library, Project Gutenberg, Library of Congress, Wikimedia Commons and Wikidata. It is configured for a maximum of 500 pages per crawl every six hours, with a one-second minimum delay between requests to the same host. This is code configuration only; no production crawl has been verified.
- Gĩkũyũ detection now relies on distinctive orthography and vocabulary rather than generic syllables such as “na”, with regression tests for Gĩkũyũ, Kiswahili, English and ambiguous short text.
- Text contribution validation rejects non-Gĩkũyũ language codes. Audio contribution requires both an explicit Gĩkũyũ-language declaration and speaker-consent confirmation; the backend stores the consent declaration and timestamp in source metadata.
- Contributor sign-in/registration pages, text/audio submission forms, a takedown request form, and a researcher portal have been added. They deliberately disable submission/export when the frontend has no configured backend URL.
- Research exports now support a CC0-only filter in addition to approved records whose permissions match the selected research, AI-training or commercial purpose.
- Search is prepared to show archived text, audio and transcript results when the frontend API URL points to the backend. Without that setting, it remains in public-reference discovery mode.

These changes have been committed to the repository, but the new checks have not yet been confirmed green. The latest combined GitHub status only reports Vercel's build-rate-limit failure; the production site has not been verified to include these changes.

## Still not production-enabled

- The FastAPI service is not connected to the Vercel frontend.
- Persistent production database, private object storage, and configured search dependencies are not provisioned for the live deployment.
- Contributor accounts, secure audio uploads, consent recording, time-aligned transcription/annotation UI and moderation workflows are not connected to a production archive.
- Production backups, restore tests, alerts and full end-to-end tests against provisioned services remain outstanding.

The crawler has not been run against a production database. No community submission should be described as stored until the backend and persistent services are deployed and tested. No paid service or production credential was created.

## Rights and data governance

Public-source discovery does not grant redistribution or AI-training rights. Every archived record must retain its source, licence evidence, attribution, discovery time, dialect metadata and review state. CC0/CC BY candidates carry the reuse flags implied by those licences but remain pending review; Kenya open-data candidates default to research-only until their terms are reviewed. Contributor recordings must have explicit permission and consent before ingestion. Takedown requests require an auditable, tested workflow before any removal-time guarantee is advertised.

## Security and dependencies

- Frontend uses a committed lockfile and `npm ci`.
- GitHub Actions repository permissions are read-only.
- The latest previously observed dependency audit reported three moderate advisories in the Tailwind/PostCSS selector-parsing dependency chain. Re-run the audit before making a current claim.
- The crawler enforces robots.txt even if the legacy configuration flag is disabled.
- No production secrets or paid services were created as part of this work.

## Verification and deployment

GitHub Actions run [40233670075](https://github.com/Kiruri-oss/Gikuyu-archivecorpus-/actions/runs/40233670075) passed the frontend typecheck, lint, production build and smoke tests plus 36 backend tests on the merge commit.

Vercel's status for the merge commit is currently a failure with a build-rate-limit restriction. The last live deployment therefore remains older than the latest source commit. A successful CI build is not proof that the latest code is deployed or that external Wikimedia search is reachable. Direct public-site HTTP testing is restricted from this environment.
