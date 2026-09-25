"""Create a leakage-safe binary category dataset for MobileNetV3.

Positives are cardboard/parcel images from the Roboflow source split.
Negatives are generic COCO images split deterministically into train/val/test.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path

IMAGE_EXTS={".jpg",".jpeg",".png",".webp"}


def source_images(root:Path,canonical:str):
    names=[canonical]
    if canonical=="val":
        names+=["valid","validation"]
    for name in names:
        d=root/name/"images"
        if d.is_dir():
            return sorted(p for p in d.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    raise SystemExit(f"Missing positive split: {canonical}")


def generic_images(root:Path):
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS)


def copy_selected(rows,target:Path,prefix:str):
    target.mkdir(parents=True,exist_ok=True)
    for i,p in enumerate(rows):
        shutil.copy2(p,target/f"{prefix}_{i:04d}{p.suffix.lower()}")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--positive-source",required=True)
    p.add_argument("--negative-source",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--train-per-class",type=int,default=96)
    p.add_argument("--val-per-class",type=int,default=16)
    p.add_argument("--test-per-class",type=int,default=16)
    p.add_argument("--seed",type=int,default=20260925)
    args=p.parse_args()

    out=Path(args.output).resolve()
    if out.exists():
        raise SystemExit(f"Refusing to overwrite {out}")
    rng=random.Random(args.seed)

    pos={}
    for split in ("train","val","test"):
        rows=source_images(Path(args.positive_source).resolve(),split)
        rng.shuffle(rows)
        limit={"train":args.train_per_class,"val":args.val_per_class,"test":args.test_per_class}[split]
        pos[split]=rows[:min(limit,len(rows))]

    neg=generic_images(Path(args.negative_source).resolve())
    needed=args.train_per_class+args.val_per_class+args.test_per_class
    if len(neg)<needed:
        raise SystemExit(f"Need {needed} unique negatives, found {len(neg)}")
    rng.shuffle(neg)
    neg_split={
        "train":neg[:args.train_per_class],
        "val":neg[args.train_per_class:args.train_per_class+args.val_per_class],
        "test":neg[args.train_per_class+args.val_per_class:needed],
    }

    report={"seed":args.seed,"splits":{}}
    for split in ("train","val","test"):
        copy_selected(pos[split],out/split/"cardboard_box","box")
        copy_selected(neg_split[split],out/split/"not_cardboard_box","neg")
        report["splits"][split]={
            "cardboard_box":len(pos[split]),
            "not_cardboard_box":len(neg_split[split]),
        }

    (out/"dataset_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
