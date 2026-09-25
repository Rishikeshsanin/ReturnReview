from __future__ import annotations
from pathlib import Path
from time import perf_counter
import io
import numpy as np
from PIL import Image, ImageColor
from app.utils.config import get_settings
from app.services.category_verifier import category_verifier, CategoryVerifierUnavailable

settings = get_settings()


class CVUnavailable(RuntimeError):
    pass


class CVService:
    """Lightweight production CV: MobileNet category verification + multiclass YOLO segmentation."""

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

    @staticmethod
    def _map_defect_type(
        source_class: str,
        bbox: list[float],
        width: int,
        height: int,
    ) -> str:
        if source_class == "tear":
            return "tear"
        if source_class == "leakage":
            return "unknown"
        if source_class != "squeeze":
            return "unknown"

        x1, y1, x2, y2 = bbox
        cx = ((x1 + x2) / 2.0) / max(width, 1)
        cy = ((y1 + y2) / 2.0) / max(height, 1)
        nearest_corner_distance = min(
            ((cx - corner_x) ** 2 + (cy - corner_y) ** 2) ** 0.5
            for corner_x, corner_y in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0))
        )
        return "crushed_corner" if nearest_corner_distance <= 0.32 else "dent_or_crush"

    def inspect(self, image_path: str, image_id: str, image_blob: bytes | None = None) -> dict:
        started = perf_counter()
        model = self._load_yolo()
        absolute = self._resolve_image(image_path, image_blob)
        image = Image.open(absolute).convert("RGB")
        try:
            verified, probability = category_verifier.verify(image)
        except CategoryVerifierUnavailable as exc:
            raise CVUnavailable(str(exc)) from exc

        if not verified:
            return {
                "product_verified": False,
                "product_similarity": probability,
                "findings": [],
                "model_version": settings.cv_model_version,
                "latency_ms": (perf_counter() - started) * 1000,
            }

        result = model.predict(
            source=str(absolute),
            verbose=False,
            conf=0.20,
            imgsz=settings.cv_image_size,
            device="cpu",
        )[0]
        findings: list[dict] = []
        if result.masks is not None and result.boxes is not None:
            masks = result.masks.data.cpu().numpy()
            boxes = result.boxes
            for idx, mask in enumerate(masks):
                seg_conf = float(boxes.conf[idx].item()) if boxes.conf is not None else 0.0
                xyxy = boxes.xyxy[idx].cpu().numpy().astype(float).tolist()
                x1, y1, x2, y2 = [max(0, int(x)) for x in xyxy]
                class_id = int(boxes.cls[idx].item()) if boxes.cls is not None else -1
                class_name = str(result.names.get(class_id, "unknown"))
                defect_type = self._map_defect_type(
                    class_name,
                    xyxy,
                    image.width,
                    image.height,
                )
                resized = np.asarray(Image.fromarray((mask > 0.5).astype(np.uint8)).resize(image.size))
                affected = float(np.count_nonzero(resized) / resized.size * 100.0)
                overlay_path, overlay_blob = self._save_overlay(image, mask, image_id, idx)
                findings.append({
                    "image_id": image_id,
                    "defect_type": defect_type,
                    "confidence": max(0.0, min(1.0, seg_conf)),
                    "segmentation_confidence": seg_conf,
                    "source_class": class_name,
                    "bbox": xyxy,
                    "mask_path": overlay_path,
                    "mask_content_type": "image/jpeg",
                    "mask_blob": overlay_blob,
                    "affected_area_percent": affected,
                })

        return {
            "product_verified": True,
            "product_similarity": probability,
            "findings": findings,
            "model_version": settings.cv_model_version,
            "latency_ms": (perf_counter() - started) * 1000,
        }


cv_service = CVService()
