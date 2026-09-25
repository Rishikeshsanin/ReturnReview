from conftest import client


def test_metrics_endpoint_serves_reviewed_llm_and_real_public_pilot_cv_metrics():
    response = client.get("/api/metrics")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "evaluated"
    assert payload["scope"] == "llm_review_complete_cv_public_pilot"

    assert payload["llm_review"]["evaluation_cases"] == 6
    assert payload["llm_review"]["policy_correctness"] == 1.0
    assert payload["llm_review"]["required_tool_coverage"] == 1.0

    cv = payload["computer_vision"]
    assert cv["status"] == "evaluated_public_pilot"
    assert cv["scope"] == "lightweight_production_candidate_public_data"
    assert cv["segmentation"]["test_images"] == 169
    assert cv["product_verification"]["test_samples"] == 32
    assert cv["product_verification"]["accuracy"] == 1.0
    assert cv["runtime"]["railway_fit"]["fits_with_reserve"] is True
    assert cv["provenance"]["release_tag"] == "cv-lightweight-1"
