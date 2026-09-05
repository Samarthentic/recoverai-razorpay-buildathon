"""
Tests for deterministic ground-truth generation logic.
"""

from app.models import Payment
from app.seed.generate_data import compute_ground_truth


def test_ground_truth_fraud_suspected():
    payment = Payment(
        id="pay_gt_01",
        payment_method="card",
        failure_reason="fraud_suspected",
        amount=50000,
    )
    rec, action, prob, reason = compute_ground_truth(payment)
    assert rec is False
    assert action == "do_not_retry"
    assert prob == 0.0
    assert "fraud" in reason.lower()


def test_ground_truth_transient_upi_timeout():
    payment = Payment(
        id="pay_gt_02",
        payment_method="upi",
        failure_reason="upi_timeout",
        retry_count=0,
        amount=25000,
    )
    rec, action, prob, reason = compute_ground_truth(payment)
    assert rec is True
    assert action == "retry_payment"
    assert prob >= 0.60
    assert "transient" in reason.lower()


def test_ground_truth_card_expired_with_email():
    payment = Payment(
        id="pay_gt_03",
        payment_method="card",
        failure_reason="card_expired",
        customer_email="user@example.com",
        amount=100000,
    )
    rec, action, prob, reason = compute_ground_truth(payment)
    assert rec is True
    assert action == "send_payment_link"
    assert prob > 0.0


def test_ground_truth_card_expired_without_email():
    payment = Payment(
        id="pay_gt_04",
        payment_method="card",
        failure_reason="card_expired",
        customer_email=None,
        amount=100000,
    )
    rec, action, prob, reason = compute_ground_truth(payment)
    assert rec is False
    assert action == "do_not_retry"
    assert prob == 0.0


def test_ground_truth_subscription_cancelled():
    payment = Payment(
        id="pay_gt_05",
        payment_method="emandate",
        failure_reason="subscription_cancelled",
        subscription_id="sub_123",
        amount=99900,
    )
    rec, action, prob, reason = compute_ground_truth(payment)
    assert rec is False
    assert action == "do_not_retry"
    assert prob == 0.0
