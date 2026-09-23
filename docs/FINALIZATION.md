# ReturnReview Finalization Status

This document separates **engineering completeness** from **evidence/model readiness**. A missing real artifact is never replaced by a fake model, metric, screenshot, or review.

## Engineering state

Completed:
- responsive Next.js reviewer UI
- FastAPI API and case workflow
- validated multi-image ingestion
- structured policy retrieval
- YOLO segmentation/OpenCLIP inference adapters
- conservative evidence aggregation
- Gemini bounded tool workflow + deterministic fallback
- deterministic grounding guard
- human final decision + edits + audit trail
- local SQLite recovery path
- dedicated Railway Postgres + persistent volume
- database-backed evidence bytes in application code
- deployment/readiness endpoints
- real CV/LLM evaluation scripts
- dataset provenance and leakage-safe validation tools
- Railway frontend + API deployment
- GitHub CI for backend/frontend/container/governance checks

## Fixed LLM evaluation set

`data/evaluation/llm_eval_cases.jsonl` defines stable scenarios covering:
- normal/no visible damage
- tear
- crushed corner
- dent or crush
- unknown defect
- failed category verification

The file contains **expected scenarios only**. It intentionally does not contain fabricated model outputs or metrics.

Validate it:

~~~bash
python scripts/validate_llm_eval_set.py
~~~

After a real Gemini run, each generated result remains explicitly unreviewed until a human sets `manual_reviewed=true` and supplies the two manual labels.

After real Gemini runs and manual review labels are added:

~~~bash
python scripts/validate_llm_eval_set.py \
  --input artifacts/evaluation/llm_eval_results.jsonl \
  --require-results

python scripts/evaluate_reviews.py \
  --input artifacts/evaluation/llm_eval_results.jsonl
~~~

The final evaluator refuses incomplete or unreviewed rows.

## Release-readiness check

Run:

~~~bash
python scripts/check_release_readiness.py
~~~

For a production environment, use:

~~~bash
python scripts/check_release_readiness.py --production-config
~~~

The checker reports only file/configuration presence. It never prints secret values.

## External blockers that cannot be fabricated

### 1. Durable production database verification

A dedicated Railway Postgres service and persistent volume now exist inside the isolated ReturnReview project, and the API database URL is configured through a Railway service reference.

Verified in production:
- API deployment succeeded on PostgreSQL
- startup reports `database_backend=postgresql`
- startup reports `durable_persistence=True`
- `/health` returns HTTP 200
- `/readiness` returns HTTP 200

The remaining persistence proof is a real case + 2–4 evidence images surviving an API redeploy.

### 2. Gemini production activation

The backend supports Gemini, but `RETURNREVIEW_GEMINI_API_KEY` must be stored server-side in Railway and `RETURNREVIEW_LLM_ENABLED=true`.

Never commit or paste the API key into chat/source.

### 3. Real CV artifacts

The production CV path requires:
- a real polygon/mask-labelled damage dataset
- trained segmentation checkpoint
- OpenCLIP prototype bank
- validation-calibrated thresholds
- held-out metrics

Detection rectangles/boxes are **not** accepted as segmentation-mask ground truth.

## Definition of fully final

ReturnReview is fully final for submission only when all are true:
1. production database is durable and survives API redeploy
2. Gemini tool-calling is tested with the fixed evaluation set
3. CV checkpoint + prototype bank are real and load in the API
4. held-out CV metrics exist
5. manually reviewed LLM metrics exist
6. real fallback demo cases are preloaded
7. one full E2E rehearsal succeeds
8. screenshots/report/presentation/video use those real outputs

Until then, the application remains deliberately honest about readiness.
