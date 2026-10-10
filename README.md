```
gikuyu-archive/README.md
```

```markdown
# Gĩkũyũ Language Archive

A community-controlled, notice-and-takedown archive for **Kikuyu (Gĩkũyũ, ISO 639-3: `kik`)** audio, literature, and oral history. Built to collect, transcribe, translate, and export AI-ready datasets while preserving the language and giving the community ownership of its own data.

---

## Table of Contents

1. [Mission](#mission)
2. [What It Does](#what-it-does)
3. [Architecture](#architecture)
4. [Project Breakdown](#project-breakdown)
5. [Tech Stack](#tech-stack)
6. [Data Model](#data-model)
7. [Local Development](#local-development)
8. [Firebase Setup](#firebase-setup)
9. [Deployment](#deployment)
10. [Testing](#testing)
11. [API Reference](#api-reference)
12. [Legal & Ethics](#legal--ethics)
13. [Takedown Policy](#takedown-policy)
14. [Data Licensing](#data-licensing)
15. [Code Licensing](#code-licensing)
16. [Contributing](#contributing)
17. [Roadmap](#roadmap)
18. [Acknowledgements](#acknowledgements)

---

## Mission

Kikuyu has millions of speakers but almost no structured digital corpus. Existing online content is scattered across YouTube sermons, Facebook groups, church sites, Wikipedia stubs, and out-of-print books. None of it is searchable, aligned, or usable for AI training.

This project exists to:

- **Hunt** for existing Kikuyu audio and text across the open web and physical media.
- **Archive** it in a permanent, searchable, community-governed database.
- **Crowdsource** transcription, translation, and linguistic annotation from native speakers.
- **Export** clean, license-tagged datasets for ASR, TTS, MT, and LLM research.
- **Protect** the community's rights through a public takedown process and tiered licensing.

The archive is not a scraping operation. It is a **data trust** with a technical layer.

---

## What It Does

| Capability | Description |
|---|---|
| **Discovery** | Crawlers scan Wikipedia (`ki.`), Wiktionary, YouTube, blogs, church sites, news portals, and academic repositories for Kikuyu content. |
| **Language Detection** | A hybrid heuristic + XLM-R classifier filters Kikuyu from Kiswahili, English, and other Bantu languages before storage. |
| **Deduplication** | SHA-256 content hashing prevents the same sermon being stored five times from five different sites. |
| **Public Archive** | Search by word, phrase, dialect, speaker, genre, or county. Every item shows its source and license. |
| **Crowdsourcing** | Contributors record in-browser, upload files, transcribe 30-second segments, translate, and verify. |
| **Researcher Export** | JSONL, CSV, and Parquet exports filtered by dialect, license, and confidence. |
| **Takedown System** | Public form. Logged, timestamped, actioned within 72 hours. Tombstones preserved for audit. |
| **Community Governance** | Reviewer and admin roles. Dialect experts gate-keep quality. |

---

## Architecture

```

┌──────────────────────────────────────────────────────────────────┐
│                      Firebase Hosting (Next.js)                  │
│  /search  /contribute  /media/[id]  /transcribe  /researcher     │
└────────────────────────────┬─────────────────────────────────────┘
│ HTTPS
▼
┌──────────────────────────────────────────────────────────────────┐
│              Cloud Run — FastAPI (backend/app/main.py)           │
│  Auth (Firebase ID tokens) · Media · Segments · Exports · API    │
└──────┬──────────────┬──────────────┬──────────────┬──────────────┘
│              │              │              │
▼              ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────────┐
│ Firestore  │ │  Firebase  │ │  Cloud     │ │  Cloud           │
│ (metadata) │ │  Storage   │ │  Functions │ │  Scheduler       │
│            │ │  (audio,   │ │  (triggers,│ │  (crawl jobs)    │
│            │ │   text)    │ │  workers)  │ │                  │
└────────────┘ └────────────┘ └────────────┘ └──────────────────┘
│
▼
┌────────────────────┐
│  Vertex AI / HF    │
│  Whisper (kik)     │
│  XLM-R (langdet)   │
└────────────────────┘

