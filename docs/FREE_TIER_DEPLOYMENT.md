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
- `MEILISEARCH_URL`, `MEILISEARCH_KEY`, `REDIS_URL`: only if those optional services remain enabled in the backend. They must not be left blank if the code still treats them as mandatory.

## Release gates

This blueprint alone is not a completed deployment. Before calling the live corpus operational:
1. Make Redis and Meilisearch optional or provide free hosted equivalents; add a PostgreSQL search fallback.
2. Run database migrations against the Supabase database.
3. Configure backend URL and CORS in Vercel and Render.
4. Verify registration/login, a Gĩkũyũ text submission, persistence after redeploy, audio upload and retrieval, researcher export, Hunter ingestion, and takedown deletion/search invisibility.
5. Verify scheduled Hunter jobs and their durable frontier; do not rely on in-process scheduling on a free service that spins down.
6. Confirm the production health endpoint reports persistence as configured only after a real database check succeeds.

Free tiers have quotas and provider terms can change. This stack is a zero-cost starting point, not a promise of unlimited or always-on production infrastructure.
