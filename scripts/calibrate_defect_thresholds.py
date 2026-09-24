"""Calibrate semantic defect similarity and ambiguity thresholds on validation data only."""
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation-root", required=True)
    parser.add_argument("--prototypes", required=True)
    parser.add_argument("--output", default="artifacts/evaluation/defect_calibration.json")
    parser.add_argument("--model", default="ViT-B-32")
    parser.add_argument("--pretrained", default="laion2b_s34b_b79k")
    args = parser.parse_args()

    import torch
    import open_clip

    raw = np.load(args.prototypes, allow_pickle=False)
    bank = {
        key.removeprefix("defect_"): raw[key]
        for key in raw.files
        if key.startswith("defect_")
    }
    if not bank:
        raise SystemExit("Prototype bank contains no defect_* entries")

    model, _, preprocess = open_clip.create_model_and_transforms(
        args.model, pretrained=args.pretrained
    )
    model.eval()

    rows: list[dict] = []
    root = Path(args.validation_root)
    for class_dir in sorted(root.iterdir()):
        if not class_dir.is_dir():
            continue
        expected = class_dir.name
        for path in sorted(class_dir.iterdir()):
            if path.suffix.lower() not in IMAGE_EXTS:
                continue
            tensor = preprocess(Image.open(path).convert("RGB")).unsqueeze(0)
            with torch.no_grad():
                emb = model.encode_image(tensor)
                emb = emb / emb.norm(dim=-1, keepdim=True)
            vec = emb.cpu().numpy()[0]
            scores = {name: cosine(vec, proto) for name, proto in bank.items()}
            ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
            top_label, top_score = ordered[0]
            margin = top_score - ordered[1][1] if len(ordered) > 1 else top_score
            rows.append({
                "image": path.name,
                "expected": expected,
                "top_label": top_label,
                "top_score": top_score,
                "margin": margin,
            })

    if not rows:
        raise SystemExit("No defect validation samples found")

    best = None
    for similarity in np.linspace(-0.2, 0.8, 201):
        for margin_threshold in np.linspace(0.0, 0.20, 101):
            correct = 0
            for row in rows:
                predicted = (
                    row["top_label"]
                    if row["top_score"] >= similarity and row["margin"] >= margin_threshold
                    else "unknown"
                )
                correct += predicted == row["expected"]
            accuracy = correct / len(rows)
            candidate = (accuracy, float(similarity), float(margin_threshold))
            if best is None or candidate > best:
                best = candidate

    payload = {
        "defect_calibration": {
            "validation_samples": len(rows),
            "validation_accuracy": best[0],
            "similarity_threshold": best[1],
            "margin_threshold": best[2],
            "classes_seen": sorted({row["expected"] for row in rows}),
        },
        "mapping_note": (
            "Public source tear is a direct label match; source squeeze is a declared "
            "compression-damage proxy for dent_or_crush; source leakage is used only "
            "as an out-of-taxonomy unknown rejection example."
        ),
        "per_sample": rows,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["defect_calibration"], indent=2))
    print(out)


if __name__ == "__main__":
    main()
