"""Build OpenCLIP prototype embeddings from labelled reference-image folders."""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", default="backend/models/prototypes.npz")
    parser.add_argument("--model", default="ViT-B-32")
    parser.add_argument("--pretrained", default="laion2b_s34b_b79k")
    args = parser.parse_args()

    import torch
    import open_clip

    model, _, preprocess = open_clip.create_model_and_transforms(args.model, pretrained=args.pretrained)
    model.eval()
    result = {}

    for folder in sorted(Path(args.root).iterdir()):
        if not folder.is_dir():
            continue
        vectors = []
        for image_path in sorted(folder.iterdir()):
            if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            tensor = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0)
            with torch.no_grad():
                vector = model.encode_image(tensor)
                vector = vector / vector.norm(dim=-1, keepdim=True)
            vectors.append(vector.cpu().numpy()[0])

        if vectors:
            prototype = np.mean(vectors, axis=0)
            prototype = prototype / np.linalg.norm(prototype)
            result[folder.name] = prototype.astype(np.float32)
            print(folder.name, len(vectors))

    if not result:
        raise SystemExit("No reference images found")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, **result)
    print(out)


if __name__ == "__main__":
    main()
