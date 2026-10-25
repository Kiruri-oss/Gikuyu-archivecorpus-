# Gĩkũyũ Archive Corpus

**Live application:** https://gikuyu-archivecorpus.vercel.app  
**Source code:** https://github.com/Kiruri-oss/Gikuyu-archivecorpus-

## Mission

Build an enduring online home for Gĩkũyũ language and cultural knowledge, then extend the infrastructure to African languages broadly. The intended library includes language profiles, vocabulary, stories, oral histories, recordings, time-aligned transcripts, translations, linguistic annotations and responsibly licensed datasets that can support language technology.

The project is deliberately ambitious. The current deployment is an early **public-source discovery layer**, not yet the persistent corpus. The distinction matters: the site must never pretend to have stored a recording or cleared a source for AI training when it has not.

## What is in the current web release

- An initial directory of 20 African language profiles, including Gĩkũyũ, Kiswahili, Kinyarwanda, Hausa, Yorùbá, Igbo, Amharic, Somali, Oromo, Zulu, Xhosa, Shona, Lingala, Luganda, Sesotho, Setswana, Malagasy, Afrikaans, Bambara and Wolof.
- Language-aware public-reference search against the selected language's Wikipedia plus English Wikipedia; the Kikuyu search also checks Kikuyu Wiktionary.
- Source details and original-publisher links, with explicit licence reminders.
- A reading list stored locally in the current browser (up to 200 items; no account sync).
- About, privacy and source-concern pages, responsive navigation and basic accessibility support.
- Same-origin API routes with input validation, source-host allow-listing, request timeouts and short-lived caching.
- A health endpoint at `/api/health`.

The language directory is a starting point for discoverability, not a claim of equal source coverage or community review. Some language Wikipedias may have limited coverage or may be temporarily unavailable.

## Hunter and archive pipeline in the backend

The backend hunter now checks each candidate against `robots.txt`, rejects unsafe local/private targets, and requires a detectable supported open licence before extracting page text. It can follow links through unlicensed pages for discovery only; their content is not archived. Eligible Gĩkũyũ candidates are stored as pending source/text records for review. AI-training and commercial-use flags remain disabled by default. YouTube, news, books and other permission-dependent media are not part of the automatic archive path.

This crawler is groundwork, not a live production collection service: the FastAPI backend still needs its database, storage, indexing and secret configuration deployed and verified before scheduled collection can operate.

## What is not yet production-enabled

- Persistent archive database and private object storage.
- Account registration, sign-in and role-based access on the deployed frontend.
- Recording uploads, community transcript submissions, review queues or annotation workflows on the deployed frontend.
- A private takedown intake, moderation audit trail and verified corpus exports.
- Scheduled crawling, backup/recovery tests and production alerts.

The Python FastAPI service under `backend/` contains groundwork for authentication, media uploads, time-aligned segments, reviewer verification, search indexing and CSV/JSONL exports, but it is **not connected to the current Vercel deployment**. It expects configured services and secrets (database, Redis, S3-compatible storage, Meilisearch and secret settings). Do not submit recordings to the live site expecting them to be saved.

## Technology and checks

- Next.js App Router, React, TypeScript and Tailwind CSS
- Wikimedia API endpoints, called server-side through same-origin Next.js routes
- Vercel hosting
- GitHub Actions for frontend typecheck, lint, production build, API smoke tests and backend unit tests

Local frontend setup:

```bash
git clone https://github.com/Kiruri-oss/Gikuyu-archivecorpus-.git
cd Gikuyu-archivecorpus-/frontend
npm ci
npm run dev
```

Frontend checks:

```bash
npm run typecheck
npm run lint
npm run build
```

Backend tests (Python 3.11+):

```bash
cd ../backend
python -m pip install -e ".[dev]"
pytest -q
```

The public-source search needs network access to Wikimedia. Never commit credentials or put secrets in browser-visible environment variables.

## API routes

- `GET /api/health` — web service health and explicit persistence status
- `GET /api/v1/search?q=...&lang=ki` — language-aware public-source search; language code must be in the supported registry
- `GET /api/v1/media?limit=30&lang=ki` — default discovery results for a selected language
- `GET /api/v1/media/{sourceId}` — detail for an allow-listed public source
- `GET /api/v1/segments/media/{sourceId}` — returns no stored transcript segments for public reference records; there is no persistent community transcript store yet

## Rights, privacy and cultural care

- Public access is not the same as permission to redistribute, commercialise or use material for AI training.
- Verify the licence and terms at each original publisher before reuse.
- Contributor consent must specify the intended uses, including whether material can be used in model training or commercial datasets.
- Keep provenance, language/dialect labels, consent status, licence, reviewer decisions and removal history with each record.
- Sacred, personal, sensitive or community-restricted knowledge should not be treated as automatically public because it can be digitised.
- The reading list is saved in browser local storage on one device and can be lost when site data is cleared.

## Product roadmap

1. **Language directory and discovery (current):** profiles and links to public reference sources.
2. **Persistent core:** database schema, private media storage, identity and permissions, migrations, backups, consent/licence metadata, deletion and audit trails.
3. **Community corpus:** text entry and import, audio upload, resumable uploads, deduplication, transcription segments, translations and annotation tools.
4. **Quality and research:** reviewer queues, inter-annotator checks, provenance-aware CSV/JSONL exports, dataset cards and clear use restrictions.
5. **Language technology and sustainable revenue:** opt-in/licence-specific datasets, paid annotation services or research partnerships, with contributor terms and community benefit defined before sales.
6. **Scale:** additional languages, source connectors, contributor-led acquisition and AI-assisted workflows only where consent and rights permit.

No paid cloud service or credentials are silently created by this repository. The next genuine blocker to a full archive is the absence of provisioned persistent services and deployment secrets—not lack of ambition or additional interface work.

## Verification caveat

A Vercel deployment marked `READY` proves that the hosting build completed, not that every live route and external source works end-to-end. Check the latest GitHub Actions run and Vercel deployment before treating a newly committed change as verified.
