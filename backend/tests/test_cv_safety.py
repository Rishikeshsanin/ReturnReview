from io import BytesIO
from PIL import Image
from conftest import client


def make_jpeg() -> BytesIO:
    buf = BytesIO()
    Image.new("RGB", (640, 480), "white").save(buf, format="JPEG")
    buf.seek(0)
    return buf


def test_inspection_refuses_to_fake_cv_without_checkpoint():
    created = client.post("/api/cases", json={
        "external_case_id": "TEST-CV-NO-MODEL",
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

    inspection = client.post(f"/api/cases/{case_id}/inspect")
    assert inspection.status_code == 503
    assert "No trained segmentation checkpoint" in inspection.json()["detail"]

    detail = client.get(f"/api/cases/{case_id}")
    assert detail.status_code == 200
    assert detail.json()["case"]["status"] == "READY_FOR_INSPECTION"
