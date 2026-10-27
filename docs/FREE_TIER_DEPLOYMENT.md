# Free-tier deployment plan

This project must not rely on Render's free PostgreSQL database for permanent corpus data: Render documents that free PostgreSQL databases expire after 30 days. The selected no-cost starting stack is:

- **Supabase Free**: durable PostgreSQL database and object storage for corpus metadata and permitted media.
- **Render Free Web Service**: run the existing Python/FastAPI backend. Expect cold starts after 15 minutes idle; this is suitable for a low-traffic launch preview, not a high-availability guarantee.
- **GitHub Actions**: run bounded scheduled Hunter jobs and CI without requiring a permanently running paid worker.
- **Existing Vercel deployment**: continue serving the Next.js frontend.
- **PostgreSQL search fallback**: prefer database-backed search where a separate hosted Meilisearch service is unavailable. Never treat a missing search service as evidence that an item does not exist.

Official limits and pricing:
- Render free service limitations and the 30-day free Postgres expiry: https://render.com/docs/free
- Supabase free plan: https://supabase.com/pricing
- Cloudflare's free D1/R2 alternative, should the application later move to a serverless architecture: https://developers.cloudflare.com/workers/platform/pricing/

## Configuration

The Render blueprint in `/render.yaml` declares the backend and marks account-specific values as secrets instead of committing credentials. The Supabase project owner must create a project, create the audio/text storage buckets, obtain the PostgreSQL connection string and S3-compatible storage credentials, then enter those values into the Render service's environment settings. Never paste credentials into GitHub issues, commits, or chat.

Required values:
- `DATABASE_URL`: Supabase PostgreSQL connection string compatible with asyncpg; use the provider's recommended connection endpoint.
- `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`: Supabase Storage S3 endpoint and generated S3 credentials.
- `MEILISEARCH_URL`, `MEILISEARCH_KEY`, `REDIS_URL` are optional in this branch. Without Meilisearch, the API falls back to PostgreSQL text search; without Redis, Hunter state falls back to process memory and may be lost when the free service sleeps or restarts.

## Release gates

This blueprint alone is not a completed deployment. Before calling the live corpus operational:
1. Make Redis and Meilisearch optional or provide free hosted equivalents; add a PostgreSQL search fallback.
2. Run database migrations against the Supabase database.
3. Set `BACKEND_API_URL` in the Vercel production environment to the Render service URL (for example, `https://gikuyu-archive-api.onrender.com`), then redeploy the frontend. Keep `FRONTEND_URL` aligned with the actual public website origin. Set `BACKEND_URL` to the actual Render URL if the generated service hostname differs.
4. Run `alembic upgrade head` from the backend directory against the configured Supabase database before exposing write routes.
5. Verify registration/login, a Gĩkũyũ text submission, persistence after redeploy, audio upload and retrieval, researcher export, Hunter ingestion, and takedown deletion/search invisibility.
6. Verify scheduled Hunter jobs and their durable frontier; do not rely on in-process scheduling on a free service that spins down. Without Redis, the frontier is not durable.
7. Confirm the production health endpoint reports persistence as configured only after a real database check succeeds.

Free tiers have quotas and provider terms can change. This stack is a zero-cost starting point, not a promise of unlimited or always-on production infrastructure.
