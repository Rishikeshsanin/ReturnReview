"""Measure combined CPU CV runtime latency and process peak RSS for deployment gating."""
from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

import numpy as np
from PIL import Image


def peak_rss_mb() -> float:
    # Linux ru_maxrss is KiB.
    return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024.0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--prototypes", required=True)
    p.add_argument("--image", required=True)
    p.add_argument("--output", default="artifacts/evaluation/runtime_benchmark.json")
    p.add_argument("--model", default="ViT-B-32")
    p.add_argument("--pretrained", default="laion2b_s34b_b79k")
    p.add_argument("--imgsz", type=int, default=320)
    args = p.parse_args()

    started = time.perf_counter()
    import torch
    import open_clip
    from ultralytics import YOLO

    import_peak = peak_rss_mb()

    yolo_started = time.perf_counter()
    yolo = YOLO(args.checkpoint)
    yolo_load_ms = (time.perf_counter() - yolo_started) * 1000.0
    after_yolo_mb = peak_rss_mb()

    clip_started = time.perf_counter()
    clip_model, _, preprocess = open_clip.create_model_and_transforms(
        args.model, pretrained=args.pretrained
    )
    clip_model.eval()
    clip_load_ms = (time.perf_counter() - clip_started) * 1000.0
    after_clip_mb = peak_rss_mb()

    bank = np.load(args.prototypes, allow_pickle=False)
    prototype_keys = sorted(bank.files)
    image = Image.open(args.image).convert("RGB")

    yolo_infer_started = time.perf_counter()
    result = yolo.predict(source=args.image, verbose=False, conf=0.20, imgsz=args.imgsz, device="cpu")[0]
    yolo_infer_ms = (time.perf_counter() - yolo_infer_started) * 1000.0

    tensor = preprocess(image).unsqueeze(0)
    clip_infer_started = time.perf_counter()
    with torch.no_grad():
        feat = clip_model.encode_image(tensor)
        feat = feat / feat.norm(dim=-1, keepdim=True)
    clip_infer_ms = (time.perf_counter() - clip_infer_started) * 1000.0

    masks = 0 if result.masks is None else int(len(result.masks.data))
    payload = {
        "platform": "github_actions_ubuntu_cpu",
        "checkpoint_bytes": Path(args.checkpoint).stat().st_size,
        "prototype_bytes": Path(args.prototypes).stat().st_size,
        "prototype_keys": prototype_keys,
        "yolo_load_ms": yolo_load_ms,
        "clip_load_ms": clip_load_ms,
        "yolo_single_image_inference_ms": yolo_infer_ms,
        "clip_single_image_inference_ms": clip_infer_ms,
        "predicted_masks": masks,
        "peak_rss_mb_after_imports": import_peak,
        "peak_rss_mb_after_yolo_load": after_yolo_mb,
        "peak_rss_mb_after_clip_load": after_clip_mb,
        "peak_rss_mb_final": peak_rss_mb(),
        "total_process_seconds": time.perf_counter() - started,
        "deployment_note": (
            "Peak RSS is measured on GitHub-hosted Ubuntu CPU and is a pre-production "
            "capacity signal, not a guarantee of identical Railway memory usage."
        ),
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
