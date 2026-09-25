from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.utils.config import get_settings

settings = get_settings()


class CategoryVerifierUnavailable(RuntimeError):
    pass


class CategoryVerifier:
    """Lazy MobileNetV3-Small category verifier for the lightweight CV runtime."""

    def __init__(self) -> None:
        self._model = None
        self._transform = None
        self._torch = None
        self._payload = None

    def _load(self) -> None:
        if self._model is not None:
            return
        path = Path(settings.category_model_path)
        if not path.is_file():
            raise CategoryVerifierUnavailable(
                "Category-verification checkpoint is missing."
            )
        try:
            import torch
            from torch import nn
            from torchvision import transforms
            from torchvision.models import mobilenet_v3_small
        except ImportError as exc:
            raise CategoryVerifierUnavailable(
                "Install backend/requirements-cv.txt to run category verification"
            ) from exc

        payload = torch.load(path, map_location="cpu", weights_only=False)
        model = mobilenet_v3_small(weights=None)
        model.classifier[3] = nn.Linear(model.classifier[3].in_features, 2)
        model.load_state_dict(payload["state_dict"])
        model.eval()

        normalization = payload["normalization"]
        image_size = int(payload.get("image_size", 224))
        transform = transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=normalization["mean"],
                    std=normalization["std"],
                ),
            ]
        )

        classes = payload.get("class_to_idx", {})
        if "cardboard_box" not in classes:
            raise CategoryVerifierUnavailable(
                "Category checkpoint does not contain cardboard_box class metadata"
            )

        self._model = model
        self._transform = transform
        self._torch = torch
        self._payload = payload

    def verify(self, image: Image.Image) -> tuple[bool, float]:
        self._load()
        tensor = self._transform(image.convert("RGB")).unsqueeze(0)
        with self._torch.no_grad():
            probabilities = self._torch.softmax(self._model(tensor), dim=1)[0]
        positive_index = self._payload["class_to_idx"]["cardboard_box"]
        probability = float(probabilities[positive_index].item())
        return probability >= settings.category_probability_threshold, probability


category_verifier = CategoryVerifier()
