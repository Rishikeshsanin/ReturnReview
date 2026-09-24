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

The fixed LLM evaluation isolates the Gemini/tool/grounding layer from CV model quality. The scenario file is synthetic structured evidence for repeatable LLM testing; it is **not** a claim about CV performance.

The canonical fixed set is:

`data/evaluation/llm_eval_cases.jsonl`

It covers:
- normal/no visible damage
- tear
- crushed corner
- dent or crush
- unknown defect
- failed category verification

Each row records an expected assistant action and expected policy ID. Real Gemini outputs are written to a separate results file.

Report only after human review:
- review/action agreement
- policy correctness
- manual unsupported-claim rate
- grounding-guard recall on unsupported claims
- human correction rate
- required-tool coverage
- average review latency

The operational approve/reject decision remains human-owned and is **not** treated as a target the LLM should learn to imitate.

## Reproducible Gemini evaluation run

Once the Gemini key exists privately in the environment, run:

~~~bash
python scripts/run_gemini_eval.py \
  --input data/evaluation/llm_eval_cases.jsonl \
  --output artifacts/evaluation/llm_eval_results.jsonl
~~~

The runner records:
- the real structured Gemini review
- measured latency
- tool-call trace
- model name
- evaluation-set SHA-256
- system-prompt SHA-256
- generation timestamp

Every generated row starts with:

~~~json
"manual_reviewed": false,
"manual_unsupported_claim": null,
"human_corrected": null
~~~

This is intentional. Automated output must never be represented as manually verified.

## Human verification gate

For every generated row, a human evaluator must inspect the fixed scenario, expected action/policy, actual Gemini draft, grounding-guard result, and tool-call trace.

Then set:
- `manual_reviewed=true`
- `manual_unsupported_claim` to the human judgment
- `human_corrected` to the human judgment

Do not alter the canonical fixed scenario file.

Validate the reviewed results:

~~~bash
python scripts/validate_llm_eval_set.py \
  --input artifacts/evaluation/llm_eval_results.jsonl \
  --require-results
~~~

Only after that succeeds, aggregate final metrics:

~~~bash
python scripts/evaluate_reviews.py \
  --input artifacts/evaluation/llm_eval_results.jsonl
~~~

The evaluator independently refuses incomplete or unreviewed rows and also reports whether all three required read-only tools were used.

## Reproducibility

Every published LLM result must remain traceable to one model, one fixed evaluation-set checksum, one system-prompt checksum and one generation run. Never mix incompatible runs into one metric file.


## Railway one-time evaluation runner

The production API image includes the evaluation scripts, but they do **not** run during normal startup.

For a controlled Railway evaluation:
1. keep the Gemini key server-side on `returnreview-api`
2. set `RETURNREVIEW_RUN_LLM_EVAL_ON_START=true`
3. redeploy only `returnreview-api`
4. wait for the background job to write `/app/artifacts/evaluation/llm_eval_results.jsonl`
5. retrieve the non-secret result artifact for manual review
6. immediately restore `RETURNREVIEW_RUN_LLM_EVAL_ON_START=false` and redeploy

The runner never prints the API key. The generated rows remain `manual_reviewed=false` until a human has inspected them.
