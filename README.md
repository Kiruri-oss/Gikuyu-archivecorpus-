# Gĩkũyũ Archive Corpus

**Live application:** https://gikuyu-archivecorpus.vercel.app  
**Source code:** https://github.com/Kiruri-oss/Gikuyu-archivecorpus-

## The product

Gĩkũyũ Archive Corpus is intended to become a substantial, searchable digital library for Gĩkũyũ: vocabulary, proverbs, riddles, folklore, literature, oral histories, consent-based audio, time-aligned transcripts, translations, dialect information, orthography review and responsibly licensed AI-training datasets.

This product is exclusively for Gĩkũyũ (Kikuyu, ISO 639-3: kik). It is not a multilingual archive, and material in other languages is outside this project's corpus scope.

## What the current deployment actually does

- Searches selected Wikimedia reference sources and links to their original pages.
- Displays reference details and allows a visitor to save links in that browser.
- Provides initial project, contribution-status, privacy and takedown information.
- Does **not** currently store a persistent Gĩkũyũ corpus or accept real audio/text submissions.

## Intended core modules

1. **Hunter:** aggressively discover Gĩkũyũ material across publicly reachable websites, archives, catalogues and repositories. Respect robots.txt, record source URL/date/type and any detected licence, and follow relevant cross-domain links under bounded crawl limits. Missing licence metadata is recorded as unknown; it does not silently grant AI-training, commercial or redistribution permission.
2. **Archive:** persistent records for source metadata, files, language text, audio, transcripts, dialects, orthography, consent and provenance.
3. **Community contribution:** proverbs, stories, conversations, original writing and eligible literature, with clear consent, ownership/permission declarations and review workflows.
4. **Transcription and annotation:** time-aligned segments, translation, correction, reviewer status, dialect labels and Gĩkũyũ orthography support including ĩ and ũ.
5. **Researcher portal:** curated, licence-filtered exports, with source-level provenance and separate eligibility checks for text/audio and AI-training use.
6. **Community participation:** contributor recognition, a proverb/riddle feature only when content is community-submitted or rights-cleared, and correction/takedown processes.

## Rights and community safeguards

The Hunter is designed as a broad archive with a takedown workflow: publicly reachable Gĩkũyũ material can be collected even when the source has no machine-readable licence statement. Each record retains its source and any licence evidence; missing or unsupported licence metadata is marked unknown, not treated as a reuse grant. Public archive visibility is separate from eligibility for AI-training, commercial or researcher exports, which must follow each record's stored permission flags.

Audio contributors must confirm their authority to submit the recording and confirm that they have permission from the speaker and own or are authorised to submit the recording. Requests to remove material are logged; when actioned, the source is hidden, its stored text/media records are removed, and corresponding search entries are purged. The external publisher's copy is not controlled by this archive.

## Architecture and current limitations

The web application is in `frontend/` (Next.js). The API/backend code is in `backend/`; it is not yet connected to a production persistent database, object store, queue, search index or account system in the current Vercel deployment. Uploads, transcription workflows and corpus exports are therefore not live and must not be represented as operational.

Before enabling community submissions, configure durable storage and database migrations, authentication and roles, upload limits and malware checks, consent/rights records, moderation and takedown handling, backups, monitoring and tests. Keep credentials in deployment secrets, never in source control.
For a deployment with a running backend, set `BACKEND_API_URL` to the server-side API origin for same-origin account, text contribution, transcription, annotation, researcher-export and admin requests. Set `NEXT_PUBLIC_API_URL` to the public API origin for direct browser calls and large audio uploads; set the backend's `FRONTEND_URL` to the web origin for CORS. When the backend is absent or unreachable, requests return an explicit error and are not reported as saved. Audio upload must use the direct API URL because large files must not pass through the web proxy.


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
