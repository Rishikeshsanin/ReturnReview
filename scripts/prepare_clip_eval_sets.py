"""Build leakage-preserving OpenCLIP validation/test folders from a raw Roboflow export.

Direct source-label mappings used for subtype evaluation:
- tear -> tear
- squeeze -> dent_or_crush (declared compression-damage proxy)
- leakage -> unknown (out-of-taxonomy rejection example)

crushed_corner remains in the runtime semantic prototype bank but is not
scored unless a future held-out source supplies that label. This script does
not invent subtype labels.

Category verification uses source parcel images as positives and a separate
generic negative-image folder. Negative images are deterministically split
between validation and test.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path

from PIL import Image
import yaml

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
CLASS_MAP = {
    "tear": "tear",
    "squeeze": "dent_or_crush",
    "leakage": "unknown",
}


def normalize_names(raw) -> dict[int, str]:
    if isinstance(raw, list):
        return {idx: str(name) for idx, name in enumerate(raw)}
    if isinstance(raw, dict):
        return {int(idx): str(name) for idx, name in raw.items()}
    raise SystemExit("data.yaml must define names")


def resolve_split(root: Path, canonical: str) -> tuple[Path, Path]:
    names = [canonical]
    if canonical == "val":
        names += ["valid", "validation"]
    for name in names:
        images = root / name / "images"
        labels = root / name / "labels"
        if images.is_dir() and labels.is_dir():
            return images, labels
    raise SystemExit(f"Could not locate source split: {canonical}")


def polygon_bounds(tokens: list[str], width: int, height: int) -> tuple[int, int, int, int]:
    coords = [float(v) for v in tokens]
    if len(coords) < 6 or len(coords) % 2:
        raise ValueError("not a segmentation polygon")
    xs = coords[0::2]
    ys = coords[1::2]
    x1, x2 = min(xs) * width, max(xs) * width
    y1, y2 = min(ys) * height, max(ys) * height
    pad_x = max(4, (x2 - x1) * 0.12)
    pad_y = max(4, (y2 - y1) * 0.12)
    return (
        max(0, int(x1 - pad_x)),
        max(0, int(y1 - pad_y)),
        min(width, int(x2 + pad_x)),
        min(height, int(y2 + pad_y)),
    )


def all_images(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Raw Roboflow segmentation export")
    parser.add_argument("--negative-images", required=True, help="Generic non-box image directory")
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-positive-per-split", type=int, default=80)
    parser.add_argument("--max-negative-per-split", type=int, default=80)
    parser.add_argument("--max-crops-per-class-split", type=int, default=80)
    parser.add_argument("--seed", type=int, default=20260924)
    args = parser.parse_args()

    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    names = normalize_names(
        (yaml.safe_load((source / "data.yaml").read_text(encoding="utf-8")) or {}).get("names")
    )
    rng = random.Random(args.seed)
    report: dict[str, object] = {
        "source": str(source),
        "seed": args.seed,
        "defect_mapping": CLASS_MAP,
        "limitations": [
            "squeeze is explicitly treated as a compression-damage proxy for dent_or_crush.",
            "leakage is evaluated as unknown/out-of-taxonomy.",
            "crushed_corner has no direct source label in this public dataset and is not assigned synthetic labels.",
        ],
        "category": {},
        "defects": {},
    }

    for split in ("val", "test"):
        images_dir, _ = resolve_split(source, split)
        positives = sorted(
            p for p in images_dir.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS
        )
        selected = positives[:]
        rng.shuffle(selected)
        selected = sorted(selected[: args.max_positive_per_split], key=lambda p: p.name)
        target = output / "category" / split / "cardboard_box"
        target.mkdir(parents=True, exist_ok=True)
        for image in selected:
            shutil.copy2(image, target / image.name)
        report["category"][f"{split}_positive"] = len(selected)

    negatives = all_images(Path(args.negative_images).resolve())
    if len(negatives) < 2:
        raise SystemExit("Need at least two generic negative images")
    rng.shuffle(negatives)
    wanted = args.max_negative_per_split
    val_neg = negatives[:wanted]
    test_neg = negatives[wanted : wanted * 2]
    if not test_neg:
        midpoint = max(1, len(negatives) // 2)
        val_neg, test_neg = negatives[:midpoint], negatives[midpoint:]
    for split, selected in (("val", val_neg), ("test", test_neg)):
        target = output / "category" / split / "negative"
        target.mkdir(parents=True, exist_ok=True)
        for idx, image in enumerate(selected):
            shutil.copy2(image, target / f"negative_{idx:04d}{image.suffix.lower()}")
        report["category"][f"{split}_negative"] = len(selected)

    for split in ("val", "test"):
        images_dir, labels_dir = resolve_split(source, split)
        counters = {label: 0 for label in set(CLASS_MAP.values())}
        candidates: dict[str, list[tuple[Path, int, tuple[int, int, int, int]]]] = {
            label: [] for label in counters
        }
        for image_path in sorted(
            p for p in images_dir.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS
        ):
            label_path = labels_dir / f"{image_path.stem}.txt"
            if not label_path.is_file():
                continue
            with Image.open(image_path) as image:
                width, height = image.size
            for line_idx, raw in enumerate(label_path.read_text(encoding="utf-8").splitlines()):
                parts = raw.strip().split()
                if len(parts) < 7:
                    continue
                class_id = int(float(parts[0]))
                source_name = names.get(class_id)
                target_label = CLASS_MAP.get(source_name or "")
                if target_label is None:
                    continue
                try:
                    bounds = polygon_bounds(parts[1:], width, height)
                except ValueError:
                    continue
                candidates[target_label].append((image_path, line_idx, bounds))

        report["defects"][split] = {}
        for label, rows in candidates.items():
            rng.shuffle(rows)
            rows = rows[: args.max_crops_per_class_split]
            target = output / "defects" / split / label
            target.mkdir(parents=True, exist_ok=True)
            for idx, (image_path, line_idx, bounds) in enumerate(rows):
                with Image.open(image_path) as image:
                    crop = image.convert("RGB").crop(bounds)
                    crop.save(target / f"{image_path.stem}_{line_idx:02d}_{idx:03d}.jpg", quality=92)
            counters[label] = len(rows)
            report["defects"][split][label] = len(rows)

    output.mkdir(parents=True, exist_ok=True)
    (output / "eval_manifest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
