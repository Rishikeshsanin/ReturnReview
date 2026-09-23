"""Validate the controlled 24–30 image ReturnReview pilot manifest."""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

ALLOWED_LABELS = {"normal", "tear", "crushed_corner", "dent_or_crush"}
REQUIRED_DEFECTS = {"tear", "crushed_corner", "dent_or_crush"}
ALLOWED_VIEWS = {"front", "left", "right", "top"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data/pilot_manifest.csv")
    parser.add_argument(
        "--images-dir",
        default="",
        help="Optional directory; when set, require every manifest image to exist.",
    )
    args = parser.parse_args()

    path = Path(args.manifest)
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    if not 24 <= len(rows) <= 30:
        raise SystemExit(f"Pilot must contain 24–30 rows, found {len(rows)}")

    filenames = [row["filename"].strip() for row in rows]
    if len(filenames) != len(set(filenames)):
        raise SystemExit("Duplicate filenames exist in pilot manifest")

    item_ids = {row["item_id"].strip() for row in rows}
    if len(item_ids) < 5:
        raise SystemExit(f"Need at least 5 physical item/session IDs, found {len(item_ids)}")

    labels = Counter(row["defect_label"].strip() for row in rows)
    unknown = set(labels) - ALLOWED_LABELS
    if unknown:
        raise SystemExit(f"Unknown defect labels: {sorted(unknown)}")
    missing = REQUIRED_DEFECTS - set(labels)
    if missing:
        raise SystemExit(f"Missing required defect labels: {sorted(missing)}")
    if labels["normal"] < 4:
        raise SystemExit("Pilot needs at least 4 normal/no-damage images")

    per_item_views: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        view = row["view"].strip()
        if view not in ALLOWED_VIEWS:
            raise SystemExit(f"Invalid view {view!r} for {row['filename']}")
        per_item_views[row["item_id"].strip()].add(view)

    for item_id, views in per_item_views.items():
        if len(views) < 3:
            raise SystemExit(f"{item_id} needs at least 3 distinct views, found {sorted(views)}")

    backgrounds = {row["background"].strip() for row in rows if row["background"].strip()}
    lighting = {row["lighting"].strip() for row in rows if row["lighting"].strip()}
    if len(backgrounds) < 2:
        raise SystemExit("Pilot needs at least 2 backgrounds")
    if len(lighting) < 2:
        raise SystemExit("Pilot needs at least 2 lighting conditions")

    if args.images_dir:
        root = Path(args.images_dir)
        missing_files = [name for name in filenames if not (root / name).is_file()]
        if missing_files:
            raise SystemExit(f"Missing {len(missing_files)} images, first: {missing_files[0]}")

    print(f"Pilot manifest valid: {len(rows)} images, {len(item_ids)} physical items/sessions")
    print("Class counts:", dict(sorted(labels.items())))


if __name__ == "__main__":
    main()
