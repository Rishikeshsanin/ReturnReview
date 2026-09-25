"""Prepare a multiclass YOLO segmentation dataset for the production-light CV path.

The source export already contains genuine polygons. This script only remaps class
IDs; it never synthesizes masks from boxes.

Runtime mapping:
- tear -> tear
- squeeze -> dent_or_crush or crushed_corner (geometry heuristic at inference)
- leakage -> unknown
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import yaml

IMAGE_EXTS={".jpg",".jpeg",".png",".webp"}
TARGETS={"tear":0,"squeeze":1,"leakage":2}
TARGET_NAMES={0:"tear",1:"squeeze",2:"leakage"}


def normalize_names(raw):
    if isinstance(raw,list):
        return {i:str(v) for i,v in enumerate(raw)}
    if isinstance(raw,dict):
        return {int(k):str(v) for k,v in raw.items()}
    raise SystemExit("data.yaml must define names")


def resolve_split(root:Path,canonical:str):
    names=[canonical]
    if canonical=="val":
        names+=["valid","validation"]
    for name in names:
        images=root/name/"images"; labels=root/name/"labels"
        if images.is_dir() and labels.is_dir():
            return images,labels
    return None


def parse_polygon(line:str,label_path:Path):
    parts=line.strip().split()
    if len(parts)<7 or (len(parts)-1)%2:
        raise SystemExit(f"{label_path}: non-polygon annotation detected")
    class_id=int(float(parts[0]))
    coords=[float(v) for v in parts[1:]]
    if any(v<0.0 or v>1.0 for v in coords):
        raise SystemExit(f"{label_path}: polygon coordinate outside [0,1]")
    return class_id,parts[1:]


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--source-id",required=True)
    p.add_argument("--source-url",required=True)
    p.add_argument("--license",required=True)
    args=p.parse_args()

    src=Path(args.input).resolve(); out=Path(args.output).resolve()
    if out.exists():
        raise SystemExit(f"Refusing to overwrite {out}")
    cfg=yaml.safe_load((src/"data.yaml").read_text()) or {}
    source_names=normalize_names(cfg.get("names"))
    source_to_target={
        sid:TARGETS[name]
        for sid,name in source_names.items()
        if name in TARGETS
    }
    if set(TARGETS)-set(source_names.values()):
        raise SystemExit("Source export is missing one or more required classes")

    totals={"images_seen":0,"images_written":0,"polygons_written":0}
    split_counts={}
    class_polygons={name:0 for name in TARGETS}

    for split in ("train","val","test"):
        located=resolve_split(src,split)
        if not located:
            continue
        images_dir,labels_dir=located
        oi=out/"images"/split; ol=out/"labels"/split
        oi.mkdir(parents=True); ol.mkdir(parents=True)
        counts={"images":0,"polygons":0}
        for image_path in sorted(p for p in images_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS):
            totals["images_seen"]+=1
            label_path=labels_dir/f"{image_path.stem}.txt"
            if not label_path.is_file():
                continue
            accepted=[]
            for raw in label_path.read_text().splitlines():
                if not raw.strip():
                    continue
                sid,coords=parse_polygon(raw,label_path)
                if sid not in source_to_target:
                    continue
                tid=source_to_target[sid]
                accepted.append(f"{tid} "+" ".join(coords))
                class_polygons[TARGET_NAMES[tid]]+=1
            if not accepted:
                continue
            shutil.copy2(image_path,oi/image_path.name)
            (ol/f"{image_path.stem}.txt").write_text("\n".join(accepted)+"\n")
            counts["images"]+=1; counts["polygons"]+=len(accepted)
            totals["images_written"]+=1; totals["polygons_written"]+=len(accepted)
        split_counts[split]=counts

    if not totals["images_written"]:
        shutil.rmtree(out)
        raise SystemExit("No accepted polygon annotations found")

    yaml_lines=[
        f"path: {out.as_posix()}",
        "train: images/train",
        "val: images/val",
        "test: images/test",
        "names:",
        "  0: tear",
        "  1: squeeze",
        "  2: leakage",
    ]
    (out/"data.yaml").write_text("\n".join(yaml_lines)+"\n")
    manifest={
        "source_id":args.source_id,
        "source_url":args.source_url,
        "license":args.license,
        "conversion":"polygon_class_remap_only",
        "target_classes":TARGET_NAMES,
        "runtime_mapping":{
            "tear":"tear",
            "squeeze":"dent_or_crush_or_crushed_corner_by_geometry",
            "leakage":"unknown",
        },
        "split_counts":split_counts,
        "class_polygons":class_polygons,
        "totals":totals,
    }
    (out/"returnreview_multiclass_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))


if __name__=="__main__":
    main()
