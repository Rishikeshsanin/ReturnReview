"""Evaluate OpenCLIP prototype defect recognition on a held-out folder dataset.

Expected:
  <test-root>/tear/*
  <test-root>/crushed_corner/*
  <test-root>/dent_or_crush/*
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
    parser.add_argument("--test-root", required=True)
    parser.add_argument("--prototypes", required=True)
    parser.add_argument("--output", default="artifacts/evaluation/fewshot_metrics.json")
    parser.add_argument("--model", default="ViT-B-32")
    parser.add_argument("--pretrained", default="laion2b_s34b_b79k")
    args = parser.parse_args()

    import torch
    import open_clip
    model, _, preprocess = open_clip.create_model_and_transforms(args.model, pretrained=args.pretrained)
    model.eval()
    bank_raw = np.load(args.prototypes, allow_pickle=False)
    bank = {
        k.removeprefix("defect_"): bank_raw[k]
        for k in bank_raw.files if k.startswith("defect_")
    }
    if not bank:
        raise SystemExit("Prototype bank contains no defect_* entries")

    y_true, y_pred = [], []
    for class_dir in sorted(Path(args.test_root).iterdir()):
        if not class_dir.is_dir():
            continue
        label = class_dir.name
        for path in class_dir.iterdir():
            if path.suffix.lower() not in IMAGE_EXTS:
                continue
            tensor = preprocess(Image.open(path).convert("RGB")).unsqueeze(0)
            with torch.no_grad():
                emb = model.encode_image(tensor)
                emb = emb / emb.norm(dim=-1, keepdim=True)
            vec = emb.cpu().numpy()[0]
            pred = max(bank, key=lambda k: float(np.dot(vec, bank[k]) / (np.linalg.norm(vec) * np.linalg.norm(bank[k]))))
            y_true.append(label)
            y_pred.append(pred)

    if not y_true:
        raise SystemExit("No held-out few-shot images found")

    classes = sorted(set(y_true) | set(y_pred))
    per_class = {}
    for c in classes:
        tp = sum(t == c and p == c for t, p in zip(y_true, y_pred))
        fp = sum(t != c and p == c for t, p in zip(y_true, y_pred))
        fn = sum(t == c and p != c for t, p in zip(y_true, y_pred))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[c] = {"precision": precision, "recall": recall, "f1": f1}

    accuracy = sum(t == p for t, p in zip(y_true, y_pred)) / len(y_true)
    macro_f1 = float(np.mean([v["f1"] for v in per_class.values()]))
    payload = {
        "few_shot": {
            "test_samples": len(y_true),
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "per_class": per_class,
            "confusion_pairs": [{"actual": t, "predicted": p} for t, p in zip(y_true, y_pred)],
        },
        "provenance": "Held-out images classified against prototypes built only from reference/training examples.",
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
