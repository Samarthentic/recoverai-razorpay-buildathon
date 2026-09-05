"""
Tests for guaranteed deterministic demo scenarios (Cases A through E).
"""

from app.models import Payment
from app.schemas import AIRecommendation
from app.services.policy_engine import evaluate_policy
from app.services.recovery_simulator import simulate_recovery


def test_case_a_approved_happy_path():
    """CASE A: Approved Happy Path - AI recommends retry, policy approves, simulator succeeds."""
    payment = Payment(
        id="pay_demo_happy_path",
        amount=50000,
        payment_method="upi",
        failure_reason="upi_timeout",
        retry_count=0,
        customer_email="demo_happy@example.com",
    )
    rec = AIRecommendation(
        root_cause="Transient UPI gateway timeout",
        recommendation="retry_payment",
        confidence=0.85,
        explanation="Standard transient timeout. Retry recommended.",
        is_recoverable=True,
    )
    decision = evaluate_policy(payment, rec)
    assert decision.decision == "approved", "Case A must be approved by policy"

    outcome = simulate_recovery(payment, rec.recommendation)
    assert outcome.amount_recovered == 50000
    assert outcome.success is True


def test_case_b_policy_block_max_retries():
    """CASE B: Policy Block - AI recommends retry, but retry_count >= max_retries."""
    payment = Payment(
        id="pay_demo_max_retries",
        amount=250000,
        payment_method="upi",
        failure_reason="upi_timeout",
        retry_count=4,  # Exceeds max 3
        customer_email="demo_max@example.com",
    )
    rec = AIRecommendation(
        root_cause="UPI timeout",
        recommendation="retry_payment",
        confidence=0.80,
        explanation="AI mistakenly suggests retry despite retry count.",
        is_recoverable=True,
    )
    decision = evaluate_policy(payment, rec)
    assert decision.decision == "blocked", "Case B must be blocked by policy"
    assert "max_retry_exceeded" in decision.triggered_rules


def test_case_c_high_value_escalation():
    """CASE C: High Value Escalation - Payment exceeds high-value threshold (₹50,000)."""
    payment = Payment(
        id="pay_demo_high_value",
        amount=7500000,  # ₹75,000 > ₹50,000 threshold
        payment_method="card",
        failure_reason="insufficient_funds",
        retry_count=0,
        customer_email="demo_hv@example.com",
    )
    rec = AIRecommendation(
        root_cause="Insufficient card funds",
        recommendation="send_payment_link",
        confidence=0.75,
        explanation="Send payment link for high-value card decline.",
        is_recoverable=True,
    )
    decision = evaluate_policy(payment, rec)
    assert decision.decision == "escalated", "Case C must be escalated to human"
    assert "high_value_human_review" in decision.triggered_rules


def test_case_d_missing_contact_block():
    """CASE D: Missing Contact Block - AI recommends send_payment_link but customer_email is None."""
    payment = Payment(
        id="pay_demo_no_email",
        amount=300000,
        payment_method="card",
        failure_reason="card_expired",
        retry_count=0,
        customer_email=None,  # Missing email
    )
    rec = AIRecommendation(
        root_cause="Card expired",
        recommendation="send_payment_link",
        confidence=0.70,
        explanation="Payment link needed for expired card.",
        is_recoverable=True,
    )
    decision = evaluate_policy(payment, rec)
    assert decision.decision == "blocked", "Case D must be blocked due to missing email"
    assert "missing_contact_info" in decision.triggered_rules


def test_case_e_low_confidence_escalation():
    """CASE E: Low Confidence Escalation - AI confidence below threshold (0.6)."""
    payment = Payment(
        id="pay_demo_low_conf",
        amount=200000,
        payment_method="netbanking",
        failure_reason="session_timeout",
        retry_count=1,
        customer_email="demo_lc@example.com",
    )
    rec = AIRecommendation(
        root_cause="Uncertain decline reason",
        recommendation="retry_payment",
        confidence=0.45,  # < 0.6 threshold
        explanation="Model uncertain of root cause.",
        is_recoverable=True,
    )
    decision = evaluate_policy(payment, rec)
    assert decision.decision == "escalated", "Case E must be escalated due to low confidence"
    assert "low_confidence_escalate" in decision.triggered_rules
