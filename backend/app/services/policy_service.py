import json
from pathlib import Path
from app.models.response_models import PolicyReference

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "policies.json"


def _load() -> list[dict]:
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_policies() -> list[dict]:
    return _load()


def retrieve_return_policy(product_category: str, issue_type: str | None = None) -> PolicyReference | None:
    policies = _load()
    candidates = [p for p in policies if p["category"] == product_category]
    if issue_type:
        exact = [p for p in candidates if issue_type in p.get("applies_to", [])]
        if exact:
            candidates = exact
    if not candidates:
        return None
    p = candidates[0]
    return PolicyReference(policy_id=p["policy_id"], name=p["name"], section=p["section"], text=p["text"])
