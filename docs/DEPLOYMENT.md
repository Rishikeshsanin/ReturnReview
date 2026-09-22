# Deployment

## Backend — Railway

ReturnReview has an isolated Railway project/service:

- service: `returnreview-api`
- public API: `https://returnreview-api-production.up.railway.app`
- healthcheck: `/health`
- source: `Rishikeshsanin/ReturnReview` → `main`

The hosted API intentionally uses the lightweight backend dependency set while the project-specific CV model is still being trained.

### Persistent data

A dedicated **1 GB ReturnReview-only Railway volume** is mounted at:

```text
/data
```

Production persistence uses:

```text
RETURNREVIEW_DATABASE_URL=sqlite:////data/returnreview.db
RETURNREVIEW_STORAGE_DIR=/data/storage
```

The running container has been verified to contain both `/data/returnreview.db` and `/data/storage`. This avoids using the shared Project Hub Supabase for ordinary hosted persistence and keeps ReturnReview isolated.

### Current production feature flags

```text
RETURNREVIEW_ENV=production
RETURNREVIEW_DEMO_MODE=true
RETURNREVIEW_CV_MODEL_VERSION=untrained
RETURNREVIEW_LLM_ENABLED=false
```

CV and Gemini are deliberately disabled until their real project inputs are available.

### CV deployment

Do not install `requirements-cv.txt` or publish a fake checkpoint just to make the inspection route appear available. After real training:

1. validate the checkpoint and calibrated prototype bank on held-out data,
2. measure CPU/RAM inference latency,
3. package the approved artifacts,
4. then decide whether the current CPU service is sufficient or a separate inference service is justified.

## Frontend

### Preferred final target — Vercel

The preferred final frontend target remains Vercel. Import this repository as a **new** Vercel project and set the project root to:

```text
frontend
```

Set:

```text
NEXT_PUBLIC_API_BASE_URL=https://returnreview-api-production.up.railway.app
```

Never reuse or reconfigure an unrelated existing Vercel project.

### Isolated Railway fallback

The repository also contains `frontend/Dockerfile` with Next.js standalone output so the web UI can be hosted as a second service inside the isolated ReturnReview Railway project. This is useful when Vercel project creation is not available through the connected automation.

After the final frontend domain exists, set backend CORS to that exact origin and run the full create-case → upload → inspect/review → human-decision flow.
