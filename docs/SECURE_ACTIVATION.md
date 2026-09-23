# Secure Production Activation

**Never paste database passwords or API keys into chat, GitHub, screenshots, docs, or frontend variables.**

## Part A — Railway Postgres

The production database is the dedicated Postgres service inside the isolated **ReturnReview** Railway project.

Already provisioned:
- Postgres service ID: `02cc5aaf-b427-48d8-bfdd-488a1d714daf`
- volume ID: `6114b26f-88d5-40d9-ad53-b1de917bc703`
- private networking
- no public database domain

The API should use Railway reference variables:

~~~text
RETURNREVIEW_DATABASE_URL=${{Postgres.DATABASE_URL}}
RETURNREVIEW_DATABASE_SCHEMA=public
~~~

No database password needs to be copied into chat or source.

After deployment verify:
- `/health` → `database_backend=postgresql`
- `/health` → `durable_persistence=true`
- `/readiness` → database OK
- logs show PostgreSQL rather than SQLite

Then run the redeploy persistence proof described in `docs/PERSISTENCE.md`.

## Part B — Gemini

Gemini still requires one private backend secret:

Railway → **ReturnReview** → **returnreview-api** → Variables

~~~text
RETURNREVIEW_GEMINI_API_KEY=<private key>
RETURNREVIEW_GEMINI_MODEL=gemini-3.8-flash
RETURNREVIEW_LLM_ENABLED=true
~~~

The key belongs only on the backend service. Do not put it on `returnreview-web`.

After redeployment:
- `/health` should report LLM enabled
- `/readiness` should no longer include `gemini_not_enabled`

Then run the fixed Gemini evaluation and manually review every generated row before publishing metrics.

## Retained Supabase foundation

The previous Supabase App 13 resources remain intact but are no longer the intended production database. Do not delete them as part of normal Railway activation.

## Rollback

If Railway Postgres activation fails:
- restore the prior SQLite database URL temporarily
- redeploy only the API
- keep the Railway Postgres volume intact
- investigate without exposing credentials

If Gemini fails:
- set `RETURNREVIEW_LLM_ENABLED=false`
- keep the deterministic fallback
- investigate without exposing the API key
