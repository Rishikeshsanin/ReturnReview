# Railway Project Hub Rules — ReturnReview

## Identity
- Application: ReturnReview
- Hub app number: App 02
- Hub slug: `return_review`
- Repository: `https://github.com/Rishikeshsanin/ReturnReview`
- Railway project: `ReturnReview`
- Railway project ID: `3b5a435b-a0ca-43c0-85c0-9783073a8cd4`
- Production environment: `production`
- Registered production services: `returnreview-api`, `returnreview-web`
- Canonical Hub repository: `https://github.com/Rishikeshsanin/railway-project-hub`

## Mandatory read-first rule
Before any Railway change for ReturnReview:
1. Read the canonical Railway Project Hub `README.md`, `AGENTS.md`, and `RAILWAY_HUB_RULES.md`.
2. Read this file and this repository's `AGENTS.md`.
3. Verify the exact Railway project, environment, target service, source repository, domain, variable names, volumes, and deployment status.
4. Operate only inside resources registered to ReturnReview.

If the canonical Hub repository is unavailable, do not create, delete, migrate, reconnect, or reconfigure Railway infrastructure. Read-only inspection is allowed.

## Allowed scope
ReturnReview may modify only its own:
- Railway project and environments
- `returnreview-api` and `returnreview-web`
- app-specific variables and secrets
- domains
- app-specific volumes/databases if explicitly registered
- GitHub deployment connections
- app-specific monitoring

## Forbidden scope
Never:
- modify another application's Railway project, service, deployment, variables, secrets, domain, volume, database, or GitHub connection
- copy secrets from another app
- use another app's Railway project because it has spare capacity
- create cross-app dependencies without explicit user approval and Hub documentation
- make organization-wide/shared-infrastructure changes for a ReturnReview task
- expose secrets in GitHub, logs, screenshots, URLs, frontend code, or chat
- treat a similarly named service as belonging to ReturnReview without registry verification

## Production safety
Use:
`read → identify → verify → plan → change → test → verify`.

For destructive or production-impacting actions, inspect dependencies and rollback first and obtain explicit user confirmation immediately before execution.

## Current architecture
The canonical ReturnReview deployment is the standalone Railway project `ReturnReview` with:
- `returnreview-api`
- `returnreview-web`

Any `app01-motionlab` service or Hub metadata currently found inside the ReturnReview project is known migration residue from an earlier Hub experiment. It is **not** part of ReturnReview's intended runtime architecture and must not be modified or deleted until the canonical Hub exists and the documented cleanup process is approved.

ReturnReview currently has no active Railway volume. Hosted SQLite/uploads are ephemeral until durable persistence is deliberately implemented.

## New resources
No new Railway resource may be created for ReturnReview until it is documented in the canonical Hub registry with owner, purpose, environment, expected name, and isolation boundary.

## Safety priority
`Isolation > Security > Recoverability > Maintainability > Convenience`.