```

---

## Project Breakdown

### `/backend` — FastAPI service on Cloud Run

| Module | Responsibility |
|---|---|
| `core/config.py` | Pydantic settings loaded from `.env` / Secret Manager. |
| `core/firebase.py` | Firebase Admin SDK initialization (Auth + Firestore + Storage). |
| `core/security.py` | ID token verification, role-based dependencies. |
| `core/deps.py` | FastAPI dependency aliases (`DbSession`, `CurrentUser`, `AdminUser`). |
| `db/firestore.py` | Firestore client wrapper with typed collection helpers. |
| `db/storage.py` | Firebase Storage upload, delete, signed URL generation. |
| `db/search.py` | Firestore query helpers + optional Algolia/Typesense adapter. |
| `models/*` | Pydantic domain models (not ORM). Mirrors Firestore documents. |
| `schemas/*` | Request/response validation schemas. |
| `api/v1/auth.py` | Register, login bridge (Firebase handles the actual auth), profile. |
| `api/v1/media.py` | Upload, list, fetch, delete media. |
| `api/v1/segments.py` | Create, update, verify time-aligned transcript segments. |
| `api/v1/annotations.py` | POS, lemma, tone, IPA, dialect tags. |
| `api/v1/submissions.py` | Contributor submissions queue. |
| `api/v1/search.py` | Full-text search across media and segments. |
| `api/v1/exports.py` | Streaming JSONL and CSV exports. |
| `api/v1/takedowns.py` | Public submission + admin action. |
| `services/language_detector.py` | Kikuyu-vs-Kiswahili-vs-English classification. |
| `services/transcription.py` | Whisper inference (Kikuyu-finetuned). |
| `services/export.py` | Dataset serializers. |
| `crawlers/web.py` | Async BeautifulSoup + httpx crawler with robots.txt respect. |
| `crawlers/youtube.py` | yt-dlp discovery + metadata extraction. |

### `/functions` — Python Cloud Functions

| Trigger | Purpose |
|---|---|
| `triggers/on_media_upload.py` | Fires on Storage `finalize`. Runs language detection, generates waveform, updates Firestore. |
| `triggers/on_segment_create.py` | Fires on Firestore segment create. Queues transcription if missing. |
| `triggers/on_takedown_create.py` | Fires on takedown create. Notifies admins, creates audit log. |
| `scheduled/crawl_web.py` | Every 12 hours. Runs web crawler across seed URLs. |
| `scheduled/crawl_youtube.py` | Every 6 hours. Discovers new Kikuyu YouTube content. |
| `scheduled/daily_digest.py` | Daily summary email to admins. |

### `/frontend` — Next.js 15 App Router

| Route | Purpose |
|---|---|
| `/` | Landing page, mission, entry points. |
| `/search` | Full-text search with debounced queries. |
| `/media/[id]` | Media detail, audio player, segment list. |
| `/contribute` | In-browser recorder + upload flow. |
| `/transcribe/[segmentId]` | Focused transcription/translation workspace. |
| `/researcher` | Bulk export UI (JSONL, CSV, Parquet). |
| `/admin/takedowns` | Takedown review and enforcement. |
| `/auth/login` | Firebase Auth sign-in. |
| `/auth/register` | Firebase Auth sign-up + profile creation. |

### `/functions` vs `/backend` — why both

- **Cloud Functions** handle event-driven work: file uploads, Firestore writes, scheduled jobs. They scale to zero and run in the background.
- **Cloud Run** handles synchronous HTTP: search, uploads, exports. It stays warm and serves the frontend.

Splitting them keeps cold-start latency off the user-facing path and keeps background work cheap.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Hosting | Firebase Hosting (CDN + rewrites to Cloud Run) |
| Backend | FastAPI 0.115, Python 3.11, Uvicorn |
| Backend hosting | Google Cloud Run |
| Auth | Firebase Authentication (email/password + Google) |
| Database | Cloud Firestore (Native mode) |
| Object storage | Firebase Storage (Cloud Storage bucket) |
| Background jobs | Cloud Functions (Python 3.11) + Cloud Scheduler |
| AI inference | Vertex AI endpoints or Hugging Face Inference API |
| Language detection | Custom heuristic + `papluca/xlm-roberta-base-language-detection` |
| Speech-to-text | `microsoft/paza-whisper-large-v3-turbo` (Kikuyu finetune) |
| Text-to-speech | Coqui VITS (planned) |
| Machine translation | NLLB-200 distilled 600M (planned) |

---

## Data Model

Firestore collections mirror the Pydantic models in `backend/app/models/`.

```

users/{userId}
email, full_name, role, institution, dialect, county, is_active, created_at

sources/{sourceId}
url, domain, source_type, status, license, language_confidence, fetched_at

media/{mediaId}
source_id, kind, title, speaker, dialect, county, genre,
file_key, sha256, duration_seconds, size_bytes, mime_type,
lang_score, license, notes, created_at

media/{mediaId}/segments/{segmentId}
start_seconds, end_seconds, transcript, translation,
speaker_label, is_verified, confidence, created_by

media/{mediaId}/segments/{segmentId}/annotations/{annotationId}
user_id, annotation_type, value, confidence

submissions/{submissionId}
contributor_id, submission_type, status, title, payload,
reviewer_id, reviewer_notes

takedowns/{takedownId}
url, requester_name, requester_email, reason, status,
actioned_at, admin_notes

```

**Composite indexes** required for common queries are declared in `firestore.indexes.json`.

---

## Local Development

### Prerequisites

- Node.js 20+
- Python 3.11+
- Firebase CLI (`npm i -g firebase-tools`)
- Google Cloud SDK (for Cloud Run deploy)
- A Firebase project with Firestore, Storage, Auth, and Hosting enabled

### 1. Clone and install

```bash
git clone <repo-url> gikuyu-archive
cd gikuyu-archive

cd frontend && npm install && cd ..
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -e . && cd ..
cd functions && pip install -r requirements.txt && cd ..
```

2. Configure environment

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
cp .firebaserc.example .firebaserc
```

Fill in your Firebase project ID, service account JSON path, and API keys.

3. Run Firebase emulators

```bash
firebase emulators:start --only auth,firestore,storage,functions
```

4. Run the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs at http://localhost:8000/api/docs.

5. Run the frontend

```bash
cd frontend
npm run dev
```

Frontend at http://localhost:3000.

---

Firebase Setup

Project initialization

```bash
firebase login
firebase projects:create gikuyu-archive-prod
firebase use gikuyu-archive-prod
firebase init firestore storage functions hosting
```

Enable services

1. Authentication — Email/Password + Google providers.
2. Firestore — Native mode, region europe-west1 or us-central1.
3. Storage — Default bucket.
4. Hosting — Connect to Firebase Studio or GitHub.
5. Cloud Run — Enable API for backend deployment.
6. Cloud Scheduler — For crawler jobs.

Deploy rules and indexes

```bash
firebase deploy --only firestore:rules,firestore:indexes,storage:rules
```

Environment secrets (Cloud Run)

```bash
gcloud secrets create gikuyu-secret-key --data-file=- <<< "your-secret-here"
gcloud secrets create gikuyu-hf-token --data-file=- <<< "your-hf-token"
```

---

Deployment

Backend → Cloud Run

```bash
cd backend
gcloud builds submit --config cloudbuild.yaml
```

Or:

```bash
./cloudrun/deploy.sh
```

Service reachable at https://gikuyu-api-<hash>-<region>.a.run.app.

Functions → Firebase

```bash
firebase deploy --only functions
```

Frontend → Firebase Hosting

```bash
cd frontend
npm run build
firebase deploy --only hosting
```

firebase.json rewrites /api/** to the Cloud Run service so the frontend can call the backend at the same origin.

---

Testing

Backend

```bash
cd backend
pytest -v --cov=app --cov-report=term-missing
```

Coverage target: 80% on services/, api/, and crawlers/.

Functions

```bash
cd functions
pytest -v
```

Frontend

```bash
cd frontend
npm run typecheck
npm run lint
npm run build
```

End-to-end

```bash
firebase emulators:exec --only auth,firestore,storage,functions "npm run test:e2e"
```

---

API Reference

Base URL: https://<region>-<project>.cloudfunctions.net/api/v1 (dev) or https://gikuyu-api-xxxxx.a.run.app/api/v1 (prod).

Method Endpoint Auth Purpose
POST /auth/register public Create profile after Firebase signup
POST /auth/login public Exchange ID token, return role
GET /auth/profile user Current profile
GET /media public List media (filter by dialect, genre)
GET /media/{id} public Media detail with signed URL
POST /media contributor Upload media
DELETE /media/{id} reviewer Delete media
GET /segments/media/{mediaId} public List segments for media
POST /segments contributor Create segment
PATCH /segments/{id} contributor Update transcript/translation
POST /segments/{id}/verify reviewer Mark verified
GET /search?q= public Full-text search
GET /exports/jsonl researcher Stream JSONL
GET /exports/csv researcher Stream CSV
POST /takedowns public Submit takedown
GET /takedowns admin List takedowns
POST /takedowns/{id}/action admin Enforce takedown

Full OpenAPI spec at /api/docs in non-production environments.

---

Legal & Ethics

Framework

The archive operates under a notice-and-takedown model, similar to the Internet Archive and the Oakland Archive Policy. We do not pre-clear rights. We log every source with URL, timestamp, and license metadata, and we act on takedown requests within 72 hours.

Kenya-specific compliance

· Data Protection Act 2019 — personal data (names, voices, emails) is stored under Firebase's Data Processing Agreement. Contributors can request export or deletion.
· Copyright Act (Cap 130) — takedowns are logged and honored. Fair dealing provisions apply to research and archiving.
· Traditional Knowledge and Cultural Expressions Act 2016 — sacred or restricted cultural material can be flagged by a community review board and hidden from public view.

Community governance

· A Community Review Board of native speakers and dialect experts approves corpus inclusion policy.
· Sacred material (initiation songs, restricted rituals) is quarantined on request from elders.
· Contributors are credited by default; anonymous contribution is available.
· Commercial reuse of the corpus requires revenue-sharing discussion with contributors.

---

Takedown Policy

How to submit

POST to /api/v1/takedowns or use the form at https://gikuyu-archive.org/takedown.

Include:

· URL of the disputed content
· Your name and email
· Reason (copyright, privacy, cultural sensitivity, other)
· Optional supporting documentation

What happens

1. Request logged with timestamp in Firestore takedowns collection.
2. Admin notified via on_takedown_create Cloud Function.
3. Content reviewed by admin within 72 hours.
4. If valid: file removed from Firebase Storage, Firestore document deleted, search index purged. A tombstone record remains for audit.
5. Requester notified of outcome.
6. Repeat requests from same source trigger domain-level blocklist.

Counter-notice

If your content was removed in error, email takedown@gikuyu-archive.org with proof of ownership or public domain status. We restore within 14 days if the claim is valid.

Statistics

Public takedown statistics are published monthly at https://gikuyu-archive.org/transparency.

---

Data Licensing

Default license for community submissions

Contributions default to Creative Commons Attribution 4.0 International (CC BY 4.0) unless the contributor selects otherwise.

Allowed licenses

License AI Training Commercial Use Attribution
CC0 ✅ ✅ Not required
CC BY 4.0 ✅ ✅ Required
CC BY-SA 4.0 ✅ ✅ Required, share-alike
CC BY-NC 4.0 ✅ ❌ Required
Community License v1 Per terms Per terms Required
Restricted (board approval) ❌ ❌ N/A

How licensing works in the archive

· Every media and text_record document has a license field.
· Exports filter by license: GET /api/v1/exports/jsonl?license=CC-BY-4.0.
· The researcher UI shows license breakdowns before download.
· AI trainers must respect license metadata. Violation is grounds for revocation of research access.

Dataset citation

```
@misc{gikuyu_archive_2026,
  title={Gĩkũyũ Language Archive},
  author={{Gĩkũyũ Language Community}},
  year={2026},
  url={https://gikuyu-archive.org},
  note={Version X.Y, accessed YYYY-MM-DD}
}
```

---

Code Licensing

MIT License

```
Copyright (c) 2026 Gĩkũyũ Language Archive Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

Code is MIT. Data is not. Code license and data license are separate concerns.

---

Contributing

We welcome three kinds of contribution:

1. Code

· Fork, branch off main, open a PR.
· Run pytest, npm run typecheck, and npm run lint before submitting.
· Follow SOLID, DRY, KISS. Small functions. Meaningful names.
· No new dependency without a one-paragraph justification in the PR body.

2. Language data

· Use /contribute to record or upload.
· Use /transcribe to help clean existing recordings.
· Dialect experts: apply for reviewer role via contribute@gikuyu-archive.org.

3. Governance

· Community Review Board seats rotate every 12 months.
· Nominations open quarterly.
· Board charters and minutes published at https://gikuyu-archive.org/governance.

Code of Conduct

Be respectful. No harassment. No political campaigning. Full CoC in CODE_OF_CONDUCT.md.

---

Roadmap

v1.0 — Foundation (current)

· ✅ Firebase + Cloud Run infrastructure
· ✅ Media upload, browse, search
· ✅ Segment transcription and translation
· ✅ Takedown system
· ✅ JSONL/CSV export

v1.1 — Quality

☐ Meilisearch / Typesense integration for Kikuyu-aware full-text search
☐ Contributor reputation system
☐ Segment-level review workflow with diffs
☐ Dialect tagging by native speakers

v1.2 — AI pipelines

☐ Whisper Kikuyu finetune baseline
☐ Automatic time alignment (WhisperX)
☐ TTS voice cloning with explicit consent gates
☐ NLLB Kikuyu ↔ English/Kiswahili MT

v2.0 — Ecosystem

☐ Public API keys for researchers
☐ Hugging Face Datasets sync
☐ Dialect map and speaker atlas
☐ Offline-first PWA for low-bandwidth contributors
☐ Community Review Board elections

---

Acknowledgements

· Kikuyu speakers, elders, and teachers who make this possible.
· Mozilla Common Voice and Masakhane for pioneering low-resource language work.
· Internet Archive and the Oakland Archive Policy for the takedown-first legal model.
· Microsoft for the paza-whisper-large-v3-turbo Kikuyu checkpoint.
· Google Cloud for Firebase and Cloud Run credits under the startup program.
· All contributors who give their voice to keep Gĩkũyũ alive online.

---

Contact

· General: hello@gikuyu-archive.org
· Takedowns: takedown@gikuyu-archive.org
· Contributions: contribute@gikuyu-archive.org
· Governance: board@gikuyu-archive.org

Project repository: https://github.com/gikuyu-archive/gikuyu-archive

---

Gĩkũyũ nĩ gĩthaka. Kũrĩa kũrĩ andũ, kũrĩ ũhoro.
(Kikuyu is a treasure. Where there are people, there is history.)

```