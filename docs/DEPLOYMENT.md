# Deployment

## Backend — Railway

The initial Railway deployment intentionally uses the lightweight backend dependency set only. It provides the API, policy service, structured review fallback and health endpoint while the project-specific CV checkpoint is still being trained.

### Container
The repository-root `Dockerfile`:
- uses Python 3.12
- installs `backend/requirements.txt`
- copies backend code and structured policy data
- starts FastAPI with Railway's `PORT`

### Required environment variables

```text
RETURNREVIEW_ENV=production
RETURNREVIEW_DATABASE_URL=sqlite:///./returnreview.db
RETURNREVIEW_STORAGE_DIR=./storage
RETURNREVIEW_ALLOWED_ORIGINS=<frontend production origin>
RETURNREVIEW_DEMO_MODE=true
RETURNREVIEW_CV_MODEL_VERSION=untrained
RETURNREVIEW_LLM_ENABLED=false
```

The first hosted skeleton uses ephemeral SQLite/file storage. It is suitable for API/deployment verification but **not final persistent case storage**. Persistence will move only after either:
1. a safely isolated Project Hub `return_review` schema/storage setup is approved and implemented, or
2. another dedicated persistent store is intentionally selected.

### CV deployment
Do not install `requirements-cv.txt` or publish a fake checkpoint just to make the inspection route appear available. After real training:
- package the validated checkpoint and calibrated prototype bank through an appropriate model-artifact workflow,
- measure CPU/RAM latency,
- then choose CPU hosting or a separate inference service based on measured requirements.

## Frontend — Vercel

Deploy `frontend/` as the project root and set:

```text
NEXT_PUBLIC_API_BASE_URL=https://<returnreview-backend>
```

Then update backend CORS to the exact Vercel production origin and rerun the end-to-end flow.
