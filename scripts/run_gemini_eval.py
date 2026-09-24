"""Run the fixed ReturnReview LLM evaluation scenarios through real Gemini.

This command requires RETURNREVIEW_GEMINI_API_KEY in the process environment.
It never prints the key and never mutates the fixed expectation file.

The output contains actual model reviews + measured latency, but manual labels
remain unset until a human evaluator reviews each result. Therefore published
metrics still require validate_llm_eval_set.py --require-results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter, sleep

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.models.response_models import DefectEvidence, ReviewOutput, VisualEvidence
from app.services.llm_service import SYSTEM_PROMPT
from app.services.policy_service import retrieve_return_policy
from app.services.review_guard import validate_review


def load_rows(path: Path) -> list[dict]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise SystemExit("Fixed evaluation set is empty")
    return rows


def build_evidence(row: dict) -> tuple[VisualEvidence, str]:
    scenario = row["scenario"]
    findings: list[DefectEvidence] = []
    for idx, item in enumerate(scenario.get("findings", []), start=1):
        image_id = str(item.get("evidence_image_id") or f"eval-image-{idx}")
        findings.append(
            DefectEvidence(
                finding_id=f"{row['case_id']}-finding-{idx}",
                image_id=image_id,
                defect_type=str(item["defect_type"]),
                confidence=float(item["confidence"]),
                bbox=None,
                affected_area_percent=None,
            )
        )

    verified = bool(scenario.get("category_verified"))
    evidence = VisualEvidence(
        case_id=row["case_id"],
        product_category="cardboard_box",
        category_verified=verified,
        verification_score=0.9 if verified else 0.2,
        findings=findings,
        uncertainties=(
            ["Defect subtype remains uncertain."]
            if any(item.defect_type == "unknown" for item in findings)
            else []
        ),
    )
    return evidence, str(scenario.get("customer_reason") or "")


def _is_transient_gemini_error(exc: Exception) -> bool:
    code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if code in {429, 500, 502, 503, 504}:
        return True
    message = str(exc)
    return any(token in message for token in ("429", "500", "502", "503", "504"))


def _generate_with_retry(client, *, model: str, contents: str, config):
    delays = (0, 2, 5, 10, 20)
    last_error: Exception | None = None
    for attempt, delay in enumerate(delays, start=1):
        if delay:
            sleep(delay)
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            last_error = exc
            if not _is_transient_gemini_error(exc) or attempt == len(delays):
                raise
    raise RuntimeError("Gemini retry loop ended unexpectedly") from last_error


def run_case(client, model: str, row: dict) -> tuple[ReviewOutput, float, list[str]]:
    from google.genai import types

    evidence, customer_reason = build_evidence(row)
    issue = evidence.findings[0].defect_type if evidence.findings else None
    policy = retrieve_return_policy(evidence.product_category, issue)
    tool_log: list[str] = []

    def get_case_context() -> dict:
        """Return trusted metadata for this fixed evaluation case."""
        tool_log.append("get_case_context")
        return {
            "case_id": row["case_id"],
            "product_name": "Cardboard shipping box",
            "product_category": evidence.product_category,
            "customer_reason": customer_reason,
            "evaluation_case": True,
        }

    def get_visual_evidence() -> dict:
        """Return the fixed structured CV evidence for this evaluation case."""
        tool_log.append("get_visual_evidence")
        return evidence.model_dump()

    def get_return_policy() -> dict:
        """Return the applicable structured policy for this evaluation case."""
        tool_log.append("get_return_policy")
        return policy.model_dump() if policy else {"policy_found": False}

    started = perf_counter()
    response = _generate_with_retry(
        client,
        model=model,
        contents=(
            "Prepare the evidence-based draft review for this fixed evaluation case. "
            "Use the supplied tools. Do not rely on unstated facts."
        ),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[get_case_context, get_visual_evidence, get_return_policy],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                maximum_remote_calls=6
            ),
            response_mime_type="application/json",
            response_schema=ReviewOutput,
        ),
    )
    latency_ms = (perf_counter() - started) * 1000.0

    parsed = (
        response.parsed
        if response.parsed is not None
        else ReviewOutput.model_validate_json(response.text)
    )
    review = validate_review(ReviewOutput.model_validate(parsed), evidence, policy)
    return review, latency_ms, tool_log


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/evaluation/llm_eval_cases.jsonl",
        help="Fixed expectation/scenario JSONL",
    )
    parser.add_argument(
        "--output",
        default="artifacts/evaluation/llm_eval_results.jsonl",
        help="Measured output JSONL; fixed input is never modified",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("RETURNREVIEW_GEMINI_MODEL", "gemini-3.8-flash"),
    )
    args = parser.parse_args()

    api_key = os.getenv("RETURNREVIEW_GEMINI_API_KEY")
    if not api_key:
        raise SystemExit(
            "RETURNREVIEW_GEMINI_API_KEY is not set. "
            "Store it privately in the environment; never paste it into source."
        )

    from google import genai

    input_path = Path(args.input)
    rows = load_rows(input_path)
    evaluation_set_sha256 = hashlib.sha256(input_path.read_bytes()).hexdigest()
    system_prompt_sha256 = hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest()
    generated_at_utc = datetime.now(timezone.utc).isoformat()

    client = genai.Client(api_key=api_key)
    results: list[dict] = []

    for row in rows:
        review, latency_ms, tool_log = run_case(client, args.model, row)
        result = dict(row)
        result["actual_review"] = review.model_dump(mode="json")
        result["latency_ms"] = round(latency_ms, 3)
        result["tool_calls"] = tool_log
        result["model"] = args.model
        result["evaluation_set_sha256"] = evaluation_set_sha256
        result["system_prompt_sha256"] = system_prompt_sha256
        result["generated_at_utc"] = generated_at_utc
        # These MUST be filled by a human after inspecting the real model output.
        result["manual_reviewed"] = False
        result["manual_unsupported_claim"] = None
        result["human_corrected"] = None
        results.append(result)
        print(
            f"{row['case_id']}: action={review.recommended_action} "
            f"latency_ms={latency_ms:.1f} guard={review.unsupported_claims_detected}"
        )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in results) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out}")
    print(
        "Manual review is still required. Set manual_reviewed=true and fill "
        "manual_unsupported_claim + human_corrected for every row, then run "
        "validate_llm_eval_set.py --require-results."
    )


if __name__ == "__main__":
    main()
