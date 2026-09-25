"""Assemble truthful metrics for the lightweight production CV candidate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text())


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pixel",required=True)
    p.add_argument("--multiclass",required=True)
    p.add_argument("--category",required=True)
    p.add_argument("--runtime",required=True)
    p.add_argument("--dataset-manifest",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()

    pixel=read(args.pixel)
    multi=read(args.multiclass)
    category=read(args.category)
    runtime=read(args.runtime)
    dataset=read(args.dataset_manifest)

    payload={
        "status":"evaluated_public_pilot",
        "scope":"lightweight_production_candidate_public_data",
        "segmentation":{
            **pixel["segmentation"],
            **multi["segmentation"],
        },
        "product_verification":category["product_verification"],
        "runtime":runtime,
        "dataset":{
            "source_id":dataset["source_id"],
            "source_url":dataset["source_url"],
            "license":dataset["license"],
            "split_counts":dataset["split_counts"],
            "class_polygons":dataset["class_polygons"],
        },
        "limitations":[
            "This remains a licensed public-data pilot, not the project-controlled capture.",
            "Source squeeze maps to compression damage and is separated into dent_or_crush vs crushed_corner with a geometry heuristic at runtime.",
            "The public source does not provide a direct crushed_corner training label.",
            "Source leakage is treated as out-of-taxonomy unknown.",
            "Generic COCO images are used as non-box category negatives.",
        ],
    }
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps({
        "segmentation":payload["segmentation"],
        "product_verification":payload["product_verification"],
        "runtime_fit":payload["runtime"].get("railway_fit"),
    },indent=2))


if __name__=="__main__":
    main()
