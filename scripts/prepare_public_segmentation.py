"""Prepare a downloaded YOLO instance-segmentation export for ReturnReview.

This script only remaps EXISTING polygon annotations to the binary class
`damage`. It deliberately refuses detection-box rows and never synthesizes
segmentation masks from rectangles.

Raw/public datasets remain local and are ignored by Git.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def load_yaml(path: Path) -> dict:
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required. Install backend/requirements-cv.txt first."
        ) from exc
    if not path.exists():
        raise SystemExit(f"Missing dataset config: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def normalize_names(raw) -> dict[int, str]:
    if isinstance(raw, list):
        return {idx: str(name) for idx, name in enumerate(raw)}
    if isinstance(raw, dict):
        return {int(idx): str(name) for idx, name in raw.items()}
    raise SystemExit("data.yaml must define names as a list or mapping")


def parse_polygon_row(line: str, label_path: Path) -> tuple[int, list[str]]:
    parts = line.strip().split()
    if not parts:
        raise ValueError("empty")

    # YOLO segmentation row = class + >= 3 xy pairs.
    # A detection box row has only class + 4 numbers and is rejected here.
    if len(parts) < 7 or (len(parts) - 1) % 2:
        raise SystemExit(
            f"{label_path}: non-polygon annotation detected. "
            "Detection boxes must never be converted into segmentation masks."
        )

    try:
        class_id = int(float(parts[0]))
        coords = [float(value) for value in parts[1:]]
    except ValueError as exc:
        raise SystemExit(f"{label_path}: invalid numeric annotation") from exc

    if any(value < 0.0 or value > 1.0 for value in coords):
        raise SystemExit(f"{label_path}: polygon coordinate outside [0, 1]")
    return class_id, parts[1:]


def resolve_split(root: Path, canonical: str) -> tuple[Path, Path] | None:
    names = [canonical]
    if canonical == "val":
        names.extend(["valid", "validation"])
    for name in names:
        image_dir = root / name / "images"
        label_dir = root / name / "labels"
        if image_dir.is_dir() and label_dir.is_dir():
            return image_dir, label_dir
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Downloaded YOLO segmentation export")
    parser.add_argument("--output", required=True, help="Local ReturnReview dataset output")
    parser.add_argument(
        "--include-classes",
        default="tear,squeeze",
        help="Comma-separated source classes to collapse to binary damage",
    )
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--license", required=True)
    args = parser.parse_args()

    source = Path(args.input).resolve()
    output = Path(args.output).resolve()
    if source == output:
        raise SystemExit("Input and output directories must differ")
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")

    cfg = load_yaml(source / "data.yaml")
    names = normalize_names(cfg.get("names"))
    include = {item.strip() for item in args.include_classes.split(",") if item.strip()}
    missing = include - set(names.values())
    if missing:
        raise SystemExit(f"Requested classes not present in source export: {sorted(missing)}")

    included_ids = {idx for idx, name in names.items() if name in include}
    if not included_ids:
        raise SystemExit("No source classes selected")

    output.mkdir(parents=True)
    totals = {
        "images_seen": 0,
        "images_written": 0,
        "polygons_written": 0,
        "polygons_skipped": 0,
    }
    split_counts: dict[str, dict[str, int]] = {}

    for split in ("train", "val", "test"):
        located = resolve_split(source, split)
        if located is None:
            continue
        images_dir, labels_dir = located
        out_images = output / "images" / split
        out_labels = output / "labels" / split
        out_images.mkdir(parents=True)
        out_labels.mkdir(parents=True)

        counts = {"images": 0, "polygons": 0}
        for image_path in sorted(
            path for path in images_dir.iterdir() if path.suffix.lower() in IMAGE_EXTS
        ):
            totals["images_seen"] += 1
            label_path = labels_dir / f"{image_path.stem}.txt"
            if not label_path.exists():
                continue

            accepted: list[str] = []
            for line in label_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                class_id, coords = parse_polygon_row(line, label_path)
                if class_id in included_ids:
                    accepted.append("0 " + " ".join(coords))
                else:
                    totals["polygons_skipped"] += 1

            if not accepted:
                continue

            shutil.copy2(image_path, out_images / image_path.name)
            (out_labels / f"{image_path.stem}.txt").write_text(
                "\n".join(accepted) + "\n", encoding="utf-8"
            )
            counts["images"] += 1
            counts["polygons"] += len(accepted)
            totals["images_written"] += 1
            totals["polygons_written"] += len(accepted)

        split_counts[split] = counts

    if totals["images_written"] == 0:
        shutil.rmtree(output)
        raise SystemExit("No accepted polygon annotations were found")

    yaml_lines = [f"path: {output.as_posix()}", "train: images/train"]
    if (output / "images" / "val").exists():
        yaml_lines.append("val: images/val")
    if (output / "images" / "test").exists():
        yaml_lines.append("test: images/test")
    yaml_lines += ["names:", "  0: damage"]
    (output / "data.yaml").write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")

    manifest = {
        "source_id": args.source_id,
        "source_url": args.source_url,
        "license": args.license,
        "original_classes": names,
        "included_classes": sorted(include),
        "output_class": "damage",
        "conversion": "polygon_class_remap_only",
        "detection_box_conversion_permitted": False,
        "split_counts": split_counts,
        "totals": totals,
    }
    (output / "returnreview_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
