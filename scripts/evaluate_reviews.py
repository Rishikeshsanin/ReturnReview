"""Aggregate manually verified LLM evaluation cases without inventing metrics.

JSONL row example (values below are schema examples, not results):
{
  "case_id": "case-1",
  "expected_action": "manual_review",
  "expected_policy_id": "RET-CBX-001",
  "actual_review": {
    "recommended_action": "manual_review",
    "policy_reference": {"policy_id": "RET-CBX-001"},
    "unsupported_claims_detected": false
  },
  "manual_unsupported_claim": false,
  "human_corrected": false,
  "latency_ms": 850.0
}
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from statistics import mean


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="artifacts/evaluation/llm_metrics.json")
    args = parser.parse_args()

    rows = [
        json.loads(line)
        for line in Path(args.input).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise SystemExit("Evaluation set is empty")

    action_agreement = []
    policy_correct = []
    manual_unsupported = []
    guard_flags = []
    corrected = []
    latencies = []

    for row in rows:
        review = row["actual_review"]
        action_agreement.append(review.get("recommended_action") == row.get("expected_action"))

        expected_policy = row.get("expected_policy_id")
        actual_policy = (review.get("policy_reference") or {}).get("policy_id")
        if expected_policy is not None:
            policy_correct.append(actual_policy == expected_policy)

        manual_flag = bool(row.get("manual_unsupported_claim", False))
        guard_flag = bool(review.get("unsupported_claims_detected", False))
        manual_unsupported.append(manual_flag)
        guard_flags.append(guard_flag)
        corrected.append(bool(row.get("human_corrected", False)))
        if row.get("latency_ms") is not None:
            latencies.append(float(row["latency_ms"]))

    true_unsupported = sum(manual_unsupported)
    caught_unsupported = sum(m and g for m, g in zip(manual_unsupported, guard_flags))

    payload = {
        "llm_review": {
            "evaluation_cases": len(rows),
            "review_action_agreement": sum(action_agreement) / len(action_agreement),
            "policy_correctness": (sum(policy_correct) / len(policy_correct)) if policy_correct else None,
            "manual_unsupported_claim_rate": sum(manual_unsupported) / len(manual_unsupported),
            "grounding_guard_recall_on_unsupported": (caught_unsupported / true_unsupported) if true_unsupported else None,
            "human_correction_rate": sum(corrected) / len(corrected),
            "average_latency_ms": mean(latencies) if latencies else None,
        },
        "provenance": "Aggregated from a manually reviewed fixed evaluation set.",
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
