"""Verify the lightweight CV release files against the release manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True)
    p.add_argument("--segmentation",required=True)
    p.add_argument("--category",required=True)
    args=p.parse_args()

    manifest=json.loads(Path(args.manifest).read_text())
    expected=manifest["artifacts"]
    checks={
        "segmentation_checkpoint":Path(args.segmentation),
        "category_checkpoint":Path(args.category),
    }
    for key,path in checks.items():
        if not path.is_file():
            raise SystemExit(f"Missing {key}: {path}")
        actual=sha256(path)
        wanted=expected[key]["sha256"]
        if actual!=wanted:
            raise SystemExit(f"Checksum mismatch for {key}")
        print(f"{key}: verified {actual}")


if __name__=="__main__":
    main()
