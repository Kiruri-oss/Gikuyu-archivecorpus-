# Deployment and product status

Last reviewed: 25 October 2026

## Product objective

Build the largest practical Gĩkũyũ (Kikuyu, ISO 639-3: kik) language library. This product is exclusively for Gĩkũyũ. Material in other languages is outside the corpus scope. The core product is a corpus: texts, oral recordings, transcripts, translations, annotations, reviewed sources and permissioned research datasets—not a search wrapper.

## Current live release

The deployed production frontend is still an older release: it provides Gĩkũyũ-focused public-reference discovery, source detail pages, device-local saved references, and project/privacy/source-concern information. New corpus features below are committed to main but are not considered live until Vercel deploys that commit and a real backend is connected.

The orthography suggestion API and web UI are merged into the repository, but are not confirmed live because Vercel rejected the deployment associated with the latest merge due to its build-rate limit. Do not assume the public site includes those latest changes until a new deployment reaches READY.

## Implemented in the repository, not yet production-connected

- A scheduled FastAPI corpus hunter that traverses configured Gĩkũyũ discovery seeds, obeys robots.txt, enforces per-origin delays, revalidates safe public DNS targets and robots.txt across redirects, and extracts bounded text from HTML, PDF and EPUB files. EPUB/PDF extraction has byte/page/member limits and preserves Gĩkũyũ diacritics. The Hunter archives detected Gĩkũyũ from publicly reachable pages whether or not a machine-readable licence is present; unknown licence metadata is recorded as unknown and never grants downstream reuse permission. Scheduled and manual runs are capped at 1,000 pages per batch, with a 100-host discovery limit and 50-page per-host limit, and run every six hours when the backend is connected.
- The Hunter follows relevant cross-domain links under host and page budgets. Gĩkũyũ text with unknown licence metadata is still archived and labelled unknown; AI-training, commercial and researcher-export permissions remain false unless supported by explicit metadata.
- Detected Gĩkũyũ records are stored in the source/text models with source URL, detected licence or unknown status, discovery time, language confidence and separate reuse flags. Under the notice-and-takedown model, the archive record is publicly searchable; unknown rights do not qualify for downstream reuse exports.
- Source and content deduplication, configurable seed hosts and permission-aware research exports.
- CSV export selects the source row correctly and includes source URL, discovery time and licence URL; JSONL exports preserve the same provenance.
- A conservative orthography suggestion API and web tool for a small initial set of spellings such as `mucii → mũciĩ`. Suggestions are not silently applied or saved and must be confirmed by fluent speakers.
- A curated Gĩkũyũ source catalogue registers dataset metadata as pending; it does not download gated datasets or bypass access controls.

The licence detector recognises supported explicit declarations such as CC0, CC BY 3.0/4.0, dedicated public-domain declarations and explicit Kenya Open Data terms. Other, missing or ambiguous declarations remain recorded as unknown for reuse. The crawler's archive collection is not blocked merely because a machine-readable licence is absent.

## Additional implementation in the current repository

- The Hunter's default seed catalogue includes Gĩkũyũ Wikimedia projects, Wikimedia Commons, Wikidata, Kenya Open Data, Internet Archive, Open Library, Project Gutenberg, Library of Congress, Google Books, Zenodo, Hugging Face datasets, GitHub language topics, African Storybook, Maseno University and African Journals Online. The scheduled Hunter also discovers Gĩkũyũ-focused YouTube video metadata and stores those URLs, titles, channels, duration and discovery queries in the pending-source review queue. These YouTube entries are metadata-only; the crawler does not claim to have archived the underlying audio or transcripts.
- Crawl-frontier progress is persisted in Redis so later scheduled batches continue through discovered links instead of repeatedly restarting from the same first pages. The visited set expires after 30 days and is cleared when a full frontier cycle completes. If Redis is unavailable, a process-local fallback keeps the current server process working, but that fallback is not durable across restarts.
- Gĩkũyũ detection includes distinctive unmarked ASCII vocabulary for web material that omits ĩ/ũ, with regression tests to avoid classifying an English page as Gĩkũyũ merely because it mentions Kikuyu. The random-page Wikimedia importer is restricted to the Gĩkũyũ Wikipedia; other language codes are rejected.
- Gĩkũyũ detection now relies on distinctive orthography and vocabulary rather than generic syllables such as “na”, with regression tests for Gĩkũyũ, Kiswahili, English and ambiguous short text.
- Text contribution validation rejects non-Gĩkũyũ language codes. Audio contribution requires both an explicit Gĩkũyũ-language declaration and speaker-consent confirmation; the backend stores the consent declaration and timestamp in source metadata.
- Contributor sign-in/registration pages, text/audio submission forms, a takedown request form, and a researcher portal are implemented in the repository. Text/account/admin/export requests use a bounded same-origin proxy when `BACKEND_API_URL` is configured; large audio uploads require `NEXT_PUBLIC_API_URL`. Without a reachable backend, the API returns explicit 503/502 errors and does not claim the contribution was saved.
- Research exports now support a CC0-only filter in addition to approved records whose permissions match the selected research, AI-training or commercial purpose.
- Search displays archived Gĩkũyũ texts, recordings and transcript matches when the backend is connected; public-reference discovery remains a fallback. English Wikipedia and other language profiles are excluded.

