from pathlib import Path
from uuid import uuid4
import io
import cv2
import numpy as np
from PIL import Image, ImageOps
from fastapi import UploadFile, HTTPException
from app.utils.config import get_settings

settings = get_settings()
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _blur_score(rgb: np.ndarray) -> float:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


async def validate_and_store(case_id: str, upload: UploadFile) -> dict:
    if upload.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Only JPEG, PNG and WebP images are supported")
    raw = await upload.read()
    if len(raw) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Image exceeds {settings.max_upload_mb} MB")
    try:
        image = Image.open(io.BytesIO(raw))
        image.verify()
        image = Image.open(io.BytesIO(raw))
        image = ImageOps.exif_transpose(image).convert("RGB")
    except Exception as exc:
        raise HTTPException(422, "Corrupted or unreadable image") from exc

    width, height = image.size
    if min(width, height) < 256:
        raise HTTPException(422, "Image resolution is too small; use at least 256 px on the shortest side")

    arr = np.asarray(image)
    blur = _blur_score(arr)
    warning = None
    if blur < 70:
        warning = "Image may be blurry; inspection confidence may be reduced."

    target = settings.storage_path / "cases" / case_id
    target.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4()}.jpg"
    path = target / filename

    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=94)
    normalized = buf.getvalue()
    path.write_bytes(normalized)

    relative = path.relative_to(settings.storage_path).as_posix()
    return {
        "path": relative,
        "content_type": "image/jpeg",
        "blob": normalized,
        "width": width,
        "height": height,
        "quality_score": min(1.0, blur / 300.0),
        "quality_warning": warning,
    }
