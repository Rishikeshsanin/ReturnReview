from conftest import client


def test_metrics_endpoint_serves_reviewed_llm_metrics_without_fake_cv_results():
    response = client.get("/api/metrics")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "partially_evaluated"
    assert payload["scope"] == "llm_review_complete_cv_pending"
    assert payload["llm_review"]["evaluation_cases"] == 6
    assert payload["llm_review"]["policy_correctness"] == 1.0
    assert payload["llm_review"]["required_tool_coverage"] == 1.0
    assert payload["computer_vision"]["status"] == "not_evaluated"
