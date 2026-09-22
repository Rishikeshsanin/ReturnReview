"""Evaluate OpenCLIP cardboard-box verification on a held-out set.

Expected layout:
  <test-root>/cardboard_box/*
  <test-root>/negative/*

The prototype bank must be created only from reference/training samples.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-root", required=True)
    parser.add_argument("--prototypes", required=True)
    parser.add_argument("--threshold", type=float, required=True)
    parser.add_argument("--output", default="artifacts/evaluation/verification_metrics.json")
    parser.add_argument("--model", default="ViT-B-32")
    parser.add_argument("--pretrained", default="laion2b_s34b_b79k")
    args = parser.parse_args()

    import torch
    import open_clip

    bank = np.load(args.prototypes, allow_pickle=False)
    if "category_cardboard_box" not in bank.files:
        raise SystemExit("Prototype bank is missing category_cardboard_box")
    prototype = bank["category_cardboard_box"]

    model, _, preprocess = open_clip.create_model_and_transforms(args.model, pretrained=args.pretrained)
    model.eval()

    rows = []
    for label, expected in (("cardboard_box", True), ("negative", False)):
        folder = Path(args.test_root) / label
        if not folder.exists():
            continue
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() not in IMAGE_EXTS:
                continue
            tensor = preprocess(Image.open(path).convert("RGB")).unsqueeze(0)
            with torch.no_grad():
                emb = model.encode_image(tensor)
                emb = emb / emb.norm(dim=-1, keepdim=True)
            score = cosine(emb.cpu().numpy()[0], prototype)
            rows.append({
                "image": path.name,
                "expected_box": expected,
                "score": score,
                "predicted_box": score >= args.threshold,
            })

    if not rows:
        raise SystemExit("No held-out verification images found")

    tp = sum(r["expected_box"] and r["predicted_box"] for r in rows)
    tn = sum((not r["expected_box"]) and (not r["predicted_box"]) for r in rows)
    fp = sum((not r["expected_box"]) and r["predicted_box"] for r in rows)
    fn = sum(r["expected_box"] and (not r["predicted_box"]) for r in rows)
    positives = tp + fn
    negatives = tn + fp

    payload = {
        "product_verification": {
            "test_samples": len(rows),
            "threshold": args.threshold,
            "accuracy": (tp + tn) / len(rows),
            "false_accept_rate": fp / negatives if negatives else None,
            "false_reject_rate": fn / positives if positives else None,
            "true_positive": tp,
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
        },
        "per_image": rows,
        "provenance": "Held-out positive and negative images evaluated against a training/reference prototype.",
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
