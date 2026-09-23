from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.utils.config import get_settings

settings = get_settings()

connect_args: dict = {}
if settings.database_backend == "sqlite":
    connect_args["check_same_thread"] = False
elif settings.database_backend == "postgresql":
    connect_args["connect_timeout"] = 10
    if settings.database_schema:
        connect_args["options"] = f"-csearch_path={settings.database_schema}"

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    future=True,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
