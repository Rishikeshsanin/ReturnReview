"""Run fixed ReturnReview LLM evaluation fixtures against Gemini.

This evaluates the LLM/tool/grounding layer independently of the CV model by
supplying fixed structured evidence fixtures. It does NOT produce CV metrics.

Output rows are deliberately marked manual_reviewed=false. The final metrics
aggregator refuses to score them until a human reviews each row and fills:
- manual_reviewed: true
- manual_unsupported_claim: true/false
- human_corrected: true/false

Usage:
  RETURNREVIEW_GEMINI_API_KEY=... python scripts/run_llm_evaluation_cases.py

Never commit the API key.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.models.response_models import VisualEvidence, PolicyReference, ReviewOutput
from app.services.llm_service import SYSTEM_PROMPT
from app.services.review_guard import validate_review

POLICY_PATH = ROOT / "data" / "policies.json"


def load_policy(policy_id: str) -> PolicyReference:
    policies = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    row = next((p for p in policies if p["policy_id"] == policy_id), None)
    if row is None:
        raise RuntimeError(f"Policy not found: {policy_id}")
    return PolicyReference(
        policy_id=row["policy_id"],
        name=row["name"],
        section=row["section"],
        text=row["text"],
    )


def run_case(client, types, model: str, fixture: dict) -> dict:
    evidence = VisualEvidence.model_validate(fixture["evidence"])
    policy = load_policy(fixture["expected_policy_id"])
    tool_log: list[str] = []

    def get_case_context() -> dict:
        """Return trusted case metadata for this fixed evaluation case."""
        tool_log.append("get_case_context")
        return {
            "case_id": fixture["case_id"],
            "external_case_id": fixture["external_case_id"],
            "product_name": fixture["product_name"],
            "product_category": fixture["product_category"],
            "customer_reason": fixture["customer_reason"],
            "status": "CV_COMPLETE",
        }

    def get_visual_evidence() -> dict:
        """Return fixed structured visual evidence for this evaluation case."""
        tool_log.append("get_visual_evidence")
        return evidence.model_dump()

    def get_return_policy() -> dict:
        """Return the fixed applicable structured return policy."""
        tool_log.append("get_return_policy")
        return policy.model_dump()

    started = perf_counter()
    response = client.models.generate_content(
        model=model,
        contents=(
            "Prepare the evidence-based draft review for this fixed evaluation case. "
            "Use the supplied tools for case metadata, visual evidence, and policy. "
            "Do not rely on unstated facts."
        ),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[get_case_context, get_visual_evidence, get_return_policy],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=6),
            response_mime_type="application/json",
            response_schema=ReviewOutput,
        ),
    )
    latency_ms = (perf_counter() - started) * 1000
    parsed = response.parsed if response.parsed is not None else ReviewOutput.model_validate_json(response.text)
    guarded = validate_review(ReviewOutput.model_validate(parsed), evidence, policy)

    return {
        "case_id": fixture["case_id"],
        "expected_action": fixture["expected_action"],
        "expected_policy_id": fixture["expected_policy_id"],
        "actual_review": guarded.model_dump(),
        "tool_calls": tool_log,
        "latency_ms": latency_ms,
        "manual_reviewed": False,
        "manual_unsupported_claim": None,
        "human_corrected": None,
        "notes": "Human reviewer must verify this row before final metrics are generated.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fixtures",
        default="data/evaluation/llm_fixed_cases.json",
    )
    parser.add_argument(
        "--output",
        default="artifacts/evaluation/llm_review_rows.jsonl",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("RETURNREVIEW_GEMINI_MODEL", "gemini-3.8-flash"),
    )
    args = parser.parse_args()

    api_key = os.environ.get("RETURNREVIEW_GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("RETURNREVIEW_GEMINI_API_KEY is required; do not commit or print it.")

    from google import genai
    from google.genai import types

    payload = json.loads((ROOT / args.fixtures).read_text(encoding="utf-8"))
    fixtures = payload["cases"]
    if not fixtures:
        raise SystemExit("No LLM evaluation fixtures found")

    client = genai.Client(api_key=api_key)
    rows: list[dict] = []
    for fixture in fixtures:
        rows.append(run_case(client, types, args.model, fixture))
        print(f"completed {fixture['case_id']}")

    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(rows)} unreviewed rows -> {out}")
    print("Next: manually review every row, set manual_reviewed=true, then run evaluate_reviews.py.")


if __name__ == "__main__":
    main()
