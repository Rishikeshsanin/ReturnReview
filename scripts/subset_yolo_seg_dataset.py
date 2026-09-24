"""Create a deterministic, leakage-preserving subset of a canonical YOLO-seg dataset.

Input/output layout:
  images/{train,val,test}
  labels/{train,val,test}

The script never moves examples between source splits. It only selects a seeded
subset inside each existing split and copies the matching image/label pairs.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def paired_examples(root: Path, split: str) -> list[tuple[Path, Path]]:
    image_dir = root / "images" / split
    label_dir = root / "labels" / split
    if not image_dir.is_dir() or not label_dir.is_dir():
        return []
    pairs: list[tuple[Path, Path]] = []
    for image in sorted(p for p in image_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS):
        label = label_dir / f"{image.stem}.txt"
        if label.is_file():
            pairs.append((image, label))
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-train", type=int, default=160)
    parser.add_argument("--max-val", type=int, default=40)
    parser.add_argument("--max-test", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20260924)
    args = parser.parse_args()

    source = Path(args.input).resolve()
    output = Path(args.output).resolve()
    if source == output:
        raise SystemExit("Input and output must differ")
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")

    limits = {"train": args.max_train, "val": args.max_val, "test": args.max_test}
    rng = random.Random(args.seed)
    report: dict[str, object] = {
        "source": str(source),
        "seed": args.seed,
        "limits": limits,
        "splits": {},
    }

    for split, limit in limits.items():
        pairs = paired_examples(source, split)
        if not pairs:
            raise SystemExit(f"No paired examples found for required split: {split}")
        selected = pairs[:]
        rng.shuffle(selected)
        selected = sorted(selected[: min(limit, len(selected))], key=lambda pair: pair[0].name)

        out_images = output / "images" / split
        out_labels = output / "labels" / split
        out_images.mkdir(parents=True, exist_ok=True)
        out_labels.mkdir(parents=True, exist_ok=True)
        for image, label in selected:
            shutil.copy2(image, out_images / image.name)
            shutil.copy2(label, out_labels / label.name)

        report["splits"][split] = {
            "available": len(pairs),
            "selected": len(selected),
        }

    (output / "data.yaml").write_text(
        "\n".join(
            [
                f"path: {output.as_posix()}",
                "train: images/train",
                "val: images/val",
                "test: images/test",
                "names:",
                "  0: damage",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (output / "subset_manifest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
