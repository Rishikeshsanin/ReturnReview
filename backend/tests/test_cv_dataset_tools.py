from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.prepare_public_segmentation import main as convert_main
from scripts.subset_yolo_seg_dataset import main as subset_main
from scripts.validate_yolo_seg_dataset import validate


def _write_source_split(root: Path, split: str) -> None:
    images = root / split / "images"
    labels = root / split / "labels"
    images.mkdir(parents=True)
    labels.mkdir(parents=True)
    Image.new("RGB", (32, 32), "white").save(images / f"{split}.jpg")
    # Genuine polygon: class 0 + four x/y points.
    (labels / f"{split}.txt").write_text(
        "0 0.10 0.10 0.90 0.10 0.90 0.90 0.10 0.90\n",
        encoding="utf-8",
    )


def test_public_converter_emits_validator_compatible_layout(tmp_path, monkeypatch):
    source = tmp_path / "raw"
    for split in ("train", "valid", "test"):
        _write_source_split(source, split)
    (source / "data.yaml").write_text("names:\n  0: tear\n", encoding="utf-8")
    output = tmp_path / "converted"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prepare_public_segmentation.py",
            "--input", str(source),
            "--output", str(output),
            "--include-classes", "tear",
            "--source-id", "test-source",
            "--source-url", "https://example.invalid/test",
            "--license", "CC BY 4.0",
        ],
    )
    convert_main()

    assert (output / "images" / "train" / "train.jpg").is_file()
    assert (output / "images" / "val" / "valid.jpg").is_file()
    assert (output / "labels" / "test" / "test.txt").is_file()
    report = validate(output)
    assert report["status"] == "valid"


def test_subset_preserves_source_splits_and_is_valid(tmp_path, monkeypatch):
    source = tmp_path / "canonical"
    for split in ("train", "val", "test"):
        images = source / "images" / split
        labels = source / "labels" / split
        images.mkdir(parents=True)
        labels.mkdir(parents=True)
        for idx in range(3):
            Image.new("RGB", (32, 32), "white").save(images / f"{split}_{idx}.jpg")
            (labels / f"{split}_{idx}.txt").write_text(
                "0 0.10 0.10 0.90 0.10 0.90 0.90 0.10 0.90\n",
                encoding="utf-8",
            )

    output = tmp_path / "subset"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "subset_yolo_seg_dataset.py",
            "--input", str(source),
            "--output", str(output),
            "--max-train", "2",
            "--max-val", "2",
            "--max-test", "2",
            "--seed", "7",
        ],
    )
    subset_main()

    report = validate(output)
    assert report["status"] == "valid"
    assert report["split_counts"]["train"]["images"] == 2
    assert report["split_counts"]["val"]["images"] == 2
    assert report["split_counts"]["test"]["images"] == 2
