# ReturnReview Agent Safety Contract

This repository is the only application scope for **ReturnReview**.

## Identity
- Application: ReturnReview
- Intended Project Hub slug: `return_review`
- Intended Project Hub schema: `return_review`
- Repository: `https://github.com/Rishikeshsanin/ReturnReview`

## Mandatory rules
1. Read `SUPABASE_HUB_RULES.md` before any Supabase write.
2. Treat every other Project Hub application as unrelated and out of scope.
3. Never modify another repository, schema, table, function, policy, bucket, edge function, auth setting, key, or app data.
4. Use fully-qualified `return_review.<object>` names for ReturnReview database objects.
5. Never create ReturnReview application tables in `public`.
6. Never use destructive/unscoped database operations.
7. Never expose or commit secrets.
8. The Project Hub project-level service-role/secret key is not an application credential and must not be used by ReturnReview.
9. Run security checks after meaningful database/RLS changes.
10. Stop before any operation that could affect shared/project-wide infrastructure.

## Current persistence state
ReturnReview currently uses local SQLite/local storage. The shared Project Hub is not connected to the application yet.
