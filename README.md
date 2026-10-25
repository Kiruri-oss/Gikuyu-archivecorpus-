# Gĩkũyũ Archive Corpus

**Live application:** https://gikuyu-archivecorpus.vercel.app  
**Source code:** https://github.com/Kiruri-oss/Gikuyu-archivecorpus-

## Mission

Build a large, searchable digital library for **Gĩkũyũ (Kikuyu, ISO 639-3: `kik`) alone**. The product is a corpus—not a multilingual directory or a search wrapper. It should collect and preserve Gĩkũyũ words, proverbs, riddles, folklore, literature, oral histories, recordings, transcripts, translations, dialect information and annotated language data for research and language technology.

The original product is a notice-and-takedown archive: the Hunter searches widely across publicly reachable sources, respects `robots.txt`, records where material came from, and captures detected Gĩkũyũ content. A rights complaint must be traceable and actionable. No login walls, access controls, private networks or robots exclusions are bypassed.

## Core modules

1. **Hunter:** crawl configured public-web seed sources, follow relevant cross-site links, detect Gĩkũyũ, deduplicate text, and record source URL, title, discovery time, detected licence and rights metadata. Machine-readable licence metadata is recorded when present; absence is marked as unknown rather than treated as a licence.
2. **Archive:** durable searchable source and text records, media metadata, hashes, transcripts, dialect labels, orthography and provenance.
3. **Contribute:** text and audio contributions for proverbs, stories, conversations, translations and original writing. Audio submissions must include the contributor's recording-rights and speaker-consent declarations.
4. **Transcription and annotation:** time-aligned transcript segments, translation, corrections, dialect tags, review state and Gĩkũyũ orthography including ĩ and ũ.
5. **Researcher portal:** searchable, provenance-preserving JSONL/CSV exports with filters for dialect and permitted research, AI-training or commercial use.
6. **Community features:** contributor recognition, proverb/riddle features sourced from archive records, correction requests and a takedown queue.

## Data and rights handling

- Gĩkũyũ is the only corpus language. A source containing another language is not itself a Gĩkũyũ corpus record.
- The Hunter is designed for broad collection from publicly reachable pages and follows the site's robots policy. It does not bypass authentication or access controls.
- Every record keeps its source URL, discovery time and detected rights metadata. If a licence is not detected, it is recorded as unknown; that unknown status **does not grant AI-training, commercial reuse or researcher redistribution permission**.
- Copyright, privacy and cultural-sensitivity requests must be logged and handled through the takedown workflow. The original source host remains responsible for its own copy.
- Audio contributions require explicit declarations that the contributor has rights to submit the recording and has obtained relevant speaker consent.
- Takedown intake and backend deletion code exist in the repository, but a working production-connected intake and service-level guarantee depend on deploying and testing the backend with persistent services.

## What is live versus in the repository

The current Vercel frontend provides Gĩkũyũ-focused public-reference discovery, source details, a device-local saved list and project information. The FastAPI backend contains corpus, transcription, annotation, export, source-review, orthography and takedown modules, but is **not yet connected to the live Vercel application with production database, object storage and search credentials**. Therefore, do not treat the current website as accepting persistent contributions or running its Hunter in production.

## Architecture

- `frontend/`: Next.js App Router, TypeScript and Tailwind.
- `backend/`: FastAPI, SQLAlchemy, PostgreSQL, object storage and Meilisearch integration.
- `backend/app/crawlers/`: public-web crawling, robots handling, source discovery and licence metadata detection.
- `backend/app/services/export.py`: provenance-preserving JSONL and CSV serializers.
- `backend/app/api/v1/`: authentication, media, segments, annotations, text records, sources, exports, orthography and takedowns.

## Development and verification

Frontend:

```bash
cd frontend
npm ci
npm run typecheck
npm run lint
npm run build
```

Backend:

```bash
cd backend
pip install -e ".[dev]"
pytest -q
```

Use a disposable test database and test object storage for integration testing. Production secrets belong in deployment secret settings, never in source control.

## Guiding principle

Gĩkũyũ deserves a permanent digital home and a serious corpus. Search wrappers are only a temporary discovery aid; the real product is a growing archive of source-traceable text and audio, high-quality transcription and annotation, and datasets whose reuse permissions are explicit.
