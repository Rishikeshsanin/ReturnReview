import os

os.environ["RETURNREVIEW_DATABASE_URL"] = "sqlite:///./test_returnreview.db"
os.environ["RETURNREVIEW_STORAGE_DIR"] = "./test_storage"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
