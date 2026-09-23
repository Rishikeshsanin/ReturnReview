# Deployment

## Production URLs

- Web: `https://returnreview-web-production.up.railway.app`
- API: `https://returnreview-api-production.up.railway.app`
- API health: `https://returnreview-api-production.up.railway.app/health`

Both services live in the isolated Railway project **ReturnReview**.

## Backend — Railway

Service: `returnreview-api`

Verified configuration:
- repository: `Rishikeshsanin/ReturnReview`
- branch: `main`
- healthcheck: `/health`
- restart policy: on failure
- watch paths limited to backend/data/container files
- exact hosted frontend origin included in CORS
- current deployment healthcheck returned HTTP 200

### Current persistence status

The intended production persistence architecture is the dedicated Railway Postgres service inside the isolated **ReturnReview** project.

Provisioned:
- Postgres service ID `02cc5aaf-b427-48d8-bfdd-488a1d714daf`
- persistent volume ID `6114b26f-88d5-40d9-ad53-b1de917bc703`
- private Railway networking
- no public database domain
- application support for PostgreSQL + DB-backed media serving

The API uses a Railway service-reference database URL rather than a copied password. The PostgreSQL deployment is now healthy: production startup reports `database_backend=postgresql` and `durable_persistence=True`, and both `/health` and `/readiness` return HTTP 200. Final persistence proof still requires a case + evidence to survive an API redeploy.

The older Supabase App 13 foundation is retained but is not the intended production runtime database.

See `docs/PERSISTENCE.md` for verification and rollback.

### Current feature flags

```text
RETURNREVIEW_ENV=production
RETURNREVIEW_DEMO_MODE=true
RETURNREVIEW_CV_MODEL_VERSION=untrained
RETURNREVIEW_LLM_ENABLED=false
RETURNREVIEW_DATABASE_SCHEMA=public
```

This is intentional. Production must not pretend an untrained model is available.

## Frontend — Railway

Service: `returnreview-web`

Verified configuration:
- repository: `Rishikeshsanin/ReturnReview`
- branch: `main`
- root directory: `/frontend`
- Dockerfile: `frontend/Dockerfile`
- Next.js standalone production output
- healthcheck: `/`
- backend URL: `https://returnreview-api-production.up.railway.app`
- deployed container healthcheck succeeded

## Preferred optional frontend target — Vercel

Vercel remains a suitable frontend alternative. The connected automation can inspect existing projects but did not expose a safe create-new-project action, so no unrelated Vercel project was touched.

To switch later:
1. Import `Rishikeshsanin/ReturnReview` as a **new** Vercel project.
2. Set project root to `frontend`.
3. Set `NEXT_PUBLIC_API_BASE_URL=https://returnreview-api-production.up.railway.app`.
4. Add the new Vercel production origin to backend CORS.
5. Verify the full E2E flow before retiring the Railway web service.

## CV deployment

Do not deploy an untrained checkpoint. After real training:
1. validate held-out metrics,
2. calibrate OpenCLIP thresholds,
3. measure CPU/RAM latency,
4. package only the approved checkpoint/prototype bank,
5. choose current CPU backend vs separate inference service using measured runtime data.

### CV artifact release package

After training, held-out evaluation, and validation-set threshold calibration,
package the **approved** model artifacts with exact checksums:

~~~bash
python scripts/package_cv_release.py \
  --checkpoint /path/to/best.pt \
  --prototypes /path/to/prototypes.npz \
  --model-version returnreview-cv-v1 \
  --category-threshold <VALIDATION_VALUE> \
  --defect-threshold <VALIDATION_VALUE> \
  --defect-margin <VALIDATION_VALUE>
~~~

The command fails if the checkpoint/prototype bank is missing or the prototype
keys do not match the runtime contract. The generated
`artifacts/cv-release/release_manifest.json` records checksums and thresholds
but deliberately contains no invented evaluation metrics.

Do not switch the hosted API to the heavy CV runtime until CPU/RAM/latency is
measured on the approved package.

## Gemini deployment

Do not commit or send the API key in chat. Add it directly to the backend environment:

```text
RETURNREVIEW_GEMINI_API_KEY=<secret>
RETURNREVIEW_LLM_ENABLED=true
```

Then run the fixed LLM evaluation set before calling the hosted review path production-ready.
