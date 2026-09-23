# Secure Production Activation

This is the only manual secret-handling step left in ReturnReview's hosted stack.

**Never paste database passwords or API keys into chat, GitHub, screenshots, docs, or frontend variables.**

## Part A — Activate durable Supabase Postgres

Already verified:
- Supabase Project Hub App 13: `return_review`
- private schema: `return_review`
- dedicated role: `return_review_backend`
- role is login-enabled, non-superuser, non-bypass-RLS
- seven ReturnReview tables exist
- RLS is enabled on all seven
- role-scoped policies exist on all seven
- no ReturnReview-specific security-advisor finding was observed

### 1. Set the dedicated role password

In the Supabase **Project Hub** SQL editor, choose your own strong password and run:

~~~sql
alter role return_review_backend
with password 'YOUR_PRIVATE_STRONG_PASSWORD';
~~~

Do not reuse the Project Hub `postgres` password.

### 2. Build the dedicated-role connection string

Railway outbound IPv6 is now enabled **only on `returnreview-api`**, so the preferred production connection is the Supabase direct Postgres endpoint:

- host: `db.nowlwprtcnieihelqjoa.supabase.co`
- port: `5432`
- database: `postgres`
- role: `return_review_backend`
- SSL: required

Use the private password you assigned in step 1. URL-encode it if necessary.

If direct IPv6 connectivity is ever unavailable, use the exact **Session pooler** string shown by Supabase Connect as the fallback. Do not guess a pooler region/host.

### 3. Configure only ReturnReview API in Railway

Outbound IPv6 is already enabled and verified on `returnreview-api`; do not enable it globally or on unrelated projects.

Railway → **ReturnReview** → **returnreview-api** → Variables:

- `RETURNREVIEW_DATABASE_SCHEMA=return_review`
- `RETURNREVIEW_DATABASE_URL=<your dedicated-role PostgreSQL URL>`

Do not put the URL in `returnreview-web`.

### 4. Redeploy only returnreview-api

After deployment, verify:
- `/health` → `database_backend=postgresql`
- `/health` → `durable_persistence=true`
- `/readiness` → database OK
- logs no longer say `database_backend=sqlite`

### 5. Persistence proof

1. create a temporary ReturnReview case
2. upload a valid 2–4 image evidence set
3. confirm the case appears
4. redeploy only `returnreview-api`
5. reload the case
6. verify case metadata and stored evidence still exist

This proves Railway ephemeral disk is no longer the source of truth.

## Part B — Activate Gemini

Railway → **ReturnReview** → **returnreview-api** → Variables:

- `RETURNREVIEW_GEMINI_API_KEY=<your private Gemini key>`
- `RETURNREVIEW_GEMINI_MODEL=gemini-3.8-flash`
- `RETURNREVIEW_LLM_ENABLED=true`

The key belongs only on the backend service.

After redeployment:
- `/health` should report LLM enabled
- `/readiness` should no longer include `gemini_not_enabled`

Then run the fixed evaluation scenarios and manually review the outputs before publishing metrics.

## Rollback

If Postgres activation fails:
- restore the prior SQLite database URL
- redeploy only the API
- leave the isolated Supabase schema untouched while troubleshooting

If Gemini fails:
- set `RETURNREVIEW_LLM_ENABLED=false`
- keep the deterministic fallback
- investigate without exposing the API key

## What ChatGPT can verify after you finish this page

Once the secret values are saved in the dashboards, tell ChatGPT only:

> secure activation done

Do **not** send the values.

ChatGPT can then inspect variable **names**, deployment logs, health/readiness, and persistence behaviour without seeing the secrets.
