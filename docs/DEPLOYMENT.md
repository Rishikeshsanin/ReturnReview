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

The API uses a Railway service-reference database URL rather than a copied
password. PostgreSQL is healthy with `database_backend=postgresql`,
`durable_persistence=True`, and schema `public`. `/health` and `/readiness`
return HTTP 200. Production smoke testing has also verified that a case, image
evidence, CV inspection, review, and audit history remain available after
persisted reload; this is the current durable-persistence proof.

The older Supabase App 13 foundation is retained but is not the intended production runtime database.

See `docs/PERSISTENCE.md` for verification and rollback.

### Current feature flags

```text
RETURNREVIEW_ENV=production
RETURNREVIEW_DEMO_MODE=true
RETURNREVIEW_CV_MODEL_VERSION=cv-lightweight-1
RETURNREVIEW_LLM_ENABLED=true
RETURNREVIEW_DATABASE_SCHEMA=public
RETURNREVIEW_GEMINI_MODEL=gemini-3.8-flash
RETURNREVIEW_GEMINI_FALLBACK_MODEL=gemini-3.5-flash
```

The Gemini API key and database URL are server-side Railway variables and must
never be copied into documentation, logs, or commits.

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

Production currently runs `cv-lightweight-1` in the API container. It uses
MobileNetV3-Small category verification and multiclass YOLO11n-seg; OpenCLIP
and prototype-bank files are not part of the production inference contract.
The controlled-adapted experiment remains explicitly undeployed.

### CV artifact release package

For a future lightweight candidate, package the **approved** artifacts with
their held-out metrics and runtime benchmark:

~~~bash
python scripts/package_lightweight_cv_release.py \
  --segmentation /path/to/best.pt \
  --category /path/to/category_mobilenet_v3_small.pt \
  --segmentation-metrics /path/to/segmentation_metrics.json \
  --category-metrics /path/to/category_metrics.json \
  --runtime-benchmark /path/to/runtime_benchmark.json \
  --model-version <NEW_VERSION> \
  --output-dir /path/to/release
~~~

The generated manifest records exact filenames, byte sizes, checksums, runtime
class mapping, and public-pilot limitations. `Dockerfile.cv` installs the
current release at these runtime paths:

```text
/app/backend/models/checkpoints/best.pt
/app/backend/models/category_mobilenet_v3_small.pt
```

The build downloads the release manifest and runs
`scripts/verify_lightweight_release.py` before accepting the image. Canonical
repository metrics are `data/evaluation/cv_metrics.json` and
`data/evaluation/llm_metrics.json`.

Do not deploy a replacement checkpoint until held-out metrics, checksum
verification, CPU/RAM latency, and the production smoke workflow all pass.

## Gemini deployment

Do not commit or send the API key in chat. Add it directly to the backend environment:

```text
RETURNREVIEW_GEMINI_API_KEY=<secret>
RETURNREVIEW_LLM_ENABLED=true
```

Production Gemini is enabled. The fixed six-case evaluation and human-reviewed
metrics remain at `data/evaluation/runs/` and
`data/evaluation/llm_metrics.json`; rerun them before changing the production
model or prompt contract.

## Readiness checker

Run from the repository root (or `/app` inside the production image):

```bash
python scripts/check_release_readiness.py --root . --production-config
```

The checker validates the installed checkpoint hashes against the committed CV
metric provenance, the MobileNet/YOLO class contract, the reviewed Gemini
metric artifact, PostgreSQL configuration, schema `public`, and model version
`cv-lightweight-1`. It reports secret presence only and never prints values.
