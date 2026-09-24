"""Build an auditable OpenCLIP semantic prototype bank from text prompts.

This is used when project-controlled subtype reference photos are not yet
available. It does not pretend text prototypes are few-shot image prototypes.
The generated NPZ uses the same keys expected by the runtime matcher.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

PROMPTS = {
    "category_cardboard_box": [
        "a photo of a corrugated cardboard shipping box",
        "a cardboard parcel box",
        "a brown corrugated packaging box",
    ],
    "defect_tear": [
        "a visible tear in corrugated cardboard",
        "torn cardboard on a shipping box",
        "a ripped area of a cardboard package",
    ],
    "defect_crushed_corner": [
        "a crushed corner of a cardboard shipping box",
        "a smashed corner on a corrugated cardboard box",
        "a visibly collapsed cardboard box corner",
    ],
    "defect_dent_or_crush": [
        "a dented side panel of a cardboard shipping box",
        "a crushed side of a corrugated cardboard box",
        "compression damage on a cardboard parcel",
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/cv/prototypes.npz")
    parser.add_argument("--manifest", default="artifacts/cv/prototypes_manifest.json")
    parser.add_argument("--model", default="ViT-B-32")
    parser.add_argument("--pretrained", default="laion2b_s34b_b79k")
    args = parser.parse_args()

    import torch
    import open_clip

    model, _, _ = open_clip.create_model_and_transforms(
        args.model, pretrained=args.pretrained
    )
    tokenizer = open_clip.get_tokenizer(args.model)
    model.eval()

    bank: dict[str, np.ndarray] = {}
    with torch.no_grad():
        for key, prompts in PROMPTS.items():
            tokens = tokenizer(prompts)
            vectors = model.encode_text(tokens)
            vectors = vectors / vectors.norm(dim=-1, keepdim=True)
            prototype = vectors.mean(dim=0)
            prototype = prototype / prototype.norm()
            bank[key] = prototype.cpu().numpy().astype(np.float32)
            print(f"{key}: {len(prompts)} prompts")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, **bank)

    manifest = {
        "kind": "openclip_text_semantic_prototypes",
        "model": args.model,
        "pretrained": args.pretrained,
        "keys": sorted(bank),
        "prompts": PROMPTS,
        "limitations": [
            "These are text-derived semantic prototypes, not project-controlled few-shot image prototypes.",
            "Thresholds must be calibrated on validation data before production use.",
            "Subtype performance must be reported only for classes represented in held-out evaluation data.",
        ],
    }
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(out)
    print(manifest_path)


if __name__ == "__main__":
    main()
