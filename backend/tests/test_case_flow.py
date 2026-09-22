from conftest import client


def test_create_and_list_case():
    payload = {
        "external_case_id": "TEST-1001",
        "product_name": "Corrugated Shipping Box",
        "product_category": "cardboard_box",
        "customer_reason": "Box arrived visibly damaged",
    }
    created = client.post("/api/cases", json=payload)
    assert created.status_code in (201, 409)
    listed = client.get("/api/cases")
    assert listed.status_code == 200
    assert isinstance(listed.json(), list)
