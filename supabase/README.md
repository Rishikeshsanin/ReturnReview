# ReturnReview Supabase Persistence

ReturnReview is registered in the shared Supabase Project Hub as **App 13**.

## Fixed identity

- Project Hub project ref: `nowlwprtcnieihelqjoa`
- App number: `13`
- App slug: `return_review`
- Private schema: `return_review`
- Backend database role: `return_review_backend`

The Project Hub itself is shared. ReturnReview resources are not.

## Isolation contract

ReturnReview uses only:

- `return_review.*`
- the dedicated `return_review_backend` database role
- resources registered to ReturnReview in `hub.app_resources`

It does **not** use:

- application tables in `public`
- another application's schema
- the project-level Supabase service-role/secret key
- Supabase Storage
- cross-app foreign keys, views, triggers, RPCs, or functions

## Current database objects

The canonical DDL is in:

`supabase/migrations/001_return_review_persistence.sql`

It defines the seven application tables used by the FastAPI/SQLAlchemy backend and enables RLS on each table. Policies target only `return_review_backend`.

Evidence JPEGs and generated overlay JPEGs are stored as `bytea` alongside their metadata. Local Railway disk is therefore only an inference/cache layer once production PostgreSQL is activated.

## Credential activation

The database role intentionally has no credential committed here.

Set its password securely in Supabase, then configure the Railway backend using a connection string stored only in Railway variables. Never commit or paste the password into source, docs, issues, screenshots, or chat.

See `docs/PERSISTENCE.md`.
