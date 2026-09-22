"""Compute true pixel-level IoU/Dice/precision/recall on a held-out YOLO-seg split.

Expected dataset structure:
  <root>/images/test/*.jpg
  <root>/labels/test/*.txt

Each label line follows YOLO segmentation format:
  class_id x1 y1 x2 y2 ...  (normalized polygon coordinates)
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def polygon_mask(label_path: Path, width: int, height: int) -> np.ndarray:
    mask = np.zeros((height, width), dtype=np.uint8)
    if not label_path.exists():
        return mask
    for raw in label_path.read_text(encoding="utf-8").splitlines():
        parts = raw.strip().split()
        if len(parts) < 7:
            continue
        coords = np.asarray([float(v) for v in parts[1:]], dtype=np.float32).reshape(-1, 2)
        coords[:, 0] *= width
        coords[:, 1] *= height
        cv2.fillPoly(mask, [coords.astype(np.int32)], 1)
    return mask


def prediction_mask(result, width: int, height: int) -> np.ndarray:
    mask = np.zeros((height, width), dtype=np.uint8)
    if result.masks is None:
        return mask
    for polygon in result.masks.xy:
        if len(polygon) >= 3:
            cv2.fillPoly(mask, [np.asarray(polygon, dtype=np.int32)], 1)
    return mask


def scores(gt: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    gt_b = gt.astype(bool)
    pred_b = pred.astype(bool)
    tp = int(np.logical_and(gt_b, pred_b).sum())
    fp = int(np.logical_and(~gt_b, pred_b).sum())
    fn = int(np.logical_and(gt_b, ~pred_b).sum())
    union = tp + fp + fn
    denom_dice = 2 * tp + fp + fn
    return {
        "iou": 1.0 if union == 0 else tp / union,
        "dice": 1.0 if denom_dice == 0 else (2 * tp) / denom_dice,
        "precision": 1.0 if tp + fp == 0 and not gt_b.any() else (tp / (tp + fp) if tp + fp else 0.0),
        "recall": 1.0 if tp + fn == 0 else tp / (tp + fn),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", default="artifacts/evaluation/metrics.json")
    parser.add_argument("--conf", type=float, default=0.20)
    args = parser.parse_args()

    root = Path(args.root)
    images = sorted(p for p in (root / "images" / "test").iterdir() if p.suffix.lower() in IMAGE_EXTS)
    if not images:
        raise SystemExit("No held-out test images found")

    model = YOLO(args.model)
    rows = []
    for image_path in images:
        with Image.open(image_path) as im:
            width, height = im.size
        gt = polygon_mask(root / "labels" / "test" / f"{image_path.stem}.txt", width, height)
        result = model.predict(str(image_path), conf=args.conf, verbose=False)[0]
        pred = prediction_mask(result, width, height)
        row = {"image": image_path.name, "has_damage": bool(gt.any()), **scores(gt, pred)}
        rows.append(row)

    damaged = [r for r in rows if r["has_damage"]]
    def avg(key: str, source: list[dict]) -> float | None:
        return round(float(np.mean([r[key] for r in source])), 6) if source else None

    payload = {
        "segmentation": {
            "test_images": len(rows),
            "damaged_test_images": len(damaged),
            "mean_iou_all": avg("iou", rows),
            "mean_dice_all": avg("dice", rows),
            "mean_iou_damaged_only": avg("iou", damaged),
            "mean_dice_damaged_only": avg("dice", damaged),
            "pixel_precision_all": avg("precision", rows),
            "pixel_recall_all": avg("recall", rows),
        },
        "per_image": rows,
        "provenance": "Computed directly from held-out YOLO polygon masks and model predictions.",
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
