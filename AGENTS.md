# ReturnReview Agent Safety Contract

This repository is the only application scope for **ReturnReview**.

## Identity
- Application: ReturnReview
- Railway Hub app number: App 02
- Railway Hub slug: `return_review`
- Intended Supabase Project Hub slug: `return_review`
- Intended Supabase Project Hub schema: `return_review`
- Repository: `https://github.com/Rishikeshsanin/ReturnReview`
- Railway project: `ReturnReview`

## Mandatory Railway rules
1. Read `RAILWAY_HUB_RULES.md` and the canonical Railway Project Hub documentation before any Railway write.
2. Treat every other Railway application as a separate customer and out of scope.
3. Never modify another application's project, environment, service, deployment, variable, secret, domain, database, volume, or GitHub connection.
4. Do not create new Railway projects/services/resources until the Hub registry and required documentation exist first.
5. Prefer read-only inspection before writes and reversible changes before destructive changes.
6. Never expose or commit secrets.
7. Stop if scope is ambiguous or a change could affect shared/project-wide infrastructure.
8. Verify deployment health and application behavior after meaningful Railway changes.
9. Destructive or production-impacting operations require explicit user confirmation immediately before execution.

## Mandatory Supabase rules
1. Read `SUPABASE_HUB_RULES.md` before any Supabase write.
2. Treat every other Supabase Project Hub application as unrelated and out of scope.
3. Never modify another repository, schema, table, function, policy, bucket, edge function, auth setting, key, or app data.
4. Use fully-qualified `return_review.<object>` names for ReturnReview database objects.
5. Never create ReturnReview application tables in `public`.
6. Never use destructive/unscoped database operations.
7. The Supabase Project Hub project-level service-role/secret key is not an application credential and must not be used by ReturnReview.
8. Run security checks after meaningful database/RLS changes.

## Current persistence state
ReturnReview is registered as Supabase Project Hub **App 13** with private schema `return_review`.

Provisioned ReturnReview-owned resources:
- seven tables in `return_review`
- dedicated `return_review_backend` login role
- RLS policies scoped to that role
- Hub resource-registry entries

Production Railway remains on SQLite until the dedicated database-role password and connection URL are set securely. Never substitute the Project Hub `postgres` password or service-role/secret key. The canonical Railway runtime remains the standalone `ReturnReview` project.
