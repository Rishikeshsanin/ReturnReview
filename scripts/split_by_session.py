"""Create leakage-safe train/validation/test manifests grouped by physical box/session.

This script never splits images belonging to the same group_id across partitions.
It reads the JSON report produced by audit_pilot_images.py and writes a split manifest.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def allocate_groups(group_ids: list[str], seed: int) -> dict[str, str]:
    ids = sorted(group_ids)
    rng = random.Random(seed)
    rng.shuffle(ids)
    n = len(ids)
    if n < 3:
        raise ValueError("At least 3 physical/session groups are required for train/validation/test splitting")

    n_test = max(1, round(n * 0.15))
    n_val = max(1, round(n * 0.15))
    if n_test + n_val >= n:
        n_test = 1
        n_val = 1
    test = set(ids[:n_test])
    val = set(ids[n_test:n_test + n_val])

    return {
        group_id: ("test" if group_id in test else "val" if group_id in val else "train")
        for group_id in ids
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", required=True, help="pilot_audit.json")
    parser.add_argument("--output", default="artifacts/dataset_split.json")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    report = json.loads(Path(args.audit).read_text(encoding="utf-8"))
    usable = [
        row for row in report["images"]
        if row.get("metadata") is not None
    ]
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in usable:
        groups[row["metadata"]["group_id"]].append(row)

    assignment = allocate_groups(list(groups), args.seed)
    rows = []
    for group_id, images in sorted(groups.items()):
        split = assignment[group_id]
        for image in images:
            rows.append({
                "file": image["file"],
                "path": image["path"],
                "group_id": group_id,
                "label": image["metadata"]["label"],
                "view": image["metadata"]["view"],
                "split": split,
            })

    split_counts = {
        split: sum(row["split"] == split for row in rows)
        for split in ("train", "val", "test")
    }
    group_split_counts = {
        split: sum(value == split for value in assignment.values())
        for split in ("train", "val", "test")
    }

    # Defensive assertion against identity/session leakage.
    seen: dict[str, str] = {}
    for row in rows:
        existing = seen.setdefault(row["group_id"], row["split"])
        if existing != row["split"]:
            raise RuntimeError(f"Leakage detected for {row['group_id']}")

    payload = {
        "seed": args.seed,
        "strategy": "grouped_by_physical_box_and_capture_session",
        "image_counts": split_counts,
        "group_counts": group_split_counts,
        "group_assignment": assignment,
        "images": rows,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(out)
    print("Image counts:", split_counts)
    print("Group counts:", group_split_counts)


if __name__ == "__main__":
    main()
