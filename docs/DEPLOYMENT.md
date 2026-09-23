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

The final persistence architecture is now provisioned in the shared Supabase Project Hub, isolated to **App 13 / `return_review`**.

Provisioned:
- private `return_review` schema
- seven application tables
- RLS on every ReturnReview table
- dedicated `return_review_backend` role with no cross-app privileges
- schema/table/role ownership registered in `hub.app_resources`
- persistent evidence/overlay byte columns
- application support for Postgres + DB-backed media serving

The live Railway API still uses its previous SQLite URL until the dedicated role credential is set securely. This is deliberate: production does **not** claim durable persistence until the real connection is activated and verified across a redeploy.

See `docs/PERSISTENCE.md` for the secret-only activation and rollback procedure.

### Current feature flags

```text
RETURNREVIEW_ENV=production
RETURNREVIEW_DEMO_MODE=true
RETURNREVIEW_CV_MODEL_VERSION=untrained
RETURNREVIEW_LLM_ENABLED=false
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
