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

The backend currently uses ordinary local SQLite/file storage inside its Railway container:

```text
RETURNREVIEW_DATABASE_URL=sqlite:///./returnreview.db
RETURNREVIEW_STORAGE_DIR=./storage
```

This is **not claimed as persistent across redeploys**.

A 1 GB Railway volume was staged and committed during deployment work, but Railway's authoritative service configuration still reported `hasVolume=false` afterward. The project therefore treats hosted persistence as unfinished rather than pretending the volume is active.

The shared Supabase Project Hub remains untouched except for read-only inspection.

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

## Gemini deployment

Do not commit or send the API key in chat. Add it directly to the backend environment:

```text
RETURNREVIEW_GEMINI_API_KEY=<secret>
RETURNREVIEW_LLM_ENABLED=true
```

Then run the fixed LLM evaluation set before calling the hosted review path production-ready.
