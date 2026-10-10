from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_release_readiness.py"
SPEC = importlib.util.spec_from_file_location("check_release_readiness", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _write_ready_root(root: Path) -> dict[str, str]:
    segmentation = b"test-yolo-checkpoint"
    category = b"test-mobilenet-checkpoint"
    segmentation_path = root / "backend/models/checkpoints/best.pt"
    category_path = root / "backend/models/category_mobilenet_v3_small.pt"
    segmentation_path.parent.mkdir(parents=True)
    category_path.parent.mkdir(parents=True, exist_ok=True)
    segmentation_path.write_bytes(segmentation)
    category_path.write_bytes(category)

    evaluation = root / "data/evaluation"
    evaluation.mkdir(parents=True)
    (evaluation / "cv_metrics.json").write_text(
        json.dumps(
            {
                "status": "evaluated_public_pilot",
                "segmentation": {"per_class": {"tear": {}, "squeeze": {}, "leakage": {}}},
                "product_verification": {"model": "mobilenet_v3_small"},
                "provenance": {
                    "release_tag": "cv-lightweight-1",
                    "segmentation_checkpoint_sha256": _sha256(segmentation),
                    "category_checkpoint_sha256": _sha256(category),
                },
            }
        ),
        encoding="utf-8",
    )
    (evaluation / "llm_metrics.json").write_text(
        json.dumps(
            {
                "llm_review": {"evaluation_cases": 6},
                "provenance": {
                    "model": "gemini-3.5-flash",
                    "human_review_completed_at_utc": "2026-09-24T06:50:00Z",
                },
            }
        ),
        encoding="utf-8",
    )
    (evaluation / "llm_eval_cases.jsonl").write_text("{}\n", encoding="utf-8")
    return {
        "RETURNREVIEW_DATABASE_URL": "postgresql+psycopg://db/returnreview",
        "RETURNREVIEW_DATABASE_SCHEMA": "public",
        "RETURNREVIEW_GEMINI_API_KEY": "not-a-real-secret",
        "RETURNREVIEW_LLM_ENABLED": "true",
        "RETURNREVIEW_CV_MODEL_VERSION": "cv-lightweight-1",
    }


def test_current_runtime_contract_is_ready(tmp_path: Path) -> None:
    environ = _write_ready_root(tmp_path)
    payload = MODULE.build_readiness(tmp_path, True, environ)

    assert payload["status"] == "ready"
    assert payload["blockers"] == []
    assert payload["runtime_contract"]["database_schema"] == "public"
    assert payload["checks"]["cv_metrics"]["path"].endswith("data/evaluation/cv_metrics.json")
    assert payload["checks"]["llm_metrics"]["contract_valid"] is True


def test_stale_schema_and_tampered_checkpoint_are_blocked(tmp_path: Path) -> None:
    environ = _write_ready_root(tmp_path)
    environ["RETURNREVIEW_DATABASE_SCHEMA"] = "return_review"
    (tmp_path / "backend/models/checkpoints/best.pt").write_bytes(b"tampered")

    payload = MODULE.build_readiness(tmp_path, True, environ)

    assert payload["status"] == "blocked"
    assert "public_schema_not_configured" in payload["blockers"]
    assert "segmentation_checkpoint_checksum_mismatch" in payload["blockers"]


def test_runtime_relative_model_paths_resolve_from_backend(tmp_path: Path) -> None:
    environ = _write_ready_root(tmp_path)
    environ["RETURNREVIEW_CV_MODEL_PATH"] = "./models/checkpoints/best.pt"
    environ["RETURNREVIEW_CATEGORY_MODEL_PATH"] = "./models/category_mobilenet_v3_small.pt"

    payload = MODULE.build_readiness(tmp_path, True, environ)

    assert payload["status"] == "ready"
    assert payload["checks"]["segmentation_checkpoint"]["path"].endswith(
        "backend/models/checkpoints/best.pt"
    )
