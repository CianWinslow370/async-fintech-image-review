from src.batch_worker import decide


def test_high_value_payment_requires_manual_review():
    decision, reason = decide(125_000)
    assert decision == "manual_review"
    assert "threshold" in reason
