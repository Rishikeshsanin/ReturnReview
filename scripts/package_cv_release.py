"""Package validated ReturnReview CV artifacts for a controlled release.

This script does not train or evaluate a model. It refuses incomplete artifacts
and writes a checksum/provenance manifest so the exact checkpoint/prototype bank
used in a demo or deployment can be reproduced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REQUIRED_PROTOTYPES = {
    "category_cardboard_box",
    "defect_tear",
    "defect_crushed_corner",
    "defect_dent_or_crush",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_file(path: Path, label: str) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"{label} is missing or empty: {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--prototypes", required=True)
    parser.add_argument("--model-version", required=True)
    parser.add_argument("--category-threshold", required=True, type=float)
    parser.add_argument("--defect-threshold", required=True, type=float)
    parser.add_argument("--defect-margin", required=True, type=float)
    parser.add_argument(
        "--output-dir",
        default="artifacts/cv-release",
    )
    args = parser.parse_args()

    checkpoint = Path(args.checkpoint).resolve()
    prototypes = Path(args.prototypes).resolve()
    output = Path(args.output_dir).resolve()

    require_file(checkpoint, "Segmentation checkpoint")
    require_file(prototypes, "Prototype bank")

    if checkpoint.suffix.lower() != ".pt":
        raise SystemExit("Expected a validated Ultralytics .pt checkpoint")
    if prototypes.suffix.lower() != ".npz":
        raise SystemExit("Expected an .npz OpenCLIP prototype bank")

    bank = np.load(prototypes, allow_pickle=False)
    keys = set(bank.files)
    missing = sorted(REQUIRED_PROTOTYPES - keys)
    if missing:
        raise SystemExit(f"Prototype bank missing required keys: {missing}")

    if not 0.0 <= args.category_threshold <= 1.0:
        raise SystemExit("category threshold must be in [0, 1]")
    if not 0.0 <= args.defect_threshold <= 1.0:
        raise SystemExit("defect threshold must be in [0, 1]")
    if not 0.0 <= args.defect_margin <= 1.0:
        raise SystemExit("defect margin must be in [0, 1]")

    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty release directory: {output}")
    output.mkdir(parents=True, exist_ok=True)

    checkpoint_out = output / "best.pt"
    prototypes_out = output / "prototypes.npz"
    shutil.copy2(checkpoint, checkpoint_out)
    shutil.copy2(prototypes, prototypes_out)

    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model_version": args.model_version,
        "artifacts": {
            "checkpoint": {
                "filename": checkpoint_out.name,
                "sha256": sha256(checkpoint_out),
                "bytes": checkpoint_out.stat().st_size,
            },
            "prototype_bank": {
                "filename": prototypes_out.name,
                "sha256": sha256(prototypes_out),
                "bytes": prototypes_out.stat().st_size,
                "keys": sorted(keys),
            },
        },
        "thresholds": {
            "category_similarity": args.category_threshold,
            "defect_similarity": args.defect_threshold,
            "defect_margin": args.defect_margin,
        },
        "claims": {
            "training_metrics_included": False,
            "evaluation_metrics_included": False,
            "note": (
                "Metrics must be generated separately from held-out evaluation "
                "and must never be inferred from this release package."
            ),
        },
    }
    (output / "release_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
