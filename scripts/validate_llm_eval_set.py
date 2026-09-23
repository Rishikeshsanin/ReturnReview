"""Validate ReturnReview's fixed LLM evaluation-set schema without inventing results."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_ACTIONS = {
    "manual_review",
    "request_more_evidence",
    "no_visible_damage_detected",
    "policy_mismatch",
    "insufficient_evidence",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/evaluation/llm_eval_cases.jsonl",
        help="Fixed evaluation-case JSONL.",
    )
    parser.add_argument(
        "--require-results",
        action="store_true",
        help="Also require real Gemini outputs plus completed human-review labels.",
    )
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        raise SystemExit(f"Missing evaluation set: {path}")

    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise SystemExit("Evaluation set is empty")

    seen: set[str] = set()
    provenance_fields = (
        "model",
        "evaluation_set_sha256",
        "system_prompt_sha256",
        "generated_at_utc",
    )

    for index, row in enumerate(rows, start=1):
        case_id = row.get("case_id")
        if not case_id or not isinstance(case_id, str):
            raise SystemExit(f"Row {index}: case_id is required")
        if case_id in seen:
            raise SystemExit(f"Duplicate case_id: {case_id}")
        seen.add(case_id)

        action = row.get("expected_action")
        if action not in ALLOWED_ACTIONS:
            raise SystemExit(f"{case_id}: invalid expected_action {action!r}")

        if not row.get("expected_policy_id"):
            raise SystemExit(f"{case_id}: expected_policy_id is required")

        scenario = row.get("scenario")
        if not isinstance(scenario, dict):
            raise SystemExit(f"{case_id}: scenario object is required")
        if "category_verified" not in scenario:
            raise SystemExit(f"{case_id}: scenario.category_verified is required")
        if not isinstance(scenario.get("findings", []), list):
            raise SystemExit(f"{case_id}: scenario.findings must be a list")

        if row.get("manual_review_required") is not True:
            raise SystemExit(f"{case_id}: manual_review_required must be true")

        if args.require_results:
            review = row.get("actual_review")
            if not isinstance(review, dict):
                raise SystemExit(f"{case_id}: actual_review missing")
            if row.get("manual_reviewed") is not True:
                raise SystemExit(f"{case_id}: manual_reviewed must be true")
            if not isinstance(row.get("manual_unsupported_claim"), bool):
                raise SystemExit(
                    f"{case_id}: manual_unsupported_claim must be a human-labelled boolean"
                )
            if not isinstance(row.get("human_corrected"), bool):
                raise SystemExit(
                    f"{case_id}: human_corrected must be a human-labelled boolean"
                )
            latency = row.get("latency_ms")
            if not isinstance(latency, (int, float)) or isinstance(latency, bool) or latency < 0:
                raise SystemExit(f"{case_id}: latency_ms must be a non-negative number")
            tool_calls = row.get("tool_calls")
            if not isinstance(tool_calls, list) or not all(
                isinstance(item, str) for item in tool_calls
            ):
                raise SystemExit(f"{case_id}: tool_calls must be a list of tool names")
            for field in provenance_fields:
                if not isinstance(row.get(field), str) or not row[field].strip():
                    raise SystemExit(f"{case_id}: {field} missing")

    print(f"Validated {len(rows)} fixed LLM evaluation cases from {path}")
    if not args.require_results:
        print(
            "Scoring fields are intentionally optional until real Gemini outputs "
            "are manually reviewed."
        )


if __name__ == "__main__":
    main()
