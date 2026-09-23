"""Validate a YOLO segmentation export before ReturnReview training.

Checks:
- expected images/labels train/val/test layout
- every label row uses class 0 (single binary class: damage)
- each polygon has at least 3 points
- all polygon coordinates are finite and normalized to [0, 1]
- image/label basenames match
- reports empty labels as valid normal/no-visible-damage examples

This script never edits the dataset.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
SPLITS = ("train", "val", "test")


def parse_label(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return errors, warnings

    for line_no, raw in enumerate(text.splitlines(), start=1):
        parts = raw.split()
        if len(parts) < 7:
            errors.append(f"{path}:{line_no}: polygon needs class + at least 3 x/y points")
            continue
        try:
            class_id = int(parts[0])
        except ValueError:
            errors.append(f"{path}:{line_no}: class id is not an integer")
            continue
        if class_id != 0:
            errors.append(f"{path}:{line_no}: only class 0 (damage) is allowed; got {class_id}")

        coord_tokens = parts[1:]
        if len(coord_tokens) % 2:
            errors.append(f"{path}:{line_no}: polygon coordinate count must be even")
            continue
        try:
            coords = [float(value) for value in coord_tokens]
        except ValueError:
            errors.append(f"{path}:{line_no}: non-numeric polygon coordinate")
            continue

        for value in coords:
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                errors.append(f"{path}:{line_no}: coordinate outside [0,1]: {value}")
                break

        points = list(zip(coords[0::2], coords[1::2]))
        if len(set(points)) < 3:
            errors.append(f"{path}:{line_no}: polygon has fewer than 3 distinct points")

    return errors, warnings


def validate(root: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    split_counts: dict[str, dict[str, int]] = {}
    total_polygons = 0

    for split in SPLITS:
        image_dir = root / "images" / split
        label_dir = root / "labels" / split
        if not image_dir.is_dir():
            errors.append(f"missing directory: {image_dir}")
            continue
        if not label_dir.is_dir():
            errors.append(f"missing directory: {label_dir}")
            continue

        images = {p.stem: p for p in image_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS}
        labels = {p.stem: p for p in label_dir.glob("*.txt") if p.is_file()}

        missing_labels = sorted(set(images) - set(labels))
        orphan_labels = sorted(set(labels) - set(images))
        if missing_labels:
            errors.append(f"{split}: {len(missing_labels)} images have no label file")
        if orphan_labels:
            errors.append(f"{split}: {len(orphan_labels)} label files have no matching image")

        normal = 0
        damaged = 0
        polygons = 0
        for stem in sorted(set(images) & set(labels)):
            label_path = labels[stem]
            text = label_path.read_text(encoding="utf-8").strip()
            if text:
                damaged += 1
                polygons += len(text.splitlines())
            else:
                normal += 1
            row_errors, row_warnings = parse_label(label_path)
            errors.extend(row_errors)
            warnings.extend(row_warnings)

        total_polygons += polygons
        split_counts[split] = {
            "images": len(images),
            "labels": len(labels),
            "normal_empty_labels": normal,
            "damaged_nonempty_labels": damaged,
            "polygons": polygons,
        }

    duplicate_names: dict[str, list[str]] = {}
    locations: dict[str, list[str]] = {}
    for split in SPLITS:
        image_dir = root / "images" / split
        if image_dir.is_dir():
            for path in image_dir.iterdir():
                if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
                    locations.setdefault(path.stem, []).append(split)
    for stem, seen in locations.items():
        if len(seen) > 1:
            duplicate_names[stem] = seen
    if duplicate_names:
        errors.append(
            f"{len(duplicate_names)} image basenames appear in multiple splits; "
            "possible leakage or duplicate export"
        )

    return {
        "status": "valid" if not errors else "invalid",
        "root": str(root.resolve()),
        "expected_class_map": {"0": "damage"},
        "split_counts": split_counts,
        "total_polygons": total_polygons,
        "duplicate_basenames_across_splits": duplicate_names,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", help="YOLO segmentation dataset root")
    parser.add_argument("--output", default="artifacts/segmentation_dataset_validation.json")
    args = parser.parse_args()

    report = validate(Path(args.root))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["split_counts"], indent=2))
    print(f"status={report['status']} errors={len(report['errors'])} -> {out}")
    if report["errors"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
