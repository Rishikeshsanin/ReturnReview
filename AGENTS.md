# ReturnReview Agent Safety Contract

This repository is the only application scope for **ReturnReview**.

## Identity
- Application: ReturnReview
- Railway Hub app number: App 02
- Railway Hub slug: `return_review`
- Retained Supabase Project Hub slug/schema: `return_review` (inactive historical foundation; not production runtime)
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
The intended production persistence target is the dedicated Railway Postgres service inside the standalone **ReturnReview** Railway project.

Canonical Railway persistence resources:
- Postgres service ID: `02cc5aaf-b427-48d8-bfdd-488a1d714daf`
- persistent volume ID: `6114b26f-88d5-40d9-ad53-b1de917bc703`
- private networking only; no public database domain
- API connection must use Railway reference/private variables, not copied credentials

The earlier Supabase Project Hub App 13 schema/role/tables remain intact but are not the production runtime target. Do not modify or delete them without a separate scoped migration/retirement decision.
