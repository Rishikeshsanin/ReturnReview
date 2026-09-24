"""Evaluate the trained segmentation model on the held-out test split."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", default="artifacts/evaluation/segmentation_map_metrics.json")
    args = parser.parse_args()

    from ultralytics import YOLO
    model = YOLO(args.model)
    metrics = model.val(data=args.data, split="test")
    output = {
        "segmentation": {
            "mask_map50": float(metrics.seg.map50),
            "mask_map50_95": float(metrics.seg.map),
            "box_map50": float(metrics.box.map50),
        },
        "note": "Generated from the held-out test split; do not edit manually.",
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
