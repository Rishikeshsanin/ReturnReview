from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
from app.api.cases import router as cases_router
from app.api.policies import router as policies_router
from app.api.metrics import router as metrics_router
from app.utils.config import get_settings

settings = get_settings()
app = FastAPI(title="ReturnReview API", version="0.1.0", description="Evidence-first product return inspection API")
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(cases_router)
app.include_router(policies_router)
app.include_router(metrics_router)
settings.storage_path.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(settings.storage_path)), name="media")


@app.on_event("startup")
def startup() -> None:
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "environment": settings.env,
        "demo_mode": settings.demo_mode,
        "llm_enabled": settings.llm_enabled and bool(settings.gemini_api_key),
        "cv_model_version": settings.cv_model_version,
    }
