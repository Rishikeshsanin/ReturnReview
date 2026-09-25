from io import BytesIO
from uuid import uuid4

from PIL import Image

from conftest import client


def make_jpeg() -> BytesIO:
    buf = BytesIO()
    Image.new("RGB", (640, 480), "white").save(buf, format="JPEG")
    buf.seek(0)
    return buf


def test_create_and_list_case():
    payload = {
        "external_case_id": f"TEST-{uuid4()}",
        "product_name": "Corrugated Shipping Box",
        "product_category": "cardboard_box",
        "customer_reason": "Box arrived visibly damaged",
    }
    created = client.post("/api/cases", json=payload)
    assert created.status_code == 201
    listed = client.get("/api/cases")
    assert listed.status_code == 200
    assert isinstance(listed.json(), list)


def test_uploaded_media_is_served_from_case_endpoint():
    created = client.post("/api/cases", json={
        "external_case_id": f"TEST-MEDIA-{uuid4()}",
        "product_name": "Corrugated Shipping Box",
        "product_category": "cardboard_box",
        "customer_reason": "Visible box damage",
    })
    assert created.status_code == 201
    case_id = created.json()["id"]

    uploaded = client.post(
        f"/api/cases/{case_id}/images",
        data={"view_label": "front"},
        files={"image": ("front.jpg", make_jpeg(), "image/jpeg")},
    )
    assert uploaded.status_code == 201

    detail = client.get(f"/api/cases/{case_id}")
    assert detail.status_code == 200
    image = detail.json()["images"][0]
    assert image["image_url"].startswith(f"/api/cases/{case_id}/images/")

    media = client.get(image["image_url"])
    assert media.status_code == 200
    assert media.headers["content-type"].startswith("image/jpeg")
    assert len(media.content) > 100


def test_inspect_response_immediately_contains_persisted_cv_evidence(monkeypatch):
    created = client.post("/api/cases", json={
        "external_case_id": f"TEST-CV-REFRESH-{uuid4()}",
        "product_name": "Corrugated Shipping Box",
        "product_category": "cardboard_box",
        "customer_reason": "Visible box damage",
    })
    assert created.status_code == 201
    case_id = created.json()["id"]

    for view in ("front", "back"):
        uploaded = client.post(
            f"/api/cases/{case_id}/images",
            data={"view_label": view},
            files={"image": (f"{view}.jpg", make_jpeg(), "image/jpeg")},
        )
        assert uploaded.status_code == 201

    def fake_inspect(image_path, image_id, image_blob=None):
        return {
            "model_version": "test-lightweight-cv",
            "product_similarity": 0.91,
            "product_verified": True,
            "latency_ms": 12.0,
            "findings": [],
        }

    monkeypatch.setattr("app.api.cases.cv_service.inspect", fake_inspect)
    inspected = client.post(f"/api/cases/{case_id}/inspect")
    assert inspected.status_code == 200
    payload = inspected.json()
    assert payload["case"]["status"] == "CV_COMPLETE"
    assert payload["evidence"]["category_verified"] is True
    assert payload["evidence"]["verification_score"] == 0.91
    assert len(payload["images"]) == 2
