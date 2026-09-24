from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RETURNREVIEW_",
        env_file=(".env", "../.env"),
        extra="ignore",
    )

    env: str = "development"
    database_url: str = "sqlite:///./returnreview.db"
    database_schema: str | None = None
    storage_dir: str = "./storage"
    allowed_origins: str = "http://localhost:3000"
    max_upload_mb: int = 10
    demo_mode: bool = True

    cv_model_path: str = "./models/checkpoints/best.pt"
    cv_model_version: str = "untrained"
    clip_model: str = "ViT-B-32"
    clip_pretrained: str = "laion2b_s34b_b79k"
    prototype_bank_path: str = "./models/prototypes.npz"
    category_similarity_threshold: float = 0.72
    defect_similarity_threshold: float = 0.66
    defect_margin_threshold: float = 0.03

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    gemini_fallback_model: str | None = "gemini-3.5-flash"
    llm_eval_model: str | None = None
    llm_enabled: bool = False
    run_llm_eval_on_start: bool = False

    @property
    def storage_path(self) -> Path:
        return Path(self.storage_dir).resolve()

    @property
    def origins(self) -> list[str]:
        return [x.strip() for x in self.allowed_origins.split(",") if x.strip()]

    @property
    def database_backend(self) -> str:
        if self.database_url.startswith("sqlite"):
            return "sqlite"
        if self.database_url.startswith(("postgresql", "postgres")):
            return "postgresql"
        return "other"

    @property
    def durable_persistence(self) -> bool:
        return self.database_backend == "postgresql"


@lru_cache
def get_settings() -> Settings:
    return Settings()
