from __future__ import annotations
from pathlib import Path
from time import perf_counter
import io
import numpy as np
from PIL import Image, ImageColor
from app.utils.config import get_settings
from app.services.embedding_service import embedding_service, EmbeddingUnavailable

settings = get_settings()


class CVUnavailable(RuntimeError):
    pass


class CVService:
    """YOLO segmentation + OpenCLIP verification/few-shot classification."""

    def __init__(self) -> None:
        self._yolo = None

    def _load_yolo(self):
        model_path = Path(settings.cv_model_path)
        if not model_path.exists():
            raise CVUnavailable(
                "No trained segmentation checkpoint is configured. Collect/annotate pilot data and train the model first."
            )
        if self._yolo is None:
            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise CVUnavailable("Install backend/requirements-cv.txt to run CV inference") from exc
            self._yolo = YOLO(str(model_path))
        return self._yolo

    def _resolve_image(self, image_path: str, image_blob: bytes | None = None) -> Path:
        path = Path(image_path)
        absolute = path if path.is_absolute() else settings.storage_path / path
        if absolute.exists():
            return absolute
        if image_blob is None:
            raise CVUnavailable("Stored image content is unavailable")
        absolute.parent.mkdir(parents=True, exist_ok=True)
        absolute.write_bytes(image_blob)
        return absolute

    def _save_overlay(self, image: Image.Image, mask: np.ndarray, image_id: str, idx: int) -> tuple[str, bytes]:
        mask_img = Image.fromarray((mask > 0.5).astype(np.uint8) * 255).resize(image.size)
        tint = Image.new("RGBA", image.size, ImageColor.getrgb("#ff3b30") + (0,))
        tint.putalpha(mask_img.point(lambda p: 105 if p else 0))
        overlay = Image.alpha_composite(image.convert("RGBA"), tint).convert("RGB")

        relative = Path("overlays") / image_id / f"finding-{idx}.jpg"
        absolute = settings.storage_path / relative
        absolute.parent.mkdir(parents=True, exist_ok=True)

        buf = io.BytesIO()
        overlay.save(buf, "JPEG", quality=92)
        payload = buf.getvalue()
        absolute.write_bytes(payload)
        return relative.as_posix(), payload

    def inspect(self, image_path: str, image_id: str, image_blob: bytes | None = None) -> dict:
        started = perf_counter()
        model = self._load_yolo()
        absolute = self._resolve_image(image_path, image_blob)
        image = Image.open(absolute).convert("RGB")
        try:
            verified, similarity = embedding_service.verify_category(image)
        except EmbeddingUnavailable as exc:
            raise CVUnavailable(str(exc)) from exc

        if not verified:
            return {
                "product_verified": False,
                "product_similarity": similarity,
                "findings": [],
                "model_version": settings.cv_model_version,
                "latency_ms": (perf_counter() - started) * 1000,
            }

        result = model.predict(source=str(absolute), verbose=False, conf=0.20)[0]
        findings: list[dict] = []
        if result.masks is not None and result.boxes is not None:
            masks = result.masks.data.cpu().numpy()
            boxes = result.boxes
            for idx, mask in enumerate(masks):
                seg_conf = float(boxes.conf[idx].item()) if boxes.conf is not None else 0.0
                xyxy = boxes.xyxy[idx].cpu().numpy().astype(float).tolist()
                x1, y1, x2, y2 = [max(0, int(x)) for x in xyxy]
                crop = image.crop((x1, y1, max(x1 + 1, x2), max(y1 + 1, y2)))
                try:
                    defect_type, class_score, class_scores = embedding_service.classify_damage(crop)
                except EmbeddingUnavailable as exc:
                    raise CVUnavailable(str(exc)) from exc
                resized = np.asarray(Image.fromarray((mask > 0.5).astype(np.uint8)).resize(image.size))
                affected = float(np.count_nonzero(resized) / resized.size * 100.0)
                overlay_path, overlay_blob = self._save_overlay(image, mask, image_id, idx)
                findings.append({
                    "image_id": image_id,
                    "defect_type": defect_type,
                    "confidence": min(seg_conf, max(0.0, class_score)),
                    "segmentation_confidence": seg_conf,
                    "classification_similarity": class_score,
                    "class_scores": class_scores,
                    "bbox": xyxy,
                    "mask_path": overlay_path,
                    "mask_content_type": "image/jpeg",
                    "mask_blob": overlay_blob,
                    "affected_area_percent": affected,
                })

        return {
            "product_verified": True,
            "product_similarity": similarity,
            "findings": findings,
            "model_version": settings.cv_model_version,
            "latency_ms": (perf_counter() - started) * 1000,
        }


cv_service = CVService()
