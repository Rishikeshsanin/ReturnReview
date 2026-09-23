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

## Reproducible Gemini evaluation run

Once the Gemini key exists privately in the environment, run the fixed cases
without modifying their expected labels:

~~~bash
python scripts/run_gemini_eval.py \
  --input data/evaluation/llm_eval_cases.jsonl \
  --output artifacts/evaluation/llm_eval_results.jsonl
~~~

The runner records the real structured review, tool-call trace and measured
latency. It deliberately leaves `manual_unsupported_claim` and
`human_corrected` unset.

After a human evaluator fills those two labels in the **results copy**:

~~~bash
python scripts/validate_llm_eval_set.py \
  --input artifacts/evaluation/llm_eval_results.jsonl \
  --require-results

python scripts/evaluate_reviews.py \
  --input artifacts/evaluation/llm_eval_results.jsonl
~~~

The canonical fixed scenario file remains unchanged.
