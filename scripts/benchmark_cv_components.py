"""Measure individual CV component CPU memory/latency in isolated processes.

Each invocation loads exactly one heavy model so its peak RSS can be compared
against Railway service limits without the combined-model distortion.
"""
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
        p = Path(path)
        if not p.is_file():
            raise SystemExit(f"Image not found: {p}")
        return p
    tmp = Path(tempfile.gettempdir()) / "returnreview-benchmark.jpg"
    Image.new("RGB", (640, 480), "white").save(tmp, "JPEG", quality=90)
    return tmp


def benchmark_yolo(checkpoint: str, image_path: Path, imgsz: int) -> dict:
    started = time.perf_counter()
    from ultralytics import YOLO

    after_import_mb = peak_rss_mb()
    load_started = time.perf_counter()
    model = YOLO(checkpoint)
    load_ms = (time.perf_counter() - load_started) * 1000.0
    after_load_mb = peak_rss_mb()

    infer_started = time.perf_counter()
    result = model.predict(
        source=str(image_path),
        verbose=False,
        conf=0.20,
        imgsz=imgsz,
        device="cpu",
    )[0]
    infer_ms = (time.perf_counter() - infer_started) * 1000.0
    masks = 0 if result.masks is None else int(len(result.masks.data))
    return {
        "component": "yolo",
        "after_import_peak_rss_mb": after_import_mb,
        "after_load_peak_rss_mb": after_load_mb,
        "final_peak_rss_mb": peak_rss_mb(),
        "load_ms": load_ms,
        "single_image_inference_ms": infer_ms,
        "predicted_masks": masks,
        "total_seconds": time.perf_counter() - started,
    }


def benchmark_openclip(model_name: str, pretrained: str, image_path: Path) -> dict:
    started = time.perf_counter()
    import torch
    import open_clip

    after_import_mb = peak_rss_mb()
    load_started = time.perf_counter()
    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name, pretrained=pretrained
    )
    model.eval()
    load_ms = (time.perf_counter() - load_started) * 1000.0
    after_load_mb = peak_rss_mb()

    tensor = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0)
    infer_started = time.perf_counter()
    with torch.no_grad():
        feature = model.encode_image(tensor)
        feature = feature / feature.norm(dim=-1, keepdim=True)
    infer_ms = (time.perf_counter() - infer_started) * 1000.0
    return {
        "component": "openclip",
        "model": model_name,
        "pretrained": pretrained,
        "embedding_dimensions": int(feature.shape[-1]),
        "after_import_peak_rss_mb": after_import_mb,
        "after_load_peak_rss_mb": after_load_mb,
        "final_peak_rss_mb": peak_rss_mb(),
        "load_ms": load_ms,
        "single_image_inference_ms": infer_ms,
        "total_seconds": time.perf_counter() - started,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--component", choices=("yolo", "openclip"), required=True)
    parser.add_argument("--checkpoint")
    parser.add_argument("--image")
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--clip-model", default="ViT-B-32")
    parser.add_argument("--clip-pretrained", default="laion2b_s34b_b79k")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    image_path = ensure_image(args.image)
    if args.component == "yolo":
        if not args.checkpoint:
            raise SystemExit("--checkpoint is required for yolo")
        result = benchmark_yolo(args.checkpoint, image_path, args.imgsz)
    else:
        result = benchmark_openclip(
            args.clip_model, args.clip_pretrained, image_path
        )

    result["platform"] = "github_actions_ubuntu_cpu"
    result["note"] = (
        "Peak RSS is measured in an isolated process. It is a deployment-capacity "
        "signal, not a guarantee of identical Railway memory use."
    )
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
