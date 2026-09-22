# Development Checklist

## Completed foundation
- [x] Repository initialized and protected by branch/PR workflow
- [x] Next.js frontend and responsive evidence-focused UI
- [x] FastAPI backend + OpenAPI
- [x] Persistent SQLite + file storage on ReturnReview-only Railway volume
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
- [x] API/model/security/evaluation/demo/deployment documentation
- [x] Project Hub rules inspected read-only
- [x] Required Supabase Hub repo safety-contract files added
- [x] Backend deployed and healthchecked on Railway
- [x] Frontend deployed and healthchecked on Railway
- [x] Production CORS includes exact hosted frontend origin
- [x] Shared Supabase remains unmodified

## Blocked on real project data
- [ ] Collect 24–30 pilot images
- [ ] Inspect pilot quality/coverage
- [ ] Annotate pilot damage masks
- [ ] Train first segmentation checkpoint
- [ ] Validate generated overlays on unseen images
- [ ] Build reference prototype bank from training/reference images
- [ ] Calibrate OpenCLIP category threshold on validation data
- [ ] Calibrate few-shot similarity + ambiguity thresholds
- [ ] Decide whether pilot performance justifies expanding to 150–400 images
- [ ] Train/finalize best checkpoint
- [ ] Run held-out CV metrics
- [ ] Package/deploy validated CV artifacts after runtime measurement

## LLM evaluation
- [ ] Add Gemini key to local/Railway environment (never commit or paste it into chat)
- [ ] Enable `RETURNREVIEW_LLM_ENABLED=true`
- [ ] Run real Gemini tool-calling cases
- [ ] Build fixed manually reviewed LLM evaluation set
- [ ] Measure groundedness/unsupported claims/policy correctness/agreement/correction rate/latency

## Final submission
- [ ] Full real-data E2E QA
- [ ] Preload real fallback demo cases
- [ ] Final evaluation dashboard populated from generated metric artifacts
- [ ] Final screenshots
- [ ] Final report/presentation/demo video
- [ ] Viva revision
