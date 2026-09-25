"""Benchmark YOLO segmentation + MobileNetV3 category verification in one CPU process."""
from __future__ import annotations

import argparse
import json
import resource
import tempfile
import time
from pathlib import Path

from PIL import Image


def peak_rss_mb() -> float:
    return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024.0


def ensure_image(path: str | None) -> Path:
    if path:
        p=Path(path)
        if not p.is_file():
            raise SystemExit(f"Image not found: {p}")
        return p
    tmp=Path(tempfile.gettempdir())/"returnreview-light-benchmark.jpg"
    Image.new("RGB",(640,480),"white").save(tmp,"JPEG")
    return tmp


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--segmentation",required=True)
    p.add_argument("--category",required=True)
    p.add_argument("--image")
    p.add_argument("--output",required=True)
    p.add_argument("--imgsz",type=int,default=320)
    args=p.parse_args()

    started=time.perf_counter()
    import torch
    from torch import nn
    from torchvision import transforms
    from torchvision.models import mobilenet_v3_small
    from ultralytics import YOLO

    image_path=ensure_image(args.image)
    after_import=peak_rss_mb()

    yolo_started=time.perf_counter()
    yolo=YOLO(args.segmentation)
    yolo_load_ms=(time.perf_counter()-yolo_started)*1000.0
    after_yolo=peak_rss_mb()

    cat_started=time.perf_counter()
    payload=torch.load(args.category,map_location="cpu",weights_only=False)
    category=mobilenet_v3_small(weights=None)
    category.classifier[3]=nn.Linear(category.classifier[3].in_features,2)
    category.load_state_dict(payload["state_dict"])
    category.eval()
    norm=payload["normalization"]
    preprocess=transforms.Compose([
        transforms.Resize((payload.get("image_size",224),payload.get("image_size",224))),
        transforms.ToTensor(),
        transforms.Normalize(mean=norm["mean"],std=norm["std"]),
    ])
    category_load_ms=(time.perf_counter()-cat_started)*1000.0
    after_category=peak_rss_mb()

    cat_in=time.perf_counter()
    tensor=preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        probs=torch.softmax(category(tensor),dim=1)[0]
    cat_ms=(time.perf_counter()-cat_in)*1000.0

    yolo_in=time.perf_counter()
    result=yolo.predict(str(image_path),verbose=False,conf=0.20,imgsz=args.imgsz,device="cpu")[0]
    yolo_ms=(time.perf_counter()-yolo_in)*1000.0

    out_payload={
        "platform":"github_actions_ubuntu_cpu",
        "after_import_peak_rss_mb":after_import,
        "after_yolo_load_peak_rss_mb":after_yolo,
        "after_category_load_peak_rss_mb":after_category,
        "final_peak_rss_mb":peak_rss_mb(),
        "yolo_load_ms":yolo_load_ms,
        "category_load_ms":category_load_ms,
        "category_single_image_inference_ms":cat_ms,
        "yolo_single_image_inference_ms":yolo_ms,
        "combined_single_image_inference_ms":cat_ms+yolo_ms,
        "predicted_masks":0 if result.masks is None else int(len(result.masks.data)),
        "category_probability_cardboard":float(probs[payload["class_to_idx"]["cardboard_box"]].item()),
        "total_seconds":time.perf_counter()-started,
        "railway_fit":{
            "current_limit_mb":1024.0,
            "observed_existing_api_base_mb":92.0,
            "safety_reserve_mb":64.0,
        },
    }
    out_payload["railway_fit"]["estimated_total_mb"]=92.0+out_payload["final_peak_rss_mb"]
    out_payload["railway_fit"]["fits_with_reserve"]=(
        out_payload["railway_fit"]["estimated_total_mb"]+64.0<1024.0
    )
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(out_payload,indent=2)+"\n")
    print(json.dumps(out_payload,indent=2))


if __name__=="__main__":
    main()
