"""Evaluate semantic OpenCLIP defect prototypes on a held-out folder split."""
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
    parser.add_argument("--test-root", required=True)
    parser.add_argument("--prototypes", required=True)
    parser.add_argument("--similarity-threshold", type=float, required=True)
    parser.add_argument("--margin-threshold", type=float, required=True)
    parser.add_argument("--output", default="artifacts/evaluation/defect_metrics.json")
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
    for class_dir in sorted(Path(args.test_root).iterdir()):
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
            predicted = (
                top_label
                if top_score >= args.similarity_threshold and margin >= args.margin_threshold
                else "unknown"
            )
            rows.append({
                "image": path.name,
                "expected": expected,
                "predicted": predicted,
                "top_score": top_score,
                "margin": margin,
                "scores": scores,
            })

    if not rows:
        raise SystemExit("No held-out defect samples found")

    classes = sorted({r["expected"] for r in rows} | {r["predicted"] for r in rows})
    per_class = {}
    for cls in classes:
        tp = sum(r["expected"] == cls and r["predicted"] == cls for r in rows)
        fp = sum(r["expected"] != cls and r["predicted"] == cls for r in rows)
        fn = sum(r["expected"] == cls and r["predicted"] != cls for r in rows)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[cls] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(r["expected"] == cls for r in rows),
        }

    payload = {
        "semantic_defect_classification": {
            "test_samples": len(rows),
            "similarity_threshold": args.similarity_threshold,
            "margin_threshold": args.margin_threshold,
            "accuracy": sum(r["expected"] == r["predicted"] for r in rows) / len(rows),
            "macro_f1": float(np.mean([v["f1"] for v in per_class.values()])),
            "per_class": per_class,
            "directly_scored_source_labels": ["tear", "squeeze->dent_or_crush", "leakage->unknown"],
            "crushed_corner_scored": False,
        },
        "provenance": (
            "Held-out source crops. tear is a direct source label; squeeze is an explicitly "
            "declared compression-damage proxy for dent_or_crush; leakage is unknown. "
            "No synthetic crushed_corner labels are introduced."
        ),
        "per_sample": rows,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["semantic_defect_classification"], indent=2))
    print(out)


if __name__ == "__main__":
    main()
