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


## Capacity fallback and evaluation model

Production keeps the configured Gemini primary model unchanged.

A separate fallback model may be configured and is used only after the primary model exhausts retries on transient capacity or server errors. Stored AI-review metadata records the model that actually produced the draft.

The fixed evaluation may use a separate explicit evaluation model. Every generated result row records the exact model used so evaluation provenance remains accurate.


## Recorded real run — 2026-09-24

A real fixed evaluation run completed in the production API environment using:

- evaluation model: `gemini-3.5-flash`
- cases: 6
- evaluation-set SHA-256: `6d09a2f35349191e3b93cdf16970b78b3a0ad3add9bcaabcbe1309fcb4e5fa1b`
- system-prompt SHA-256: `8e9fee71e99c6830af01e32aed079733c7003cd8dab301dc512d39f74466df64`
- raw results: `data/evaluation/runs/2026-09-24-gemini-3.5-flash-results.jsonl`

The evaluation model is explicitly recorded because the primary production model experienced repeated transient provider-capacity errors during the controlled run. These results must not be described as 3.8 results.

Human review was approved on 2026-09-24. The raw run remains unchanged; the reviewed copy is `data/evaluation/runs/2026-09-24-gemini-3.5-flash-reviewed.jsonl`, and the canonical metrics artifact is `data/evaluation/llm_metrics.json`.

Reviewed labels:
- normal: no unsupported claim; no correction
- tear: no unsupported claim; no correction
- crushed corner: no unsupported claim; no correction
- dent/crush: unsupported confidence interpretation flagged; correction required
- unknown: no unsupported claim; no correction
- category-verification failure: grounded draft, but action corrected to the fixed expected `insufficient_evidence`

Final reviewed LLM metrics:
- action agreement: 5/6 = 83.3%
- policy correctness: 6/6 = 100%
- required-tool coverage: 6/6 = 100%
- human correction rate: 2/6 = 33.3%
- manually identified unsupported-claim rate: 1/6 = 16.7%
- grounding-guard recall on unsupported claims: 0/1 = 0%
- mean latency: 14,386.87 ms (~14.39 s)

CI re-runs the strict reviewed-set validator and recomputes the metrics on every change. The published artifact must match the evaluator output before CI passes.


## Post-review hardening

The first human-reviewed run intentionally remains immutable as a baseline. It exposed two concrete issues in the evaluated code version:

1. the grounding guard did not inspect the model's uncertainty text for invalid confidence-complement arithmetic;
2. a category-verification failure could preserve the model's `request_more_evidence` action instead of the fixed `insufficient_evidence` contract.

The current code fixes both issues and includes regression tests. The published 2026-09-24 metrics are **not rewritten** after the fix; a future real evaluation run should be used to measure the improved guard/action behavior.
