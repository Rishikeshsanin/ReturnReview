"""Package lightweight production CV artifacts and their truthful metrics."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime,timezone
from pathlib import Path


def sha256(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def require(path:Path,label:str):
    if not path.is_file() or path.stat().st_size==0:
        raise SystemExit(f"{label} missing or empty: {path}")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--segmentation",required=True)
    p.add_argument("--category",required=True)
    p.add_argument("--segmentation-metrics",required=True)
    p.add_argument("--category-metrics",required=True)
    p.add_argument("--runtime-benchmark",required=True)
    p.add_argument("--model-version",required=True)
    p.add_argument("--output-dir",required=True)
    args=p.parse_args()

    seg=Path(args.segmentation).resolve()
    cat=Path(args.category).resolve()
    seg_metrics=Path(args.segmentation_metrics).resolve()
    cat_metrics=Path(args.category_metrics).resolve()
    runtime=Path(args.runtime_benchmark).resolve()
    for path,label in [
        (seg,"segmentation checkpoint"),(cat,"category checkpoint"),
        (seg_metrics,"segmentation metrics"),(cat_metrics,"category metrics"),
        (runtime,"runtime benchmark")
    ]:
        require(path,label)

    out=Path(args.output_dir).resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty {out}")
    out.mkdir(parents=True,exist_ok=True)
    files={
        "segmentation_checkpoint":(seg,"best.pt"),
        "category_checkpoint":(cat,"category_mobilenet_v3_small.pt"),
        "segmentation_metrics":(seg_metrics,"segmentation_metrics.json"),
        "category_metrics":(cat_metrics,"category_metrics.json"),
        "runtime_benchmark":(runtime,"runtime_benchmark.json"),
    }
    artifacts={}
    for key,(src,name) in files.items():
        dst=out/name
        shutil.copy2(src,dst)
        artifacts[key]={"filename":name,"sha256":sha256(dst),"bytes":dst.stat().st_size}

    manifest={
        "schema_version":1,
        "created_at":datetime.now(timezone.utc).isoformat(),
        "model_version":args.model_version,
        "runtime":{
            "category_verification":"mobilenet_v3_small_binary_classifier",
            "damage_segmentation":"yolo11n_seg_multiclass",
            "defect_mapping":{
                "tear":"tear",
                "squeeze":"dent_or_crush_or_crushed_corner_by_geometry",
                "leakage":"unknown",
            },
            "openclip_required_in_production":False,
        },
        "artifacts":artifacts,
        "claims":{
            "public_pilot":True,
            "project_controlled_dataset":False,
            "crushed_corner_direct_training_label":False,
        },
    }
    (out/"release_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))


if __name__=="__main__":
    main()
