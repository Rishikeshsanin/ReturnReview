"""Truthful release-readiness checker for ReturnReview.

This script never fabricates metrics. It reports concrete files/configuration that
must exist before a final academic demo can be called fully ready.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def file_state(path: Path) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="")
    parser.add_argument(
        "--production-config",
        action="store_true",
        help="Also inspect environment-variable presence (values are never printed).",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    required_files = {
        "segmentation_checkpoint": root / "backend/models/checkpoints/best.pt",
        "prototype_bank": root / "backend/models/prototypes.npz",
        "heldout_metrics": root / "artifacts/evaluation/metrics.json",
        "llm_metrics": root / "artifacts/evaluation/llm_metrics.json",
        "llm_eval_set": root / "data/evaluation/llm_eval_cases.jsonl",
    }

    checks = {name: file_state(path) for name, path in required_files.items()}

    blockers: list[str] = []
    for name in ("segmentation_checkpoint", "prototype_bank", "heldout_metrics", "llm_metrics"):
        if not checks[name]["exists"]:
            blockers.append(f"missing_{name}")

    if not checks["llm_eval_set"]["exists"]:
        blockers.append("missing_llm_eval_set")

    production = None
    if args.production_config:
        env_names = {
            "database_url": "RETURNREVIEW_DATABASE_URL",
            "database_schema": "RETURNREVIEW_DATABASE_SCHEMA",
            "gemini_api_key": "RETURNREVIEW_GEMINI_API_KEY",
            "llm_enabled": "RETURNREVIEW_LLM_ENABLED",
            "cv_model_version": "RETURNREVIEW_CV_MODEL_VERSION",
        }
        production = {
            key: {"env_name": name, "present": bool(os.getenv(name))}
            for key, name in env_names.items()
        }
        # Presence only; secret values are never emitted.
        if not production["gemini_api_key"]["present"]:
            blockers.append("gemini_api_key_not_configured")
        if os.getenv("RETURNREVIEW_LLM_ENABLED", "").lower() not in {"1", "true", "yes"}:
            blockers.append("llm_not_enabled")

        db_url = os.getenv("RETURNREVIEW_DATABASE_URL", "")
        if not db_url.startswith(("postgresql://", "postgresql+psycopg://", "postgres://")):
            blockers.append("durable_postgresql_not_configured")
        if os.getenv("RETURNREVIEW_DATABASE_SCHEMA") != "return_review":
            blockers.append("return_review_schema_not_configured")

    payload = {
        "status": "ready" if not blockers else "blocked",
        "truthfulness": "No missing artifact is replaced with a placeholder metric/model.",
        "checks": checks,
        "production_configuration": production,
        "blockers": sorted(set(blockers)),
    }

    rendered = json.dumps(payload, indent=2)
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered + "\n", encoding="utf-8")
        print(target)
    else:
        print(rendered)

    raise SystemExit(0 if not blockers else 2)


if __name__ == "__main__":
    main()
