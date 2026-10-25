# Gĩkũyũ Archive Corpus

**Live application:** https://gikuyu-archivecorpus.vercel.app  
**Source code:** https://github.com/Kiruri-oss/Gikuyu-archivecorpus-

## The product

Gĩkũyũ Archive Corpus is intended to become a substantial, searchable digital library for Gĩkũyũ: vocabulary, proverbs, riddles, folklore, literature, oral histories, consent-based audio, time-aligned transcripts, translations, dialect information, orthography review and responsibly licensed AI-training datasets.

This product is exclusively for Gĩkũyũ (Kikuyu, ISO 639-3: kik). It is not a multilingual archive, and adding other language corpora is outside this project's objective. English-language pages may be used only as supporting discovery references where useful; they are never a substitute for Gĩkũyũ material.

## What the current deployment actually does

- Searches selected Wikimedia reference sources and links to their original pages.
- Displays reference details and allows a visitor to save links in that browser.
- Provides initial project, contribution-status, privacy and takedown information.
- Does **not** currently store a persistent Gĩkũyũ corpus or accept real audio/text submissions.

## Core modules

1. **Hunter — implemented in the backend code:** starts from Gĩkũyũ-specific seeds and major public catalogues, follows cross-domain references within explicit page/domain budgets, respects robots.txt and per-host delay, and records source URL, title, discovery time and rights state. It keeps unlicensed pages as source leads, but only ingests full text when a supported open licence is detected and the language detector confidently identifies Gĩkũyũ. New sources remain pending review.
2. **Archive:** persistent records for source metadata, files, language text, audio, transcripts, dialects, orthography, consent and provenance. The production Vercel deployment is not yet connected to the backend database and storage.
3. **Community contribution:** backend routes and frontend forms support text and audio submissions, with ownership/permission declarations, speaker-consent confirmation and review status. These workflows require a configured backend and persistent storage to accept real contributions.
4. **Transcription and annotation:** backend models and API routes support time-aligned segments, translation, correction, annotations, dialect labels and Gĩkũyũ orthography support including ĩ and ũ.
5. **Researcher portal:** backend exports support JSONL and CSV with source provenance and per-record permissions for research, AI training and commercial use. Researcher authentication and production API connectivity are still required.
6. **Community participation:** contributor recognition, a proverb/riddle feature, correction and takedown processes remain further work; no community partnership is claimed unless it is actually established.

## Rights and community safeguards

The intended default is to collect only material with a verified basis for storage and reuse, such as public-domain material, CC0, CC BY where its terms are followed, and government open data whose terms permit reuse. Website availability alone does not establish permission. Media excerpts and other protected works require an appropriate permission basis. Audio contributors must confirm their authority to submit the recording and obtain the relevant speakers' consent; sensitive or culturally restricted knowledge requires additional care.

The project should provide a reachable rights-contact and takedown workflow, maintain an audit trail, and act promptly on valid complaints. Any specific legal deadlines and policy wording must be reviewed against applicable Kenyan law before being promised publicly.

## Hunter operation

The backend hunter is configured by `CRAWLER_SEED_URLS`, `CRAWLER_MAX_PAGES`, `CRAWLER_MAX_DOMAINS`, `CRAWLER_MAX_PAGES_PER_DOMAIN`, `CRAWLER_MAX_CONCURRENCY` and `CRAWLER_MIN_HOST_DELAY_SECONDS`. In a configured production backend it runs every six hours. An administrator can inspect `/api/v1/hunter/status` or trigger a bounded run through `/api/v1/hunter/run?max_pages=250`. Both endpoints require an administrator account. The crawler keeps rejected and taken-down sources out of future automatic ingestion.

## Architecture and current limitations

The web application is in `frontend/` (Next.js). The API/backend code is in `backend/`; it is not yet connected to a production persistent database, object store, queue, search index or account system in the current Vercel deployment. The crawler implementation is in the repository, but it is not operating against a production archive until that backend infrastructure is configured. Uploads, transcription workflows and corpus exports are therefore not live on the current public site and must not be represented as operational.

Before enabling community submissions, configure durable storage and database migrations, authentication and roles, upload limits and malware checks, consent/rights records, moderation and takedown handling, backups, monitoring and tests. Keep credentials in deployment secrets, never in source control.

## Development

Frontend:

```bash
cd frontend
npm ci
npm run lint
npm run build
```

Backend setup and checks are documented in `backend/pyproject.toml` and the backend README. Use a disposable test database and test storage when running integration tests.

## Guiding principle

The objective is not a thin wrapper around external websites. Public-source discovery is only an initial ingestion path. The real product is a durable Gĩkũyũ corpus built from traceable sources, community knowledge shared with consent, high-quality transcription and annotation, and carefully curated datasets.
