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

The weak guard-recall result is intentionally reported rather than hidden. The reviewed failure led to a regression fix that now rejects confidence-complement arithmetic, and category-verification failure is deterministically normalized to `insufficient_evidence`. The historical metric remains unchanged; improvement must be demonstrated by a future real rerun rather than by rewriting the baseline.

### 3. Lightweight CV public-pilot candidate — complete

A checksum-verified public-data release candidate now exists as `cv-lightweight-1`.

Artifacts:
- multiclass YOLO11n-seg checkpoint
- MobileNetV3-Small cardboard-box verifier
- release manifest with SHA-256 checksums
- held-out CV metric artifact
- runtime capacity benchmark

Held-out public-pilot results:
- category verification: 100% accuracy and F1 on 32 held-out images (16 positives / 16 disjoint generic negatives)
- segmentation mean IoU: 14.1%
- segmentation mean Dice: 20.0%
- mask mAP@50: 12.9%
- measured combined CPU inference: ~185.6 ms/image on GitHub-hosted Ubuntu CPU
- measured CV peak RSS: ~802.7 MB
- estimated existing-API + CV footprint: ~894.7 MB; 1 GB gate passes with the recorded 64 MB reserve

The segmentation numbers are modest and are not hidden. This is a public-data engineering pilot, not a claim of production-grade visual accuracy.

The runtime no longer requires OpenCLIP in production. Category verification uses MobileNetV3-Small; YOLO predicts source classes `tear`, `squeeze`, and `leakage`. Runtime maps `tear` directly, treats `leakage` as `unknown`, and separates `squeeze` into `dent_or_crush` versus `crushed_corner` using an explicit corner-geometry heuristic because the public source does not provide a direct crushed-corner label.

The separate project-controlled cardboard-box capture remains the final academic-strength evidence task. Detection rectangles/boxes are **not** accepted as segmentation-mask ground truth.

## 4. Live production E2E checkpoint — complete

The backend response-refresh fix was deployed to the existing Railway `returnreview-api` service from application commit `fa15d51cabafd1f2afc02517e9562fc6d383df75` and reached `SUCCESS`.

The live production smoke subsequently passed on GitHub Actions run `36228065797`. It verified:
- `/health` HTTP 200 with PostgreSQL, durable persistence, LLM enabled, and `cv-lightweight-1`
- `/readiness` HTTP 200 with `cv_ready=true`, `llm_ready=true`, no blockers, and durable PostgreSQL
- `/api/metrics` HTTP 200 with the reviewed six-case LLM baseline and public-pilot CV artifact
- the deployed Evaluation page
- two held-out licensed public-pilot cardboard-box images uploaded into a new QA case
- immediate `POST /inspect` returned `CV_COMPLETE`, `category_verified=true`, a non-null verification score, two images, and the persisted `CV_COMPLETED` event without requiring a fresh GET
- live Gemini review completed and the subsequent case GET returned `READY_FOR_REVIEW` with the saved AI review and audit history

The successful QA case was `E2E-CV-36228065797-A1`. This closes the stale immediate-inspection-response production checkpoint.

The smoke harness was also hardened so rerunning a workflow cannot collide with a previously persisted QA case, and third-party Gemini transport timeouts are treated as non-blocking only for the optional AI-review exercise; unexpected HTTP contract failures still fail the smoke.

GitHub `main` may be ahead of the deployed API application SHA because the follow-up commits only changed `.github/**` workflow files. Those paths are outside the API service's Railway watch patterns, so no additional backend redeploy is required for the smoke-harness-only changes.

This is a **production engineering smoke using held-out licensed public-pilot images**. It does not replace the still-pending project-controlled real-box capture, polygon annotation, controlled CV evaluation, or final real-data submission rehearsal.

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
