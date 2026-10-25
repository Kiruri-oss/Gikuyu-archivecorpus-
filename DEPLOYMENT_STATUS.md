# Deployment and product status

Last reviewed: 26 October 2026

## Product objective

Build the largest practical Gĩkũyũ (Kikuyu, ISO 639-3: kik) language library. This product is exclusively for Gĩkũyũ. Material in other languages is outside the corpus scope. The core product is a corpus: texts, oral recordings, transcripts, translations, annotations, reviewed sources and permissioned research datasets—not a search wrapper.

## Current live release

The deployed frontend currently provides Gĩkũyũ-focused public-reference discovery, source detail pages, device-local saved references, and project/privacy/source-concern information. Search results point to their original publishers; they are not records stored by this project.

The orthography suggestion API and web UI are merged into the repository, but are not confirmed live because Vercel rejected the deployment associated with the latest merge due to its build-rate limit. Do not assume the public site includes those latest changes until a new deployment reaches READY.

## Implemented in the repository, not yet production-connected

- A scheduled FastAPI corpus hunter that traverses configured Gĩkũyũ discovery seeds, obeys robots.txt, enforces a per-host delay, bounds page size and redirects, rejects obvious private/local URL targets, and extracts detected Gĩkũyũ from publicly reachable pages whether or not a machine-readable licence is present. Missing licence metadata is recorded as unknown and never grants downstream reuse permission. The default catalogue includes Gĩkũyũ Wikimedia sources plus targeted discovery pages at Internet Archive, Open Library, Project Gutenberg, Library of Congress and Wikimedia Commons; each crawl is capped at 500 pages and scheduled every six hours when the backend runs in production.
- The Hunter follows relevant cross-domain links under host and page budgets. Gĩkũyũ text with unknown licence metadata is still archived and labelled unknown; AI-training, commercial and researcher-export permissions remain false unless supported by explicit metadata.
- Detected Gĩkũyũ records are stored in the source/text models with source URL, detected licence or unknown status, discovery time, language confidence and separate reuse flags. Under the notice-and-takedown model, the archive record is publicly searchable; unknown rights do not qualify for downstream reuse exports.
- Source and content deduplication, configurable seed hosts and permission-aware research exports.
- CSV export selects the source row correctly and includes source URL, discovery time and licence URL; JSONL exports preserve the same provenance.
- A conservative orthography suggestion API and web tool for a small initial set of spellings such as `mucii → mũciĩ`. Suggestions are not silently applied or saved and must be confirmed by fluent speakers.
- A curated Gĩkũyũ source catalogue registers dataset metadata as pending; it does not download gated datasets or bypass access controls.

The licence detector recognises supported explicit declarations such as CC0, CC BY 3.0/4.0, dedicated public-domain declarations and explicit Kenya Open Data terms. Other, missing or ambiguous declarations remain recorded as unknown for reuse. The crawler's archive collection is not blocked merely because a machine-readable licence is absent.

## Additional implementation in the current repository

- The Hunter's default seed catalogue now includes targeted Gĩkũyũ discovery entry points at the Gĩkũyũ Wikimedia projects, Internet Archive, Open Library, Project Gutenberg, Library of Congress, Wikimedia Commons and Wikidata. It is configured for a maximum of 500 pages per crawl every six hours, with a one-second minimum delay between requests to the same host. This is code configuration only; no production crawl has been verified.
- Gĩkũyũ detection now relies on distinctive orthography and vocabulary rather than generic syllables such as “na”, with regression tests for Gĩkũyũ, Kiswahili, English and ambiguous short text.
- Text contribution validation rejects non-Gĩkũyũ language codes. Audio contribution requires both an explicit Gĩkũyũ-language declaration and speaker-consent confirmation; the backend stores the consent declaration and timestamp in source metadata.
- Contributor sign-in/registration pages, text/audio submission forms, a takedown request form, and a researcher portal have been added. They deliberately disable submission/export when the frontend has no configured backend URL.
- Research exports now support a CC0-only filter in addition to approved records whose permissions match the selected research, AI-training or commercial purpose.
- Search is prepared to show archived text, audio and transcript results when the frontend API URL points to the backend. Without that setting, it remains in public-reference discovery mode.