- The transcription workspace supports audio playback, time-aligned Gĩkũyũ transcript segments, translations, corrections restricted to the recording contributor or reviewers, and linguistic annotations (transcription, translation, lemma, part of speech, morphology, tone, IPA, dialect and quality).
- Research exports include permission-filtered CSV/JSONL and bounded WAV ZIP bundles of original WAV files (up to 100 per request) with a source/rights manifest. MP3/M4A conversion to WAV is not implemented. Reviewer/admin interfaces are available in the repository for Hunter control, pending-source review and takedown requests. Administrators can queue bounded manual crawls, inspect run status, approve/reject sources, action removal requests, or reject an unsupported request and restore a source hidden solely for that request when no other open request exists. The public takedown intake immediately hides a matching approved source while the request is queued; an administrator action removes matching indexed records and stored media/text where applicable.
- The homepage now has a daily proverb/riddle slot backed only by approved corpus records and a pseudonymous contributor leaderboard based on approved public contributions. Neither fabricates entries when the backend is absent.
- PWA files have been added: install manifest, icon, service-worker registration, static-shell caching and an offline fallback that can display device-local saved-reference titles. Live offline behaviour has not yet been tested on a phone.
These changes have been committed to the repository, but the new checks have not yet been confirmed green. The latest merged commit is `66e4e1f300661d63a1af33f79bfc7a11101690ea`. GitHub Actions run [40241014319](https://github.com/Kiruri-oss/Gikuyu-archivecorpus-/actions/runs/40241014319) passed 74 backend tests plus frontend typecheck, lint, production build and API smoke tests. This is code/CI verification, not proof of a live production crawl.

## Still not production-enabled

- The FastAPI service is not connected to the Vercel frontend or a production database, object store and search index. Alembic migration `0005_media_language_code` must be applied before the updated media model is used against an existing database.
- Persistent production database, private object storage, and configured search dependencies are not provisioned for the live deployment.
- Contributor accounts, streamed audio uploads, consent recording, time-aligned transcription/annotation UI, WAV exports and moderation workflows are not connected to a production archive.
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

GitHub Actions run [40233670075](https://github.com/Kiruri-oss/Gikuyu-archivecorpus-/actions/runs/40233670075) passed the frontend typecheck, lint, production build and smoke tests plus 36 backend tests on the merge commit.

A Vercel preview for the Hunter branch reached READY, but it is not the production release. The production deployment remains on an older commit. A manual production deployment attempt for the latest merged main commit was rejected by Vercel with HTTP 402 `payment_required`: the team has exceeded the 100-deployments-per-day API limit, with a 24-hour retry window. No plan upgrade or paid resource was created. A successful CI build is not proof that the latest code is deployed or that external source services are reachable. Direct public-site HTTP testing is restricted from this environment.

## Exact activation requirements

The Vercel project currently has no configured archive-backend environment variables, so the backend cannot be started or reached from production. To activate the corpus, provision a persistent PostgreSQL database, Redis, an S3-compatible object store, and Meilisearch, then deploy the FastAPI service as a persistent container/worker (not a short-lived frontend function).

Required backend environment variables from `backend/app/core/config.py`:

- `SECRET_KEY`: a newly generated, private signing secret.
- `DATABASE_URL`: PostgreSQL connection string.
- `REDIS_URL`: Redis connection string.
- `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET_AUDIO` and optionally `S3_BUCKET_TEXT`, `S3_REGION`, `S3_USE_SSL`.
- `MEILISEARCH_URL` and `MEILISEARCH_KEY`.
- `FRONTEND_URL`: the production frontend origin.
- `APP_ENV=production` and `CRAWLER_ENABLED=true` to run the scheduled Hunter.

After the database is provisioned, run `cd backend && alembic upgrade head` before starting the API. Migration `0005_media_language_code` adds the explicit Gĩkũyũ scope to audio records. In Vercel, set server-only `BACKEND_API_URL` to the backend origin for same-origin proxy requests. Set `NEXT_PUBLIC_API_URL` to the backend origin only when browser-direct requests and large audio uploads are enabled; it must not contain credentials.

No database, storage, Redis, Meilisearch or backend service has been provisioned by this work, and no paid resource was created.
