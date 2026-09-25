"""Evaluate multiclass YOLO segmentation on the held-out test split."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ultralytics import YOLO


def to_list(value):
    try:
        return [float(x) for x in value]
    except Exception:
        return []


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",required=True)
    p.add_argument("--data",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()

    model=YOLO(args.model)
    metrics=model.val(data=args.data,split="test",verbose=False)
    names=getattr(metrics,"names",{}) or {}
    maps=to_list(getattr(metrics.seg,"maps",[]))
    per_class={}
    for idx,score in enumerate(maps):
        name=names.get(idx,str(idx)) if isinstance(names,dict) else str(idx)
        per_class[str(name)]={"mask_map50_95":score}

    payload={
        "segmentation":{
            "mask_map50":float(metrics.seg.map50),
            "mask_map50_95":float(metrics.seg.map),
            "box_map50":float(metrics.box.map50),
            "per_class":per_class,
        },
        "runtime_mapping":{
            "tear":"tear",
            "squeeze":"dent_or_crush_or_crushed_corner_by_geometry",
            "leakage":"unknown",
        },
        "note":"Generated directly from the held-out public-source test split.",
    }
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps(payload,indent=2))


if __name__=="__main__":
    main()
