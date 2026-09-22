from app.services.policy_service import retrieve_return_policy


def test_cardboard_policy_exists():
    policy = retrieve_return_policy("cardboard_box", "tear")
    assert policy is not None
    assert policy.policy_id == "RET-CBX-001"
