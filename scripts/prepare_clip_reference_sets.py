"""Build leakage-safe OpenCLIP reference-image folders from the source train split.

Only train-split images/crops are used to create prototypes. Validation/test images are
never copied into the reference bank.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path

from PIL import Image
import yaml

IMAGE_EXTS={".jpg",".jpeg",".png",".webp"}
CLASS_MAP={"tear":"tear","squeeze":"dent_or_crush","leakage":"unknown"}


def normalize_names(raw):
    if isinstance(raw,list):
        return {i:str(v) for i,v in enumerate(raw)}
    if isinstance(raw,dict):
        return {int(k):str(v) for k,v in raw.items()}
    raise SystemExit("data.yaml must define names")


def train_dirs(root:Path):
    images=root/"train"/"images"
    labels=root/"train"/"labels"
    if not images.is_dir() or not labels.is_dir():
        raise SystemExit("Source train/images + train/labels are required")
    return images,labels


def bounds(tokens,width,height):
    coords=[float(v) for v in tokens]
    if len(coords)<6 or len(coords)%2:
        raise ValueError("invalid polygon")
    xs=coords[0::2]; ys=coords[1::2]
    x1,x2=min(xs)*width,max(xs)*width
    y1,y2=min(ys)*height,max(ys)*height
    px=max(6,(x2-x1)*0.18); py=max(6,(y2-y1)*0.18)
    return max(0,int(x1-px)),max(0,int(y1-py)),min(width,int(x2+px)),min(height,int(y2+py))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--category-count",type=int,default=48)
    p.add_argument("--defect-count",type=int,default=48)
    p.add_argument("--seed",type=int,default=20260924)
    args=p.parse_args()

    src=Path(args.source).resolve()
    out=Path(args.output).resolve()
    if out.exists():
        raise SystemExit(f"Refusing to overwrite {out}")
    names=normalize_names((yaml.safe_load((src/"data.yaml").read_text()) or {}).get("names"))
    images_dir,labels_dir=train_dirs(src)
    rng=random.Random(args.seed)

    images=sorted(p for p in images_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    rng.shuffle(images)
    category=sorted(images[:min(args.category_count,len(images))],key=lambda p:p.name)
    cat_dir=out/"category_cardboard_box"
    cat_dir.mkdir(parents=True)
    for image in category:
        shutil.copy2(image,cat_dir/image.name)

    candidates={v:[] for v in CLASS_MAP.values()}
    for image_path in sorted(images_dir.iterdir()):
        if image_path.suffix.lower() not in IMAGE_EXTS:
            continue
        label_path=labels_dir/f"{image_path.stem}.txt"
        if not label_path.is_file():
            continue
        with Image.open(image_path) as img:
            w,h=img.size
        for line_idx,raw in enumerate(label_path.read_text().splitlines()):
            parts=raw.strip().split()
            if len(parts)<7:
                continue
            cls=names.get(int(float(parts[0])))
            target=CLASS_MAP.get(cls or "")
            if not target:
                continue
            try:
                box=bounds(parts[1:],w,h)
            except ValueError:
                continue
            candidates[target].append((image_path,line_idx,box))

    counts={}
    for label,rows in candidates.items():
        rng.shuffle(rows)
        rows=rows[:args.defect_count]
        target=out/f"defect_{label}"
        target.mkdir(parents=True)
        for idx,(image_path,line_idx,box) in enumerate(rows):
            with Image.open(image_path) as img:
                crop=img.convert("RGB").crop(box)
                crop.save(target/f"{image_path.stem}_{line_idx:02d}_{idx:03d}.jpg",quality=94)
        counts[label]=len(rows)

    manifest={
        "source":str(src),
        "split":"train_only",
        "category_reference_images":len(category),
        "defect_reference_crops":counts,
        "notes":[
            "Only source train split contributes prototype references.",
            "tear maps directly to tear.",
            "squeeze is explicitly treated as a compression-damage proxy for dent_or_crush.",
            "leakage supplies a train-only out-of-taxonomy prototype for the runtime unknown class.",
            "No crushed_corner source examples are invented."
        ]
    }
    (out/"reference_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))


if __name__=="__main__":
    main()
