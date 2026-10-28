# Free-tier deployment plan

This project must not rely on Render's free PostgreSQL database for permanent corpus data: Render documents that free PostgreSQL databases expire after 30 days. The selected no-cost starting stack is:

- **Supabase Free**: PostgreSQL metadata database.
- **Firebase Cloud Storage adapter**: optional file-storage backend for audio and permitted files. This is integrated in code, but new Firebase Storage buckets may require the Blaze billing plan; do not enable billing until the owner has reviewed costs.
- **Render Free Web Service**: run the existing Python/FastAPI backend. Expect cold starts after 15 minutes idle; this is suitable for a low-traffic launch preview, not a high-availability guarantee.
- **GitHub Actions**: run bounded scheduled Hunter jobs and CI without requiring a permanently running paid worker.
- **Existing Vercel deployment**: continue serving the Next.js frontend.
- **PostgreSQL search fallback**: prefer database-backed search where a separate hosted Meilisearch service is unavailable. Never treat a missing search service as evidence that an item does not exist.

Official limits and pricing:
- Render free service limitations and the 30-day free Postgres expiry: https://render.com/docs/free
- Supabase free plan: https://supabase.com/pricing
- Cloudflare's free D1/R2 alternative, should the application later move to a serverless architecture: https://developers.cloudflare.com/workers/platform/pricing/

## Configuration

The Render blueprint in `/render.yaml` declares the backend and marks account-specific values as secrets instead of committing credentials. Create a Supabase project for PostgreSQL, then either configure Firebase Cloud Storage or an S3-compatible object store for media. Never paste credentials into GitHub issues, commits, or chat.

Firebase file storage configuration:
- `FIREBASE_PROJECT_ID`: Firebase project ID.
- `FIREBASE_STORAGE_BUCKET`: exact bucket name shown in Firebase/Google Cloud Storage.
- `FIREBASE_SERVICE_ACCOUNT_JSON`: complete service-account JSON stored only as a protected Render environment variable. Create a least-privilege service account and do not commit its key.
- Firebase currently requires checking the project's billing plan before creating/using Cloud Storage buckets; the Firebase pricing page lists no-cost storage allowances on Blaze, not a general no-billing guarantee. Do not upgrade the account without reviewing the current terms.

When Firebase variables are present, audio and text object keys use the existing logical bucket name as a prefix inside the configured Firebase bucket. PostgreSQL remains the source of truth for metadata; this change does not migrate relational metadata to Firestore.

Required values:
- `DATABASE_URL`: Supabase PostgreSQL connection string compatible with asyncpg; use the provider's recommended connection endpoint.
- Alternatively, for S3-compatible storage, set `S3_ENDPOINT`, `S3_ACCESS_KEY`, and `S3_SECRET_KEY`; do not configure both providers unless deliberately testing provider precedence.
- `MEILISEARCH_URL`, `MEILISEARCH_KEY`, `REDIS_URL` are optional in this branch. Without Meilisearch, the API falls back to PostgreSQL text search; without Redis, Hunter state falls back to process memory and may be lost when the free service sleeps or restarts.

## Release gates

This blueprint and the Firebase adapter alone do not constitute a completed deployment. No Firebase project credentials are available to this coding session, so the live account has not been connected or verified. Before calling the live corpus operational:
1. Make Redis and Meilisearch optional or provide free hosted equivalents; add a PostgreSQL search fallback.
2. Run database migrations against the Supabase database.
3. Set `BACKEND_API_URL` in the Vercel production environment to the Render service URL (for example, `https://gikuyu-archive-api.onrender.com`), then redeploy the frontend. Keep `FRONTEND_URL` aligned with the actual public website origin. Set `BACKEND_URL` to the actual Render URL if the generated service hostname differs.
4. Run `alembic upgrade head` from the backend directory against the configured Supabase database before exposing write routes.
5. Verify registration/login, a Gĩkũyũ text submission, persistence after redeploy, audio upload and retrieval, researcher export, Hunter ingestion, and takedown deletion/search invisibility.
6. Verify scheduled Hunter jobs and their durable frontier; do not rely on in-process scheduling on a free service that spins down. Without Redis, the frontier is not durable.
7. Confirm the production health endpoint reports persistence as configured only after a real database check succeeds.

Free tiers have quotas and provider terms can change. This stack is a zero-cost starting point, not a promise of unlimited or always-on production infrastructure.
