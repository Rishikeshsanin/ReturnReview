from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
import subprocess
import sys
import threading
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

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


def _redact_runtime_text(value: str) -> str:
    if settings.gemini_api_key:
        value = value.replace(settings.gemini_api_key, "[REDACTED]")
    return value


def _run_llm_evaluation_job() -> None:
    """Run the fixed Gemini evaluation once without blocking API startup."""
    if not settings.llm_enabled or not settings.gemini_api_key:
        logger.warning("llm_eval_skipped reason=gemini_not_enabled")
        return

    output = Path("/app/artifacts/evaluation/llm_eval_results.jsonl")
    output.parent.mkdir(parents=True, exist_ok=True)
    evaluation_model = settings.llm_eval_model or settings.gemini_model
    command = [
        sys.executable,
        "/app/scripts/run_gemini_eval.py",
        "--input",
        "/app/data/evaluation/llm_eval_cases.jsonl",
        "--output",
        str(output),
        "--model",
        evaluation_model,
    ]

    logger.info("llm_eval_started model=%s cases_file=/app/data/evaluation/llm_eval_cases.jsonl", evaluation_model)
    try:
        completed = subprocess.run(
            command,
            cwd="/app",
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    except Exception as exc:
        logger.exception("llm_eval_failed error=%s", exc.__class__.__name__)
        return

    stdout = _redact_runtime_text(completed.stdout or "").strip()
    stderr = _redact_runtime_text(completed.stderr or "").strip()
    if stdout:
        logger.info("llm_eval_stdout %s", stdout.replace("\n", " | "))
    if completed.returncode != 0:
        logger.error(
            "llm_eval_failed returncode=%s stderr=%s",
            completed.returncode,
            stderr.replace("\n", " | "),
        )
        return

    logger.info("llm_eval_completed output=%s", output)


def _maybe_start_llm_evaluation() -> None:
    if not settings.run_llm_eval_on_start:
        return
    threading.Thread(
        target=_run_llm_evaluation_job,
        name="returnreview-llm-eval",
        daemon=True,
    ).start()


def _migrate_legacy_sqlite() -> None:
    if settings.database_backend != "sqlite":
        return
    with engine.begin() as connection:
        image_columns = {
            row[1] for row in connection.execute(text("pragma table_info(case_images)")).fetchall()
        }
        if image_columns:
            if "content_type" not in image_columns:
                connection.execute(text(
                    "alter table case_images add column content_type varchar(80) default 'image/jpeg'"
                ))
            if "image_blob" not in image_columns:
                connection.execute(text("alter table case_images add column image_blob blob"))

        finding_columns = {
            row[1] for row in connection.execute(text("pragma table_info(defect_findings)")).fetchall()
        }
        if finding_columns:
            if "mask_content_type" not in finding_columns:
                connection.execute(text(
                    "alter table defect_findings add column mask_content_type varchar(80)"
                ))
            if "mask_blob" not in finding_columns:
                connection.execute(text("alter table defect_findings add column mask_blob blob"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    _migrate_legacy_sqlite()
    Base.metadata.create_all(bind=engine)
    logger.info(
        "application_started env=%s database_backend=%s durable_persistence=%s cv_model_version=%s",
        settings.env,
        settings.database_backend,
        settings.durable_persistence,
        settings.cv_model_version,
    )
    _maybe_start_llm_evaluation()
    yield
    logger.info("application_stopped")


app = FastAPI(
    title="ReturnReview API",
    version="0.2.0",
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


def readiness_payload(database_ok: bool) -> dict:
    cv_ready = (
        settings.cv_model_version != "untrained"
        and Path(settings.cv_model_path).exists()
        and Path(settings.prototype_bank_path).exists()
    )
    llm_ready = settings.llm_enabled and bool(settings.gemini_api_key)
    blockers: list[str] = []
    if not database_ok:
        blockers.append("database_unavailable")
    if not settings.durable_persistence:
        blockers.append("durable_persistence_not_enabled")
    if not cv_ready:
        blockers.append("validated_cv_artifacts_not_configured")
    if not llm_ready:
        blockers.append("gemini_not_enabled")
    return {
        "status": "ready" if database_ok else "not_ready",
        "database": {
            "ok": database_ok,
            "backend": settings.database_backend,
            "durable": settings.durable_persistence,
            "schema": settings.database_schema,
        },
        "cv_ready": cv_ready,
        "cv_model_version": settings.cv_model_version,
        "llm_ready": llm_ready,
        "gemini_model": settings.gemini_model,
        "blockers": blockers,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "environment": settings.env,
        "demo_mode": settings.demo_mode,
        "database_backend": settings.database_backend,
        "durable_persistence": settings.durable_persistence,
        "llm_enabled": settings.llm_enabled and bool(settings.gemini_api_key),
        "cv_model_version": settings.cv_model_version,
    }


@app.get("/readiness")
def readiness():
    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
    except Exception:
        logger.exception("readiness_database_failed")
        return JSONResponse(status_code=503, content=readiness_payload(False))
    return readiness_payload(True)
