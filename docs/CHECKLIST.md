# Development Checklist

## Completed foundation
- [x] Repository initialized
- [x] Safe `develop` branch created
- [x] Next.js frontend and responsive evidence-focused UI
- [x] FastAPI backend + OpenAPI
- [x] Local SQLite persistence
- [x] Case creation/list/detail
- [x] Validated 2–4 image workflow
- [x] Structured policy lookup
- [x] Structured visual-evidence schema
- [x] YOLO segmentation adapter
- [x] OpenCLIP category/few-shot adapter
- [x] Prototype-bank builder
- [x] Gemini tool-calling adapter with deterministic fallback
- [x] Deterministic LLM grounding guard
- [x] Human approve/reject/request-more-evidence
- [x] Reviewer summary correction + notes
- [x] Audit timeline
- [x] Valid case-state transitions
- [x] Request IDs, latency logging and safe 500 handling
- [x] Real IoU/Dice evaluation script
- [x] Real few-shot F1 evaluation script
- [x] LLM/manual evaluation aggregation script
- [x] Refuse fake CV result when checkpoint is absent
- [x] GitHub CI: backend tests + frontend production build
- [x] API/model/security/demo documentation

## Blocked on real project data
- [ ] Collect 24–30 pilot images
- [ ] Inspect pilot quality/coverage
- [ ] Annotate pilot damage masks
- [ ] Train first segmentation checkpoint
- [ ] Validate generated overlays on unseen images
- [ ] Build reference prototype bank from training/reference images
- [ ] Calibrate OpenCLIP category threshold
- [ ] Calibrate few-shot similarity + ambiguity thresholds
- [ ] Decide whether pilot performance justifies expanding to 150–400 images
- [ ] Train/finalize best checkpoint
- [ ] Held-out CV metrics

## LLM evaluation
- [ ] Add Gemini key to a local/server environment (never commit it)
- [ ] Run real Gemini tool-calling cases
- [ ] Build fixed manually reviewed LLM evaluation set
- [ ] Measure groundedness/unsupported claims/policy correctness/agreement/correction rate/latency

## Persistence and deployment
- [ ] Read shared Project Hub Supabase README before any integration
- [ ] Inspect shared Supabase schema/storage read-only
- [ ] Add a collision-free ReturnReview namespace only if safe
- [ ] Deploy frontend
- [ ] Deploy backend/CV service after runtime/model size is measured
- [ ] Production CORS/storage/database verification
- [ ] Final end-to-end QA and demo rehearsal
