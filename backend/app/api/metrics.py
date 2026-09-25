import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("")
def metrics():
    root = Path(__file__).resolve().parents[3]
    llm_path = root / "data" / "evaluation" / "llm_metrics.json"
    cv_path = root / "data" / "evaluation" / "cv_metrics.json"

    llm = json.loads(llm_path.read_text(encoding="utf-8")) if llm_path.exists() else None
    cv = json.loads(cv_path.read_text(encoding="utf-8")) if cv_path.exists() else None

    if llm is None and cv is None:
        return {
            "status": "not_evaluated",
            "message": "No reviewed evaluation metrics are available yet.",
            "computer_vision": {
                "status": "not_evaluated",
                "message": "Real trained CV artifacts and held-out metrics are still required.",
            },
        }

    payload = {
        "status": "evaluated" if llm is not None and cv is not None else "partially_evaluated",
        "scope": (
            "llm_review_complete_cv_public_pilot"
            if llm is not None and cv is not None
            else "partial_evaluation"
        ),
    }
    if llm is not None:
        payload.update(llm)
    if cv is not None:
        payload["computer_vision"] = cv
    else:
        payload["computer_vision"] = {
            "status": "not_evaluated",
            "message": "Real trained CV artifacts and held-out metrics are still required.",
        }
    return payload
