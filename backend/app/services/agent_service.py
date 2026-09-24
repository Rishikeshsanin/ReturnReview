from __future__ import annotations
from time import perf_counter, sleep
from sqlalchemy.orm import Session
from app.models.response_models import ReviewOutput
from app.models.database_models import ReturnCase
from app.services.evidence_service import build_visual_evidence
from app.services.policy_service import retrieve_return_policy
from app.services.llm_service import deterministic_review, SYSTEM_PROMPT
from app.services.review_guard import validate_review
from app.utils.config import get_settings

settings = get_settings()


def _is_hard_quota_gemini_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "generaterequestsperdayperprojectpermodel",
            "free_tier_requests",
            "exceeded your current quota",
            "check your plan and billing details",
        )
    )


def _is_transient_gemini_error(exc: Exception) -> bool:
    code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if code == 429 and _is_hard_quota_gemini_error(exc):
        return False
    if code in {429, 500, 502, 503, 504}:
        return True
    message = str(exc)
    if _is_hard_quota_gemini_error(exc):
        return False
    return any(token in message for token in ("429", "500", "502", "503", "504"))


def _is_capacity_gemini_error(exc: Exception) -> bool:
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


def _generate_with_capacity_fallback(
    client,
    *,
    primary_model: str,
    fallback_model: str | None,
    contents: str,
    config,
):
    try:
        response = _generate_with_retry(
            client,
            model=primary_model,
            contents=contents,
            config=config,
        )
        return response, primary_model
    except Exception as exc:
        if (
            not fallback_model
            or fallback_model == primary_model
            or not _is_capacity_gemini_error(exc)
        ):
            raise
        response = _generate_with_retry(
            client,
            model=fallback_model,
            contents=contents,
            config=config,
        )
        return response, fallback_model


def run_review_agent(db: Session, case: ReturnCase) -> tuple[ReviewOutput, dict]:
    """Bounded read-only Gemini tool workflow followed by a deterministic grounding guard."""
    evidence = build_visual_evidence(db, case)
    issue = evidence.findings[0].defect_type if evidence.findings else None
    policy = retrieve_return_policy(case.product_category, issue)

    if not settings.llm_enabled or not settings.gemini_api_key:
        review = deterministic_review(evidence, policy, case.customer_reason)
        return validate_review(review, evidence, policy), {
            "provider": "deterministic",
            "model": "fallback-v1",
            "latency_ms": 0.0,
            "tool_calls": [],
            "grounding_guard": "passed",
        }

    from google import genai
    from google.genai import types

    tool_log: list[str] = []

    def get_case_context() -> dict:
        """Return trusted case metadata for the current return case."""
        tool_log.append("get_case_context")
        return {
            "case_id": case.id,
            "external_case_id": case.external_case_id,
            "product_name": case.product_name,
            "product_category": case.product_category,
            "customer_reason": case.customer_reason,
            "status": case.status,
        }

    def get_visual_evidence() -> dict:
        """Return structured computer-vision evidence for the current case."""
        tool_log.append("get_visual_evidence")
        return evidence.model_dump()

    def get_return_policy() -> dict:
        """Return the applicable structured return policy for the current case."""
        tool_log.append("get_return_policy")
        return policy.model_dump() if policy else {"policy_found": False}

    client = genai.Client(api_key=settings.gemini_api_key)
    started = perf_counter()
    try:
        response, model_used = _generate_with_capacity_fallback(
            client,
            primary_model=settings.gemini_model,
            fallback_model=settings.gemini_fallback_model,
            contents=(
                "Prepare the evidence-based draft review for this case. Use the supplied tools to obtain "
                "case metadata, visual evidence, and policy. Do not rely on unstated facts."
            ),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[get_case_context, get_visual_evidence, get_return_policy],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=6),
                response_mime_type="application/json",
                response_schema=ReviewOutput,
            ),
        )
        parsed = response.parsed if response.parsed is not None else ReviewOutput.model_validate_json(response.text)
        review = validate_review(ReviewOutput.model_validate(parsed), evidence, policy)
        return review, {
            "provider": "gemini",
            "model": model_used,
            "latency_ms": (perf_counter() - started) * 1000,
            "tool_calls": tool_log,
            "grounding_guard": "flagged" if review.unsupported_claims_detected else "passed",
        }
    except Exception:
        fallback = validate_review(deterministic_review(evidence, policy, case.customer_reason), evidence, policy)
        return fallback, {
            "provider": "deterministic",
            "model": "fallback-after-agent-error",
            "latency_ms": (perf_counter() - started) * 1000,
            "tool_calls": tool_log,
            "grounding_guard": "passed",
        }
