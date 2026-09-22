"""Audit raw ReturnReview pilot photos before annotation.

The audit is intentionally non-destructive: it reads images and writes a JSON report.
It checks decoding, dimensions, blur, brightness, exact duplicates and near-duplicates.

Recommended filename:
  box03_crushedcorner_session1_front_01.jpg
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from itertools import combinations
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
NAME_RE = re.compile(
    r"^(?P<object>box\d+)_(?P<label>normal|tear|crushedcorner|crushed_corner|dentcrush|dent_or_crush)_"
    r"(?P<session>session\d+)_(?P<view>front|back|left|right|top|bottom|other)_(?P<index>\d+)$",
    re.IGNORECASE,
)
LABEL_MAP = {
    "normal": "normal",
    "tear": "tear",
    "crushedcorner": "crushed_corner",
    "crushed_corner": "crushed_corner",
    "dentcrush": "dent_or_crush",
    "dent_or_crush": "dent_or_crush",
}


def parse_filename(path: Path) -> dict | None:
    match = NAME_RE.match(path.stem)
    if not match:
        return None
    row = match.groupdict()
    row["label"] = LABEL_MAP[row["label"].lower()]
    row["group_id"] = f"{row['object'].lower()}_{row['session'].lower()}"
    return row


def dhash(image: Image.Image, hash_size: int = 8) -> int:
    gray = image.convert("L").resize((hash_size + 1, hash_size))
    pixels = np.asarray(gray)
    diff = pixels[:, 1:] > pixels[:, :-1]
    value = 0
    for bit in diff.flatten():
        value = (value << 1) | int(bit)
    return value


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def inspect_image(path: Path) -> dict:
    raw = path.read_bytes()
    exact_hash = hashlib.sha256(raw).hexdigest()
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        width, height = image.size
        arr = np.asarray(image)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    parsed = parse_filename(path)
    warnings = []
    if min(width, height) < 256:
        warnings.append("low_resolution")
    if blur < 70:
        warnings.append("possibly_blurry")
    if brightness < 45:
        warnings.append("possibly_too_dark")
    if brightness > 225:
        warnings.append("possibly_overexposed")
    if parsed is None:
        warnings.append("filename_not_in_recommended_format")
    return {
        "file": path.name,
        "path": str(path),
        "width": width,
        "height": height,
        "blur_score": round(blur, 2),
        "brightness_mean": round(brightness, 2),
        "sha256": exact_hash,
        "dhash": dhash(image),
        "metadata": parsed,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", help="Folder containing raw pilot images")
    parser.add_argument("--output", default="artifacts/pilot_audit.json")
    parser.add_argument("--near-duplicate-distance", type=int, default=3)
    args = parser.parse_args()

    root = Path(args.root)
    paths = sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )
    if not paths:
        raise SystemExit("No JPEG/PNG/WebP images found")

    rows = []
    unreadable = []
    for path in paths:
        try:
            rows.append(inspect_image(path))
        except Exception as exc:
            unreadable.append({"file": str(path), "error": type(exc).__name__})

    exact_map: dict[str, list[str]] = {}
    for row in rows:
        exact_map.setdefault(row["sha256"], []).append(row["file"])
    exact_duplicates = [v for v in exact_map.values() if len(v) > 1]

    near_duplicates = []
    for left, right in combinations(rows, 2):
        if left["sha256"] == right["sha256"]:
            continue
        distance = hamming(int(left["dhash"]), int(right["dhash"]))
        if distance <= args.near_duplicate_distance:
            near_duplicates.append({
                "left": left["file"],
                "right": right["file"],
                "dhash_distance": distance,
            })

    label_counts: dict[str, int] = {}
    group_counts: dict[str, int] = {}
    for row in rows:
        meta = row["metadata"]
        if not meta:
            continue
        label_counts[meta["label"]] = label_counts.get(meta["label"], 0) + 1
        group_counts[meta["group_id"]] = group_counts.get(meta["group_id"], 0) + 1

    report = {
        "root": str(root.resolve()),
        "total_files": len(paths),
        "readable_images": len(rows),
        "unreadable": unreadable,
        "label_counts": label_counts,
        "physical_session_groups": group_counts,
        "exact_duplicates": exact_duplicates,
        "near_duplicates": near_duplicates,
        "images": [{k: v for k, v in row.items() if k != "dhash"} for row in rows],
        "threshold_notes": {
            "blur_below": 70,
            "dark_below": 45,
            "overexposed_above": 225,
            "near_duplicate_dhash_distance_at_most": args.near_duplicate_distance,
            "note": "Warnings are review cues, not automatic rejection rules.",
        },
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Audited {len(rows)} readable images -> {out}")
    print("Labels:", label_counts)
    print("Groups:", len(group_counts))
    print("Exact duplicate sets:", len(exact_duplicates))
    print("Near-duplicate pairs:", len(near_duplicates))


if __name__ == "__main__":
    main()
