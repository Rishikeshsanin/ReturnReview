"""Choose the category-verification threshold using validation data only.

Never calibrate on the held-out test set.
Expected validation layout:
  <validation-root>/cardboard_box/*
  <validation-root>/negative/*
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation-root", required=True)
    parser.add_argument("--prototypes", required=True)
    parser.add_argument("--model", default="ViT-B-32")
    parser.add_argument("--pretrained", default="laion2b_s34b_b79k")
    parser.add_argument("--output", default="artifacts/evaluation/category_calibration.json")
    args = parser.parse_args()

    import torch
    import open_clip

    bank = np.load(args.prototypes, allow_pickle=False)
    prototype = bank["category_cardboard_box"]
    model, _, preprocess = open_clip.create_model_and_transforms(args.model, pretrained=args.pretrained)
    model.eval()

    samples: list[tuple[float, bool]] = []
    for label, expected in (("cardboard_box", True), ("negative", False)):
        folder = Path(args.validation_root) / label
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() not in IMAGE_EXTS:
                continue
            tensor = preprocess(Image.open(path).convert("RGB")).unsqueeze(0)
            with torch.no_grad():
                emb = model.encode_image(tensor)
                emb = emb / emb.norm(dim=-1, keepdim=True)
            vec = emb.cpu().numpy()[0]
            score = float(np.dot(vec, prototype) / (np.linalg.norm(vec) * np.linalg.norm(prototype)))
            samples.append((score, expected))

    if not samples:
        raise SystemExit("No validation samples found")

    best = None
    for threshold in np.linspace(-1.0, 1.0, 2001):
        correct = sum((score >= threshold) == expected for score, expected in samples)
        accuracy = correct / len(samples)
        if best is None or accuracy > best[0]:
            best = (accuracy, float(threshold))

    payload = {
        "category_calibration": {
            "validation_samples": len(samples),
            "validation_accuracy": best[0],
            "recommended_threshold": best[1],
            "positive_samples": sum(expected for _, expected in samples),
            "negative_samples": sum(not expected for _, expected in samples),
        },
        "provenance": "Threshold selected using validation positives and generic non-box negatives only.",
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["category_calibration"], indent=2))
    print(out)


if __name__ == "__main__":
    main()
