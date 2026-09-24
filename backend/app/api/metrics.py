import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("")
def metrics():
    root = Path(__file__).resolve().parents[3]
    llm_path = root / "data" / "evaluation" / "llm_metrics.json"

    if not llm_path.exists():
        return {
            "status": "not_evaluated",
            "message": "No reviewed evaluation metrics are available yet.",
            "computer_vision": {
                "status": "not_evaluated",
                "message": "Real trained CV artifacts and held-out metrics are still required.",
            },
        }

    llm = json.loads(llm_path.read_text(encoding="utf-8"))
    return {
        "status": "partially_evaluated",
        "scope": "llm_review_complete_cv_pending",
        **llm,
        "computer_vision": {
            "status": "not_evaluated",
            "message": "Real trained checkpoint, prototype bank, calibration, and held-out CV metrics are still required.",
        },
    }
