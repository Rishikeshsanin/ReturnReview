# Fixed LLM Evaluation Protocol

This evaluation isolates the **LLM/tool/grounding layer** from CV model quality.

It uses fixed structured evidence fixtures from:

`data/evaluation/llm_fixed_cases.json`

These fixtures are **not** claims about real CV performance. They exist so the Gemini agent can be tested repeatably against known structured inputs while CV training is still pending.

## Run

From the repository root with backend dependencies installed:

```bash
export RETURNREVIEW_GEMINI_API_KEY="set securely outside Git"
export RETURNREVIEW_GEMINI_MODEL="gemini-3.8-flash"

python scripts/run_llm_evaluation_cases.py
```

Output:

`artifacts/evaluation/llm_review_rows.jsonl`

Each generated row is deliberately marked:

```json
"manual_reviewed": false
```

## Human verification

For each row, inspect:
- the fixed evidence fixture,
- expected action,
- expected policy ID,
- actual Gemini draft,
- grounding-guard flag,
- tool-call log.

Then fill:

```json
"manual_reviewed": true,
"manual_unsupported_claim": false,
"human_corrected": false
```

Use the real judgment for the two boolean fields.

## Final metrics

Only after **every** row is manually reviewed:

```bash
python scripts/evaluate_reviews.py \
  --input artifacts/evaluation/llm_review_rows.jsonl
```

The evaluator refuses incomplete/unreviewed rows.

Reported metrics:
- action agreement,
- policy correctness,
- manually judged unsupported-claim rate,
- grounding-guard recall on unsupported claims,
- human correction rate,
- required-tool coverage,
- average latency.

This protocol prevents automated outputs from being presented as manually verified final metrics.
