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

### 1. Durable production database verification — complete

A dedicated Railway Postgres service and persistent volume now exist inside the isolated ReturnReview project, and the API database URL is configured through a Railway service reference.

Verified in production:
- API deployment succeeded on PostgreSQL
- startup reports `database_backend=postgresql`
- startup reports `durable_persistence=True`
- `/health` returns HTTP 200
- `/readiness` returns HTTP 200

Persistence proof completed with `PERSISTENCE-PROOF-01`: the case, both uploaded evidence images, and audit events remained available after redeploying only `returnreview-api`.

### 2. Gemini production activation and evaluation — complete

Gemini is enabled on the Railway backend with its API key stored only as a private backend variable. The production primary remains `gemini-3.8-flash`; a stable capacity fallback is configured separately.

A real six-case fixed evaluation run completed on 2026-09-24 using the explicitly recorded evaluation model `gemini-3.5-flash` after repeated transient 503 capacity failures from the primary model. The raw unreviewed run is preserved at `data/evaluation/runs/2026-09-24-gemini-3.5-flash-results.jsonl`.

Human review is complete. The immutable raw run remains at `data/evaluation/runs/2026-09-24-gemini-3.5-flash-results.jsonl`; the approved reviewed copy is `data/evaluation/runs/2026-09-24-gemini-3.5-flash-reviewed.jsonl`; and the canonical metric artifact is `data/evaluation/llm_metrics.json`.

Reviewed LLM metrics:
- action agreement: 83.3% (5/6)
- policy correctness: 100%
- required-tool coverage: 100%
- human correction rate: 33.3% (2/6)
- manually identified unsupported-claim rate: 16.7% (1/6)
- grounding-guard recall on the one human-identified unsupported claim: 0%
- average latency: 14.39 seconds

The weak guard-recall result is intentionally reported rather than hidden; it identifies a concrete improvement area before final submission.

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
