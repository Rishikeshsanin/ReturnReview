# ReturnReview — Project Hub Rules

This file exists to satisfy the repository-side safety contract required before ReturnReview may receive any Project Hub resources.

## Registered identity
ReturnReview is registered in Project Hub as:
- app number: **13**
- app slug: `return_review`
- schema: `return_review`
- repository: `https://github.com/Rishikeshsanin/ReturnReview`
- backend DB role: `return_review_backend`

## Isolation
- ReturnReview may access only its own registered schema/resources plus explicitly approved shared resources.
- Never create application tables in `public`.
- Never reference another app schema with foreign keys, views, triggers, RPCs or application logic.
- Every SQL statement must use fully-qualified schema/object names where applicable.
- Never run `DROP SCHEMA ... CASCADE`, unscoped `DROP`, `TRUNCATE`, `DELETE` or `ALTER`.
- Never change project-wide Auth/OAuth, keys, region, plan, extensions or other shared configuration for ReturnReview without an explicit impact review.

## Security
- Enable and test RLS on every user-facing table.
- Storage buckets, RPCs, functions, realtime channels and edge functions must be ReturnReview-prefixed and registered as ReturnReview resources.
- Do not use the Project Hub service-role/secret key in ReturnReview.
- Do not commit DB passwords, API keys, secrets or credentials.
- Run Supabase security advisors after meaningful DDL/RLS work.

## Change procedure
Before the first Project Hub write:
1. Re-read `hub.read_me_first`.
2. Verify that a `hub.apps` record exists for `return_review` and its schema is exactly `return_review`.
3. Verify this repository contains both `AGENTS.md` and `SUPABASE_HUB_RULES.md`.
4. Inspect only ReturnReview's own schema/resources.
5. Apply small, scoped changes.
6. Verify RLS/security and record the resource/migration in the Hub registry where required.

## Current state
Provisioned and verified:
- `hub.apps` registration for App 13
- private `return_review` schema
- seven ReturnReview application tables
- RLS enabled on every ReturnReview table
- policies targeted only to `return_review_backend`
- dedicated non-superuser/non-bypass-RLS backend login role
- schema/table/role records in `hub.app_resources`

Not created:
- no ReturnReview tables in `public`
- no Supabase Storage bucket
- no edge function/RPC/realtime resource
- no cross-app dependency

The backend role password is intentionally not stored in this repository. Production activation must use the dedicated role and never the Project Hub admin/service-role credential.
