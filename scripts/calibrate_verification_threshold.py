"""Choose the category-verification threshold using validation data only.

Never calibrate on the held-out test set.
Expected validation layout:
  <validation-root>/cardboard_box/*
  <validation-root>/negative/*
"""
from __future__ import annotations
import argparse
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

    print(f"validation_samples={len(samples)}")
    print(f"best_validation_accuracy={best[0]:.6f}")
    print(f"recommended_threshold={best[1]:.6f}")
    print("Record this threshold with the dataset/model version. Evaluate it only once on the held-out test split.")


if __name__ == "__main__":
    main()
