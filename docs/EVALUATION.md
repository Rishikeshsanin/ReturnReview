# Evaluation Protocol

ReturnReview must report only metrics produced from held-out samples.

## Computer vision

### Segmentation
Use a test split separated by physical box/capture session where practical.

Report:
- mean pixel IoU (all test images)
- mean Dice (all test images)
- mean IoU and Dice on damaged images only
- pixel precision / recall
- test sample count
- optional YOLO mask mAP as a secondary metric

Run:
```bash
python scripts/evaluate_masks.py --model backend/models/checkpoints/best.pt --root data/dataset
```

### Few-shot recognition
Prototype images must come from training/reference samples. Evaluation images must be held out.

Report:
- accuracy
- macro F1
- per-class precision / recall / F1
- confusion pairs/matrix

## LLM/review

Create a small manually reviewed JSONL evaluation set. Each row records:
- expected assistant action
- expected policy ID
- generated structured review
- manual unsupported-claim label
- whether a reviewer had to correct the draft
- measured LLM latency

Report:
- review/action agreement
- policy correctness
- manual unsupported-claim rate
- grounding-guard detection rate
- human correction rate
- average review latency

The operational approve/reject decision remains human-owned and is **not** treated as a target the LLM should learn to imitate.

## Reproducibility
Store model version, prompt version, evaluation-set version and generation timestamp with every published result.

## Fixed evaluation scaffold

The repository includes `data/evaluation/llm_eval_cases.jsonl` and `scripts/validate_llm_eval_set.py`. The initial rows define stable scenarios and expected actions only. They are **not model results**.

Before scoring, populate each row with a real `actual_review`, `manual_unsupported_claim`, `human_corrected`, and measured `latency_ms`, then run the validator with `--require-results`.
