"""Aggregate manually verified LLM evaluation cases without inventing metrics.

Final metrics are intentionally blocked unless every row contains:
- a real actual_review,
- manual_reviewed=true,
- human-labelled manual_unsupported_claim,
- human-labelled human_corrected,
- measured latency and tool-call trace,
- reproducibility metadata from the real Gemini run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

REQUIRED_TOOLS = {
    "get_case_context",
    "get_visual_evidence",
    "get_return_policy",
}


def require_single_value(rows: list[dict], field: str) -> str:
    values = {row[field] for row in rows}
    if len(values) != 1:
        raise SystemExit(
            f"Final metrics require one consistent {field}; found {sorted(values)}"
        )
    return next(iter(values))


def main() -> None:
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

    incomplete: list[str] = []
    for row in rows:
        case_id = row.get("case_id", "<unknown>")
        latency = row.get("latency_ms")
        tool_calls = row.get("tool_calls")
        if (
            not isinstance(row.get("actual_review"), dict)
            or row.get("manual_reviewed") is not True
            or not isinstance(row.get("manual_unsupported_claim"), bool)
            or not isinstance(row.get("human_corrected"), bool)
            or not isinstance(latency, (int, float))
            or isinstance(latency, bool)
            or latency < 0
            or not isinstance(tool_calls, list)
            or not all(isinstance(item, str) for item in tool_calls)
            or not all(
                isinstance(row.get(field), str) and row[field].strip()
                for field in (
                    "model",
                    "evaluation_set_sha256",
                    "system_prompt_sha256",
                    "generated_at_utc",
                )
            )
        ):
            incomplete.append(case_id)

    if incomplete:
        raise SystemExit(
            "Final LLM metrics require complete real outputs and human review. "
            "Incomplete cases: " + ", ".join(incomplete)
        )

    model = require_single_value(rows, "model")
    evaluation_set_sha256 = require_single_value(rows, "evaluation_set_sha256")
    system_prompt_sha256 = require_single_value(rows, "system_prompt_sha256")
    generated_at_utc = require_single_value(rows, "generated_at_utc")

    action_agreement: list[bool] = []
    policy_correct: list[bool] = []
    manual_unsupported: list[bool] = []
    guard_flags: list[bool] = []
    corrected: list[bool] = []
    latencies: list[float] = []
    tool_coverage: list[bool] = []

    for row in rows:
        review = row["actual_review"]
        action_agreement.append(
            review.get("recommended_action") == row.get("expected_action")
        )

        expected_policy = row.get("expected_policy_id")
        actual_policy = (review.get("policy_reference") or {}).get("policy_id")
        if expected_policy is not None:
            policy_correct.append(actual_policy == expected_policy)

        manual_flag = row["manual_unsupported_claim"]
        guard_flag = bool(review.get("unsupported_claims_detected", False))
        manual_unsupported.append(manual_flag)
        guard_flags.append(guard_flag)
        corrected.append(row["human_corrected"])
        latencies.append(float(row["latency_ms"]))

        calls = set(row["tool_calls"])
        tool_coverage.append(REQUIRED_TOOLS.issubset(calls))

    true_unsupported = sum(manual_unsupported)
    caught_unsupported = sum(
        manual and guard
        for manual, guard in zip(manual_unsupported, guard_flags)
    )

    payload = {
        "llm_review": {
            "evaluation_cases": len(rows),
            "review_action_agreement": sum(action_agreement) / len(action_agreement),
            "policy_correctness": (
                sum(policy_correct) / len(policy_correct)
                if policy_correct
                else None
            ),
            "manual_unsupported_claim_rate": (
                sum(manual_unsupported) / len(manual_unsupported)
            ),
            "grounding_guard_recall_on_unsupported": (
                caught_unsupported / true_unsupported
                if true_unsupported
                else None
            ),
            "human_correction_rate": sum(corrected) / len(corrected),
            "required_tool_coverage": sum(tool_coverage) / len(tool_coverage),
            "average_latency_ms": mean(latencies),
        },
        "provenance": {
            "statement": (
                "Aggregated only after every fixed Gemini evaluation row was "
                "manually reviewed."
            ),
            "model": model,
            "evaluation_set_sha256": evaluation_set_sha256,
            "system_prompt_sha256": system_prompt_sha256,
            "generated_at_utc": generated_at_utc,
        },
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
