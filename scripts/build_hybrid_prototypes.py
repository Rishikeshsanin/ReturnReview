"""Build a hybrid OpenCLIP prototype bank.

Image-derived prototypes are used when train-only reference folders exist.
Missing locked runtime classes may fall back to explicit text prototypes. The manifest
records which source produced every prototype so image and text prototypes are never
silently conflated.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

IMAGE_EXTS={".jpg",".jpeg",".png",".webp"}
TEXT_FALLBACKS={
    "defect_crushed_corner":[
        "a crushed corner of a corrugated cardboard shipping box",
        "a visibly collapsed corner of a cardboard parcel box",
        "compression damage concentrated at a cardboard box corner",
    ]
}
REQUIRED={
    "category_cardboard_box",
    "defect_tear",
    "defect_crushed_corner",
    "defect_dent_or_crush",
}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--output",default="artifacts/cv/prototypes.npz")
    p.add_argument("--manifest",default="artifacts/cv/prototypes_manifest.json")
    p.add_argument("--model",default="ViT-B-32")
    p.add_argument("--pretrained",default="laion2b_s34b_b79k")
    args=p.parse_args()

    import torch,open_clip

    model,_,preprocess=open_clip.create_model_and_transforms(args.model,pretrained=args.pretrained)
    tokenizer=open_clip.get_tokenizer(args.model)
    model.eval()

    root=Path(args.root)
    bank={}
    sources={}

    with torch.no_grad():
        for folder in sorted(root.iterdir()):
            if not folder.is_dir():
                continue
            vectors=[]
            for image_path in sorted(folder.iterdir()):
                if image_path.suffix.lower() not in IMAGE_EXTS:
                    continue
                tensor=preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0)
                vector=model.encode_image(tensor)
                vector=vector/vector.norm(dim=-1,keepdim=True)
                vectors.append(vector.cpu().numpy()[0])
            if vectors:
                proto=np.mean(vectors,axis=0)
                proto=proto/np.linalg.norm(proto)
                bank[folder.name]=proto.astype(np.float32)
                sources[folder.name]={"kind":"train_image_prototype","samples":len(vectors)}

        for key,prompts in TEXT_FALLBACKS.items():
            if key in bank:
                continue
            tokens=tokenizer(prompts)
            vec=model.encode_text(tokens)
            vec=vec/vec.norm(dim=-1,keepdim=True)
            proto=vec.mean(dim=0)
            proto=proto/proto.norm()
            bank[key]=proto.cpu().numpy().astype(np.float32)
            sources[key]={"kind":"text_fallback","prompts":prompts}

    missing=sorted(REQUIRED-set(bank))
    if missing:
        raise SystemExit("Missing required prototypes: "+", ".join(missing))

    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    np.savez(out,**bank)
    manifest={
        "kind":"hybrid_openclip_prototype_bank",
        "model":args.model,
        "pretrained":args.pretrained,
        "sources":sources,
        "limitations":[
            "crushed_corner is text-derived because the public source has no direct train label.",
            "tear, dent_or_crush, and unknown use train-only image crops.",
            "unknown is represented by the public source leakage class only as an out-of-taxonomy example.",
            "category verification uses train-only full parcel images.",
            "Thresholds are calibrated on validation data and evaluated once on held-out test data."
        ]
    }
    mp=Path(args.manifest); mp.parent.mkdir(parents=True,exist_ok=True)
    mp.write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))


if __name__=="__main__":
    main()
