import os

os.environ["RETURNREVIEW_DATABASE_URL"] = "sqlite:///./test_returnreview.db"
os.environ["RETURNREVIEW_STORAGE_DIR"] = "./test_storage"

from fastapi.testclient import TestClient
from app.database import Base, engine
from app.main import app

# Keep tests deterministic even when the TestClient is used outside a context
# manager and a framework version defers lifespan startup.
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)
