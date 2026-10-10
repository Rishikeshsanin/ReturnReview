"""Truthful release-readiness checker for ReturnReview.

The checker mirrors the current production container layout and never replaces a
missing model or metric with a placeholder. Secret values are never emitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


EXPECTED_CV_MODEL_VERSION = "cv-lightweight-1"
EXPECTED_DATABASE_SCHEMA = "public"
EXPECTED_SEGMENTATION_CLASSES = {"tear", "squeeze", "leakage"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_state(path: Path, *, include_sha256: bool = False) -> dict[str, Any]:
    exists = path.is_file()
    state: dict[str, Any] = {
        "path": path.as_posix(),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else None,
    }
    if include_sha256:
        state["sha256"] = sha256(path) if exists else None
    return state


def runtime_path(root: Path, environ: Mapping[str, str], env_name: str, default: str) -> Path:
    configured = environ.get(env_name, "").strip()
    if not configured:
        return root / default
    path = Path(configured)
    if path.is_absolute():
        return path
    # The API container runs from /app/backend, so relative runtime paths are
    # resolved against that directory rather than the repository/runtime root.
    return root / "backend" / path


def load_json_contract(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.is_file():
        return None, []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, [f"invalid_json: {type(exc).__name__}"]
    if not isinstance(payload, dict):
        return None, ["root_must_be_object"]
    return payload, []


def build_readiness(root: Path, production_config: bool, environ: Mapping[str, str]) -> dict[str, Any]:
    root = root.resolve()
    required_paths = {
        "segmentation_checkpoint": runtime_path(
            root, environ, "RETURNREVIEW_CV_MODEL_PATH", "backend/models/checkpoints/best.pt"
        ),
        "category_checkpoint": runtime_path(
            root,
            environ,
            "RETURNREVIEW_CATEGORY_MODEL_PATH",
            "backend/models/category_mobilenet_v3_small.pt",
        ),
        "cv_metrics": root / "data/evaluation/cv_metrics.json",
        "llm_metrics": root / "data/evaluation/llm_metrics.json",
        "llm_eval_set": root / "data/evaluation/llm_eval_cases.jsonl",
    }
    checks = {
        name: file_state(path, include_sha256=name.endswith("checkpoint"))
        for name, path in required_paths.items()
    }
    blockers: list[str] = []
    for name, state in checks.items():
        if not state["exists"] or state["size_bytes"] == 0:
            blockers.append(f"missing_or_empty_{name}")

    cv_metrics, cv_errors = load_json_contract(required_paths["cv_metrics"])
    if cv_metrics is not None:
        provenance = cv_metrics.get("provenance", {})
        segmentation = cv_metrics.get("segmentation", {})
        verification = cv_metrics.get("product_verification", {})
        if cv_metrics.get("status") != "evaluated_public_pilot":
            cv_errors.append("status_must_be_evaluated_public_pilot")
        if provenance.get("release_tag") != EXPECTED_CV_MODEL_VERSION:
            cv_errors.append("release_tag_must_match_cv-lightweight-1")
        if verification.get("model") != "mobilenet_v3_small":
            cv_errors.append("category_model_must_be_mobilenet_v3_small")
        if set(segmentation.get("per_class", {})) != EXPECTED_SEGMENTATION_CLASSES:
            cv_errors.append("segmentation_classes_must_be_tear_squeeze_leakage")

        expected_hashes = {
            "segmentation_checkpoint": provenance.get("segmentation_checkpoint_sha256"),
            "category_checkpoint": provenance.get("category_checkpoint_sha256"),
        }
        for name, expected_hash in expected_hashes.items():
            actual_hash = checks[name].get("sha256")
            if not isinstance(expected_hash, str) or len(expected_hash) != 64:
                cv_errors.append(f"missing_{name}_sha256_provenance")
            elif actual_hash is not None and actual_hash != expected_hash:
                blockers.append(f"{name}_checksum_mismatch")
    if cv_errors:
        blockers.append("invalid_cv_metrics_contract")
    checks["cv_metrics"]["contract_valid"] = bool(cv_metrics is not None and not cv_errors)
    checks["cv_metrics"]["contract_errors"] = cv_errors

    llm_metrics, llm_errors = load_json_contract(required_paths["llm_metrics"])
    if llm_metrics is not None:
        if not isinstance(llm_metrics.get("llm_review"), dict):
            llm_errors.append("missing_llm_review_metrics")
        provenance = llm_metrics.get("provenance", {})
        if not str(provenance.get("model", "")).startswith("gemini-"):
            llm_errors.append("provenance_model_must_be_gemini")
        if not provenance.get("human_review_completed_at_utc"):
            llm_errors.append("human_review_completion_missing")
    if llm_errors:
        blockers.append("invalid_llm_metrics_contract")
    checks["llm_metrics"]["contract_valid"] = bool(llm_metrics is not None and not llm_errors)
    checks["llm_metrics"]["contract_errors"] = llm_errors

    production = None
    if production_config:
        env_names = {
            "database_url": "RETURNREVIEW_DATABASE_URL",
            "database_schema": "RETURNREVIEW_DATABASE_SCHEMA",
            "gemini_api_key": "RETURNREVIEW_GEMINI_API_KEY",
            "llm_enabled": "RETURNREVIEW_LLM_ENABLED",
            "cv_model_version": "RETURNREVIEW_CV_MODEL_VERSION",
            "cv_model_path": "RETURNREVIEW_CV_MODEL_PATH",
            "category_model_path": "RETURNREVIEW_CATEGORY_MODEL_PATH",
        }
        production = {
            key: {"env_name": name, "present": bool(environ.get(name))}
            for key, name in env_names.items()
        }
        if not production["gemini_api_key"]["present"]:
            blockers.append("gemini_api_key_not_configured")
        if environ.get("RETURNREVIEW_LLM_ENABLED", "").lower() not in {"1", "true", "yes"}:
            blockers.append("llm_not_enabled")

        db_url = environ.get("RETURNREVIEW_DATABASE_URL", "")
        if not db_url.startswith(("postgresql://", "postgresql+psycopg://", "postgres://")):
            blockers.append("durable_postgresql_not_configured")
        if environ.get("RETURNREVIEW_DATABASE_SCHEMA") != EXPECTED_DATABASE_SCHEMA:
            blockers.append("public_schema_not_configured")
        if environ.get("RETURNREVIEW_CV_MODEL_VERSION") != EXPECTED_CV_MODEL_VERSION:
            blockers.append("cv_lightweight_1_not_configured")

    return {
        "status": "ready" if not blockers else "blocked",
        "truthfulness": "No missing artifact is replaced with a placeholder metric/model.",
        "runtime_contract": {
            "category_verification": "MobileNetV3-Small",
            "damage_segmentation": "multiclass YOLO11n-seg",
            "cv_model_version": EXPECTED_CV_MODEL_VERSION,
            "database_backend": "Railway PostgreSQL",
            "database_schema": EXPECTED_DATABASE_SCHEMA,
            "llm_provider": "Gemini",
        },
        "checks": checks,
        "production_configuration": production,
        "blockers": sorted(set(blockers)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="")
    parser.add_argument(
        "--production-config",
        action="store_true",
        help="Also inspect environment-variable presence and non-secret contracts.",
    )
    args = parser.parse_args()

    payload = build_readiness(Path(args.root), args.production_config, os.environ)
    rendered = json.dumps(payload, indent=2)
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered + "\n", encoding="utf-8")
        print(target)
    else:
        print(rendered)
    raise SystemExit(0 if payload["status"] == "ready" else 2)


if __name__ == "__main__":
    main()
