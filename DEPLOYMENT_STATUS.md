# Deployment and product status

Last reviewed: 26 October 2026

## Product objective

Build the largest practical Gĩkũyũ (Kikuyu, ISO 639-3: kik) language library. Gĩkũyũ is the only corpus language. The product is a source-traceable archive of texts, oral recordings, transcripts, translations, annotations and research datasets—not a multilingual directory or a search wrapper.

## Current live release

The deployed frontend provides Gĩkũyũ-focused public-reference discovery, source detail pages, device-local saved references, and project/privacy/source-concern information. Search results link to external publishers; they are not records persisted by this frontend.

The FastAPI backend is not connected to the Vercel frontend with production database, object storage and search credentials. The backend changes below are in the repository and do not mean the live site is running the Hunter or accepting contributions.

## Hunter changes in this branch

- Expanded the crawler from same-host-only crawling to relevant cross-domain discovery, with a 500-page run budget, a 40-host cap and a per-host page cap.
- Expanded default seeds to include public corpus/catalogue sources, Kenyan open data, archives, research repositories and Gĩkũyũ-specific discovery pages.
- Retained robots.txt enforcement, safe public-HTTP URL checks, redirect limits, page-size limits and no authentication/access-control bypass.
- Captures detected Gĩkũyũ pages even when machine-readable licence metadata is absent, matching the project's notice-and-takedown archive direction.
- Records unknown licence status explicitly. Unknown rights never grant AI-training, commercial-use or researcher-redistribution permission.
- Stores new corpus candidates as public archive records and indexes them when the database is available. Search-index errors are logged without discarding the database archive record.
- Adds tests for relevant cross-domain discovery and unknown-rights reuse defaults.
- Takedown action now hides the source, removes its text/media records and attempts to purge the corresponding search-index and object-store entries while retaining the takedown record for audit.

## Still not production-enabled

- The FastAPI service is not connected to the Vercel frontend.
- Persistent production database, private object storage and configured search dependencies are not provisioned for the live deployment.
- Contributor accounts, secure audio uploads, consent recording, time-aligned transcription/annotation UI, researcher exports and the takedown intake are not connected end-to-end to a production archive.
- Production backups, restore tests, alerts and full end-to-end tests against provisioned services remain outstanding.
- The Hunter changes in this branch have not yet passed CI or been deployed. No claim is made that live crawling has started.

## Rights and data governance

The crawler respects robots.txt and does not bypass access controls. It records source and licence evidence. Unknown rights are not treated as a grant for downstream dataset reuse. Public visibility in the archive and eligibility for AI-training/commercial exports are separate flags. Audio submissions require rights and speaker-consent declarations. A takedown record is retained so removal requests can be audited.

## Security and dependencies

- Frontend uses a committed lockfile and `npm ci`.
- GitHub Actions repository permissions are read-only.
- The latest previously observed dependency audit reported three moderate advisories in the Tailwind/PostCSS selector-parsing dependency chain; rerun the audit before making a current claim.
- No production secrets or paid services were created as part of this work.

## Verification

The new Hunter and takedown changes are committed to a feature branch with regression tests. CI and deployment status must be checked after the pull request is opened. A successful CI build is not proof that the backend is deployed, that its production services are configured, or that external source sites are reachable.
