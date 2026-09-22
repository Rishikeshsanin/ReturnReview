# Final Demo Runbook

Target duration: **3–5 minutes**.

1. Open ReturnReview dashboard and show recent cases/statistics.
2. Create a new cardboard-box return case.
3. Upload 2–4 views and point out image-quality warnings.
4. Run computer vision inspection.
5. Show original photos and the damage overlay.
6. Explain category verification, segmentation confidence, few-shot defect label and affected visible-image area.
7. Generate the AI review.
8. Show exact policy evidence, evidence-image references and uncertainties.
9. Edit the AI summary or add reviewer notes to demonstrate human-in-the-loop correction.
10. Approve, reject or request more evidence.
11. Show the audit timeline.
12. Open Evaluation and show only real held-out metrics.

## Reliability plan
Before finals, preload several **real previously processed** cases:
- obvious tear
- crushed corner
- dent/crush
- normal/no visible damage
- uncertain/unknown defect

These are fallback demonstration records, not fake metrics. The live flow should still be demonstrated when available.

## Pre-demo checklist
- backend health is green
- CV checkpoint and prototype bank load successfully
- Gemini key is configured server-side
- no secrets appear in browser/network source
- demo images are local/offline-accessible
- final held-out metric artifacts are present
- one complete E2E rehearsal succeeds
