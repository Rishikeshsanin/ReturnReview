from contextlib import asynccontextmanager
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.api.cases import router as cases_router
from app.api.policies import router as policies_router
from app.api.metrics import router as metrics_router
from app.utils.config import get_settings

settings = get_settings()
settings.storage_path.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("returnreview")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("application_started env=%s cv_model_version=%s", settings.env, settings.cv_model_version)
    yield
    logger.info("application_stopped")


app = FastAPI(
    title="ReturnReview API",
    version="0.1.0",
    description="Evidence-first product return inspection API",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(cases_router)
app.include_router(policies_router)
app.include_router(metrics_router)
app.mount("/media", StaticFiles(directory=str(settings.storage_path)), name="media")


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    started = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        latency_ms = (perf_counter() - started) * 1000
        logger.exception(
            "request_failed request_id=%s method=%s path=%s latency_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            latency_ms,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
            headers={"X-Request-ID": request_id},
        )
    latency_ms = (perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_completed request_id=%s method=%s path=%s status=%s latency_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        latency_ms,
    )
    return response


@app.get("/health")
def health():
    return {
        "status": "ok",
        "environment": settings.env,
        "demo_mode": settings.demo_mode,
        "llm_enabled": settings.llm_enabled and bool(settings.gemini_api_key),
        "cv_model_version": settings.cv_model_version,
    }
