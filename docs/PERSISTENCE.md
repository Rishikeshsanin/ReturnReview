# Durable Persistence

## Goal

ReturnReview must preserve cases, audit history, uploaded evidence, and generated overlays across Railway redeploys without sharing another application's data.

## Architecture

~~~text
Browser
  ↓
ReturnReview web (Railway)
  ↓
ReturnReview API (Railway)
  ↓
dedicated DB role: return_review_backend
  ↓
Supabase Project Hub Postgres
  ↓
private schema: return_review
~~~

The backend still writes a temporary local copy of evidence files so YOLO/OpenCLIP can consume ordinary file paths. The durable copy is stored in Postgres:

- `case_images.image_blob`
- `defect_findings.mask_blob`

The UI serves those bytes through case-scoped FastAPI media endpoints. A Railway container restart can therefore recreate local inference files from the database when needed.

## Provisioned state

Already completed:

- ReturnReview registered as Supabase Hub App 13
- `hub.assert_app_scope('return_review','return_review')` passed
- private `return_review` schema created
- seven ReturnReview tables created
- RLS enabled on every ReturnReview table
- policies scoped to `return_review_backend`
- dedicated non-superuser/non-bypass-RLS login role created
- schema, role, and tables registered in `hub.app_resources`
- Supabase security advisor checked after DDL
- no ReturnReview-specific security advisory remains from this foundation

## Production activation — secret-only step

The connected automation cannot set a database-role password. Do this manually without sharing the password:

1. In the Supabase SQL editor for Project Hub, set a strong password for `return_review_backend`.
2. In Railway → ReturnReview → `returnreview-api` → Variables, set:
   - `RETURNREVIEW_DATABASE_SCHEMA=return_review`
   - `RETURNREVIEW_DATABASE_URL=<dedicated return_review_backend PostgreSQL URL>`
3. Use SSL and the Supavisor **session pooler** (port 5432) if the Railway network needs IPv4.
4. Do not use the `postgres` role password or Supabase service-role key.
5. Redeploy only `returnreview-api`.
6. Verify `/health` reports `database_backend=postgresql` and `durable_persistence=true`.
7. Verify `/readiness` reports database OK.
8. Create a test case + image, redeploy the API, and confirm both still exist afterward.
9. Remove the test case only if explicitly desired; do not run unscoped deletes.

A pooled URL commonly follows this shape:

`postgresql+psycopg://<ROLE>.<PROJECT_REF>:<URL_ENCODED_PASSWORD>@<SUPAVISOR_HOST>:5432/postgres?sslmode=require`

Copy the exact host/format from Supabase **Connect** instead of guessing it.

## Recovery

If PostgreSQL activation fails:

- keep the isolated Supabase schema intact
- restore `RETURNREVIEW_DATABASE_URL` to the previous SQLite value
- leave `RETURNREVIEW_DATABASE_SCHEMA` harmlessly configured or remove it
- redeploy only ReturnReview API
- investigate connection/authentication without modifying another app

The SQLite fallback is for recovery/development; it is not the final hosted persistence target.
