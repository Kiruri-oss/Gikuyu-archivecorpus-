# Gĩkũyũ Archive

**Live application:** https://gikuyu-archivecorpus.vercel.app  
**Source code:** https://github.com/Kiruri-oss/Gikuyu-archivecorpus-

Gĩkũyũ Archive is an early-stage language-preservation project. The current public deployment is a **public-source discovery tool**: it searches selected Wikimedia reference sites and links people to the original pages. It is not yet a persistent community corpus.

## What works in the current deployment

- Search public reference pages from Kikuyu Wikipedia, Kikuyu Wiktionary and English Wikipedia.
- Open a source detail view with an introduction and a link to the publisher.
- Save up to 200 references in a reading list stored locally in the current browser.
- Read clear guidance about project scope, privacy and third-party source concerns.
- Use responsive pages with basic accessibility support, search validation, request timeouts, source allow-listing and short-lived caching.
- Check service health at `/api/health`.

## What is not enabled

The deployed frontend does **not** currently provide accounts, a persistent database, audio uploads, user-submitted transcripts, moderation queues, private takedown intake, verified corpus exports or automated crawling. The Python FastAPI code under `backend/` is not connected to the Vercel production deployment. Contribution and export pages state these limits rather than implying that an upload or export succeeded.

Do not submit recordings or sensitive information expecting the current site to store or review them. Search results are third-party references, and discovery does not grant reuse or AI-training rights.

## Technology

- Next.js App Router, React, TypeScript and Tailwind CSS
- Same-origin Next.js API routes for public-source search and source-page details
- Wikimedia API endpoints, with timeouts and brief caching
- Vercel deployment
- GitHub Actions for frontend typecheck, lint, production build and API smoke tests, plus backend unit tests

## Local development

Requirements: Node.js 20+ and Python 3.11+ for the backend tests.

```bash
git clone https://github.com/Kiruri-oss/Gikuyu-archivecorpus-.git
cd Gikuyu-archivecorpus-/frontend
npm ci
npm run dev
```

The frontend runs on http://localhost:3000. Its public-source search routes need network access to Wikimedia to return live results.

Run frontend checks:

```bash
npm run typecheck
npm run lint
npm run build
```

Run backend tests:

```bash
cd ../backend
python -m pip install -e ".[dev]"
pytest -q
```

The backend expects provisioned services and environment configuration for production use. Do not put credentials in source control.

## API routes

- `GET /api/health` — frontend service status and explicit persistence mode
- `GET /api/v1/search?q=...` — search selected public reference sources (minimum two characters)
- `GET /api/v1/media?limit=...` — default discovery results
- `GET /api/v1/media/{sourceId}` — details for an allow-listed public source
- `GET /api/v1/segments/media/{sourceId}` — currently returns an empty list for public references; there is no persistent community transcript store

## Rights, privacy and cultural care

- Check the original publisher's licence and terms before reusing material.
- Do not assume that publicly accessible material is free for redistribution or AI training.
- Public reference links may lead to third-party privacy and content policies.
- The reading list is saved in browser local storage on one device and is not account-synced.
- Community recordings and culturally sensitive knowledge require informed consent, clear licensing, access controls and workable deletion/takedown processes before a collection workflow is launched.

Read the live [privacy notice](https://gikuyu-archivecorpus.vercel.app/privacy), [project overview](https://gikuyu-archivecorpus.vercel.app/about) and [source concern guidance](https://gikuyu-archivecorpus.vercel.app/takedown).

## Launch roadmap

1. **Current:** dependable public-source discovery MVP.
2. **Foundation:** choose and provision a persistent database and private object storage; define authentication, roles, retention, consent, licence metadata and deletion behaviour.
3. **Community pilot:** implement submissions, transcript review, private takedown intake and audit trails; test access controls and recovery.
4. **Research release:** build licence-aware exports, dataset documentation, source provenance and repeatable quality checks.
5. **Scale:** only then consider scheduled crawling and AI-assisted transcription, with clear consent and cultural safeguards.

The next stages require real infrastructure configuration and, before accepting community material, policy decisions. No paid cloud service or credentials are silently created by this repository.

## Current verification caveat

GitHub Actions is the source of truth for the latest code checks. A Vercel deployment marked `READY` means the hosting build completed; it does not prove every production API request works. The current environment has not independently verified the public site's HTTP responses end-to-end.
