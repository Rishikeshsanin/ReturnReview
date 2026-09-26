# Development Checklist

## Completed foundation
- [x] Repository initialized and protected by branch/PR workflow
- [x] Next.js frontend and responsive evidence-focused UI
- [x] FastAPI backend + OpenAPI
- [x] Local SQLite/file-storage implementation
- [x] Case creation/list/detail/history
- [x] Validated 2–4 image workflow
- [x] Structured policy lookup
- [x] Structured visual-evidence schema
- [x] YOLO segmentation adapter
- [x] OpenCLIP category/few-shot adapter
- [x] Prototype-bank builder
- [x] Conservative multi-view defect aggregation
- [x] Gemini tool-calling adapter with deterministic fallback
- [x] Deterministic LLM grounding guard
- [x] Human approve/reject/request-more-evidence
- [x] Reviewer summary correction + notes
- [x] Audit timeline
- [x] Valid case-state transitions
- [x] Request IDs, latency logging and safe 500 handling
- [x] Pixel IoU/Dice/precision/recall evaluation script
- [x] YOLO segmentation mAP evaluation script
- [x] Few-shot accuracy/macro-F1/per-class evaluation script
- [x] Product-verification threshold calibration + accuracy/FAR/FRR evaluation
- [x] LLM/manual evaluation aggregation script
- [x] Refuse fake CV result when checkpoint is absent
- [x] GitHub CI: backend tests + frontend build + both container smoke tests
- [x] Live production E2E smoke passes health/readiness/metrics, held-out CV inspection, Gemini review, persisted case reload, and audit verification
- [x] Immediate `/inspect` response returns newly persisted CV evidence after the SQLAlchemy refresh fix
- [x] Production smoke QA IDs are rerun-safe and optional Gemini transport timeouts no longer erase a valid CV/persistence smoke result
- [x] API/model/security/evaluation/demo/deployment documentation
- [x] Project Hub rules inspected read-only
- [x] Required Supabase Hub repo safety-contract files added
- [x] Backend deployed and healthchecked on Railway
- [x] Frontend deployed and healthchecked on Railway
- [x] Production CORS includes exact hosted frontend origin
- [x] Supabase Hub safety re-check completed before writes
- [x] ReturnReview registered as Supabase Project Hub App 13
- [x] Private `return_review` schema + seven tables provisioned
- [x] Dedicated least-privilege `return_review_backend` role provisioned
- [x] RLS policies + Hub resource registry verified
- [x] DB-backed image/overlay persistence implemented in application code
- [x] Production readiness endpoint implemented
- [x] Dedicated Railway Postgres + persistent volume provisioned in the isolated ReturnReview project
- [x] API database URL configured through a Railway service reference

## Dataset readiness
- [x] Controlled 28-image pilot capture/annotation plan + manifest validator
- [x] Real-data audit script
- [x] Leakage-safe physical/session split script
- [x] Public source provenance list with verified task/license metadata
- [x] Strict YOLO segmentation export validator
- [x] Reproducible licensed public-data CV pilot training workflow
- [x] Semantic OpenCLIP prototype + threshold calibration/evaluation tooling

## Blocked on real project data
- [ ] Collect 24–30 pilot images
- [ ] Inspect pilot quality/coverage
- [ ] Annotate pilot damage masks
- [x] Train public-pilot segmentation checkpoints
- [ ] Validate generated overlays on project-controlled unseen images
- [x] Replace memory-heavy production OpenCLIP path with lightweight MobileNetV3 verification
- [x] Train/finalize lightweight public-pilot candidate
- [x] Run held-out public-pilot CV metrics
- [x] Package checksum-verified CV artifacts after runtime measurement
- [x] Pass recorded 1 GB Railway runtime-capacity gate
- [ ] Repeat/validate on project-controlled capture

## LLM evaluation
- [x] Fixed LLM evaluation scenario set + schema validator
- [x] Reproducible real-Gemini evaluation runner
- [x] Manual-review gating before final metric aggregation
- [x] Required-tool coverage + reproducibility metadata
- [x] Truthful release-readiness checker
- [x] Add Gemini key to Railway backend environment (never commit or paste it into chat)
- [x] Enable `RETURNREVIEW_LLM_ENABLED=true`
- [x] Run fixed real Gemini tool-calling cases
- [x] Manually review every generated evaluation row
- [x] Generate groundedness/unsupported-claim/policy/agreement/correction/tool/latency metrics
- [x] Publish reviewed LLM metrics through the Evaluation dashboard

## Persistence
- [x] Choose final production persistence: dedicated Railway Postgres
- [x] Provision Postgres only inside the isolated ReturnReview project
- [x] Provision dedicated persistent database volume
- [x] Register database + volume in Railway Project Hub governance
- [x] Configure `RETURNREVIEW_DATABASE_URL` with a Railway service reference
- [x] Configure `RETURNREVIEW_DATABASE_SCHEMA=public`
- [x] Verify API reports PostgreSQL + durable persistence
- [x] Verify case + image persistence across an API redeploy

## Final submission
- [ ] Full real-data E2E QA
- [ ] Preload real fallback demo cases
- [x] Final evaluation dashboard code supports both LLM and held-out CV metric artifacts
- [ ] Final screenshots
- [ ] Final report/presentation/demo video
- [ ] Viva revision
