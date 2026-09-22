from __future__ import annotations
from pathlib import Path
import numpy as np
from PIL import Image
from app.utils.config import get_settings

settings = get_settings()


class EmbeddingUnavailable(RuntimeError):
    pass


class EmbeddingService:
    """OpenCLIP-backed prototype matching for category verification and few-shot defect labels."""

    def __init__(self) -> None:
        self._model = None
        self._preprocess = None
        self._torch = None
        self._bank: dict[str, np.ndarray] | None = None

    def _load_model(self):
        if self._model is not None:
            return
        try:
            import torch
            import open_clip
        except ImportError as exc:
            raise EmbeddingUnavailable("Install backend/requirements-cv.txt to use OpenCLIP") from exc
        model, _, preprocess = open_clip.create_model_and_transforms(
            settings.clip_model,
            pretrained=settings.clip_pretrained,
        )
        model.eval()
        self._model = model
        self._preprocess = preprocess
        self._torch = torch

    def _load_bank(self) -> dict[str, np.ndarray]:
        if self._bank is not None:
            return self._bank
        path = Path(settings.prototype_bank_path)
        if not path.exists():
            raise EmbeddingUnavailable(
                "Prototype bank is missing. Build it from labelled reference images before real verification/few-shot inference."
            )
        payload = np.load(path, allow_pickle=False)
        self._bank = {key: payload[key].astype(np.float32) for key in payload.files}
        return self._bank

    def embed(self, image: Image.Image) -> np.ndarray:
        self._load_model()
        tensor = self._preprocess(image.convert("RGB")).unsqueeze(0)
        with self._torch.no_grad():
            feat = self._model.encode_image(tensor)
            feat = feat / feat.norm(dim=-1, keepdim=True)
        return feat.cpu().numpy()[0].astype(np.float32)

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
        return float(np.dot(a, b) / denom) if denom else 0.0

    def verify_category(self, image: Image.Image) -> tuple[bool, float]:
        bank = self._load_bank()
        key = "category_cardboard_box"
        if key not in bank:
            raise EmbeddingUnavailable(f"Prototype '{key}' is missing")
        score = self._cosine(self.embed(image), bank[key])
        return score >= settings.category_similarity_threshold, score

    def classify_damage(self, crop: Image.Image) -> tuple[str, float, dict[str, float]]:
        bank = self._load_bank()
        emb = self.embed(crop)
        scores = {
            name.removeprefix("defect_"): self._cosine(emb, proto)
            for name, proto in bank.items()
            if name.startswith("defect_")
        }
        if not scores:
            raise EmbeddingUnavailable("No defect prototypes exist in the prototype bank")
        ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        label, score = ordered[0]
        margin = score - ordered[1][1] if len(ordered) > 1 else score
        if score < settings.defect_similarity_threshold or margin < settings.defect_margin_threshold:
            return "unknown", score, scores
        return label, score, scores


embedding_service = EmbeddingService()
