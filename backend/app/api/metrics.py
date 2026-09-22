import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("")
def metrics():
    path = Path(__file__).resolve().parents[3] / "artifacts" / "evaluation" / "metrics.json"
    if not path.exists():
        return {"status": "not_evaluated", "message": "Run the held-out evaluation pipeline before reporting metrics."}
    return {"status": "evaluated", **json.loads(path.read_text(encoding="utf-8"))}