- The transcription workspace now supports audio playback, time-aligned Gĩkũyũ transcript segments, translations, corrections restricted to the recording contributor or reviewers, and linguistic annotations (transcription, translation, lemma, part of speech, morphology, tone, IPA, dialect and quality).
- Reviewer/admin interfaces are available in the repository for pending Hunter sources and takedown requests. The public takedown intake immediately hides a matching approved source while the request is queued; an administrator action removes matching indexed records and stored media/text where applicable.
- The homepage now has a daily proverb/riddle slot backed only by approved corpus records and a pseudonymous contributor leaderboard based on approved public contributions. Neither fabricates entries when the backend is absent.
- PWA files have been added: install manifest, icon, service-worker registration, static-shell caching and an offline fallback that can display device-local saved-reference titles. Live offline behaviour has not yet been tested on a phone.
These changes have been committed to the repository, but the new checks have not yet been confirmed green. The latest combined GitHub status only reports Vercel's build-rate-limit failure; the production site has not been verified to include these changes.

## Still not production-enabled

- The FastAPI service is not connected to the Vercel frontend.
- Persistent production database, private object storage, and configured search dependencies are not provisioned for the live deployment.
- Contributor accounts, secure audio uploads, consent recording, time-aligned transcription/annotation UI and moderation workflows are not connected to a production archive.
- Production backups, restore tests, alerts and full end-to-end tests against provisioned services remain outstanding.

The crawler has not been run against a production database. No community submission should be described as stored until the backend and persistent services are deployed and tested. No paid service or production credential was created.

## Rights and data governance

Each record retains source provenance, detected licence evidence, discovery time, dialect metadata and rights state. Unknown rights are never silently treated as permission for AI training, commercial use or researcher redistribution. Audio contributions require explicit rights and speaker-consent declarations. The backend takedown action hides the source, removes stored text/media records and attempts to purge search-index/object-store entries while retaining the request for audit. The live site is not yet connected to the production backend, so no timed removal guarantee is currently claimed.

## Security and dependencies

- Frontend uses a committed lockfile and `npm ci`.
- GitHub Actions repository permissions are read-only.
- The latest previously observed dependency audit reported three moderate advisories in the Tailwind/PostCSS selector-parsing dependency chain. Re-run the audit before making a current claim.
- The crawler enforces robots.txt even if the legacy configuration flag is disabled.
- No production secrets or paid services were created as part of this work.

## Verification and deployment

- Earlier GitHub Actions run [40233670075](https://github.com/Kiruri-oss/Gikuyu-archivecorpus-/actions/runs/40233670075) passed frontend typecheck, lint, production build and smoke tests plus 36 backend tests, but it predates the latest feature work.
- GitHub Actions run [40238363152](https://github.com/Kiruri-oss/Gikuyu-archivecorpus-/actions/runs/40238363152) passed the backend test job. Its frontend job failed at TypeScript checking because the PWA layout imported a missing `ServiceWorkerRegister` component; that component has since been added.
- The latest observed frontend run passed typecheck but failed lint on an unescaped apostrophe in the researcher page. That text and its sign-in route were corrected on main after the failed run. The backend test job passed again, including source-visibility and takedown regression tests. A fresh CI run after the researcher-page fix is still required.
- Vercel's status remains a failure with a build-rate-limit restriction. The latest source code is not confirmed deployed.
- No production crawl, live contribution submission, real object-storage deletion, phone-offline session or full end-to-end production workflow has been verified from this environment. Direct public-site HTTP testing is restricted here.

A successful backend test job does not prove that the current frontend builds, that the latest code is deployed, or that external source services are reachable. Do not describe the project as production-ready until a current full CI run and a verified deployment succeed.
