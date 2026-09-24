# Durable Persistence

## Goal

ReturnReview must preserve cases, audit history, uploaded evidence, and generated overlays across Railway redeploys without sharing another application's data.

## Production architecture

~~~text
Browser
  ↓
ReturnReview web (Railway)
  ↓
ReturnReview API (Railway)
  ↓ private Railway service reference
ReturnReview Postgres (Railway)
  ↓
postgres-volume
~~~

All production runtime resources remain inside the isolated Railway project **ReturnReview**.

Canonical database resources:
- project: `ReturnReview`
- project ID: `3b5a435b-a0ca-43c0-85c0-9783073a8cd4`
- database service: `Postgres`
- database service ID: `02cc5aaf-b427-48d8-bfdd-488a1d714daf`
- persistent volume: `postgres-volume`
- volume ID: `6114b26f-88d5-40d9-ad53-b1de917bc703`
- mount path: `/var/lib/postgresql/data`
- public database domain: none

The backend stores durable evidence bytes in Postgres:
- `case_images.image_blob`
- `defect_findings.mask_blob`

A temporary local copy may still be recreated when YOLO/OpenCLIP needs a filesystem path; the database remains the intended durable source of truth.

## API configuration

`returnreview-api` uses a Railway reference rather than a copied database password:

~~~text
RETURNREVIEW_DATABASE_URL=${{Postgres.DATABASE_URL}}
RETURNREVIEW_DATABASE_SCHEMA=public
~~~

Railway resolves the database reference internally. Do not copy or expose the resolved credential in chat, GitHub, frontend variables, screenshots, or documentation.

## Verification gate

Do not call persistence complete merely because Postgres exists.

Required proof:
1. API deployment succeeds with PostgreSQL configured.
2. `/health` reports `database_backend=postgresql`.
3. `/health` reports `durable_persistence=true`.
4. `/readiness` reports database OK.
5. create a temporary ReturnReview case.
6. upload a valid 2–4 image evidence set.
7. confirm the case and media are retrievable.
8. redeploy only `returnreview-api`.
9. reload the same case and evidence.
10. confirm they survived.

Only then mark durable persistence complete.

## Verified production proof

Completed on 2026-09-24 using case `PERSISTENCE-PROOF-01`:
- created the case on production PostgreSQL
- uploaded two valid evidence images (`left` and `front`)
- confirmed both media endpoints rendered before redeploy
- redeployed only `returnreview-api`
- deployment `0522dc2b-5a35-4757-993b-56d067d3cb91` completed successfully
- reloaded the same case after redeploy
- the same case, both images, and all three audit events remained available

Durable Railway Postgres persistence is therefore verified end to end.

## Supabase history

A previously provisioned Supabase Project Hub App 13 foundation still exists:
- schema `return_review`
- seven ReturnReview tables
- dedicated `return_review_backend` role
- role-scoped RLS policies

Those resources are retained and untouched for safety/history. They are **not** the intended production runtime database after the Railway migration. Do not delete or modify them without a separate explicit retirement/migration decision.

## Recovery

If the Railway Postgres API activation fails:
- do not delete the Railway database or volume
- restore the previous SQLite URL only as a temporary rollback
- redeploy only `returnreview-api`
- inspect logs and private-network/reference configuration
- do not modify unrelated Railway projects or the retained Supabase foundation

SQLite is a development/recovery fallback, not the final hosted persistence target.
