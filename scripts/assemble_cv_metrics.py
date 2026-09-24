"""Assemble ReturnReview CV evaluation artifacts without inventing missing metrics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read(path: str) -> dict:
    p = Path(path)
    if not p.is_file():
        raise SystemExit(f"Missing required metric artifact: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pixel", required=True)
    parser.add_argument("--map", required=True)
    parser.add_argument("--category-calibration", required=True)
    parser.add_argument("--category-test", required=True)
    parser.add_argument("--defect-calibration", required=True)
    parser.add_argument("--defect-test", required=True)
    parser.add_argument("--dataset-validation", required=True)
    parser.add_argument("--output", default="artifacts/evaluation/cv_metrics.json")
    args = parser.parse_args()

    pixel = read(args.pixel)
    map_metrics = read(args.map)
    category_cal = read(args.category_calibration)
    category_test = read(args.category_test)
    defect_cal = read(args.defect_calibration)
    defect_test = read(args.defect_test)
    dataset_validation = read(args.dataset_validation)

    payload = {
        "status": "evaluated_public_pilot",
        "scope": "public_pilot_not_project_controlled_final",
        "segmentation": {
            **pixel["segmentation"],
            **map_metrics["segmentation"],
        },
        "product_verification": category_test["product_verification"],
        "semantic_defect_classification": defect_test["semantic_defect_classification"],
        "calibration": {
            "category_similarity_threshold": category_cal["category_calibration"]["recommended_threshold"],
            "defect_similarity_threshold": defect_cal["defect_calibration"]["similarity_threshold"],
            "defect_margin_threshold": defect_cal["defect_calibration"]["margin_threshold"],
        },
        "dataset": {
            "validation_status": dataset_validation["status"],
            "split_counts": dataset_validation["split_counts"],
            "source": "Roboflow box instance-segmentation public dataset, CC BY 4.0; selected tear+squeeze polygons collapsed to binary damage.",
            "limitations": [
                "This is a public-data pilot, not the requested 28-image project-controlled capture.",
                "squeeze is used only as an explicitly declared compression-damage proxy for dent_or_crush during subtype evaluation.",
                "leakage is used only as an out-of-taxonomy unknown rejection example.",
                "crushed_corner has no direct held-out source label in this public pilot and is not scored.",
                "Generic non-box images are used as product-verification negatives.",
            ],
        },
        "provenance": {
            "pixel_metrics": args.pixel,
            "map_metrics": args.map,
            "category_calibration": args.category_calibration,
            "category_test": args.category_test,
            "defect_calibration": args.defect_calibration,
            "defect_test": args.defect_test,
            "dataset_validation": args.dataset_validation,
        },
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "segmentation": payload["segmentation"],
        "product_verification": payload["product_verification"],
        "semantic_defect_classification": payload["semantic_defect_classification"],
        "calibration": payload["calibration"],
    }, indent=2))
    print(out)


if __name__ == "__main__":
    main()
