"""
Tests for stable recovery simulation reproducibility, domain consistency, and ground-truth independence.
"""

from app.models import Payment
from app.seed.generate_data import generate_payments
from app.services.recovery_simulator import _get_stable_seed, simulate_recovery


def test_seed_generation_stability():
    """Verify SHA-256 seed is deterministic and consistent."""
    seed1 = _get_stable_seed("pay_test_123", "retry_payment")
    seed2 = _get_stable_seed("pay_test_123", "retry_payment")
    assert seed1 == seed2, "Seed must be identical for same payment ID and action"
    
    seed3 = _get_stable_seed("pay_test_123", "send_payment_link")
    assert seed1 != seed3, "Seed must vary with different actions"


def test_simulation_reproducibility_across_calls():
    """Verify simulate_recovery produces identical outcome across multiple invocations."""
    payment = Payment(
        id="pay_sim_repro_01",
        amount=50000,
        payment_method="upi",
        failure_reason="upi_timeout",
        retry_count=0,
    )
    
    outcome1 = simulate_recovery(payment, "retry_payment")
    outcome2 = simulate_recovery(payment, "retry_payment")
    outcome3 = simulate_recovery(payment, "retry_payment")

    assert outcome1.success == outcome2.success == outcome3.success
    assert outcome1.amount_recovered == outcome2.amount_recovered == outcome3.amount_recovered
    assert outcome1.details == outcome2.details == outcome3.details


def test_permanent_failure_never_succeeds_on_retry():
    """Verify card_expired, fraud_suspected, account_closed never recover on direct retry."""
    reasons = ["card_expired", "fraud_suspected", "account_closed", "subscription_cancelled"]
    for reason in reasons:
        payment = Payment(
            id=f"pay_perm_{reason}",
            amount=50000,
            payment_method="card",
            failure_reason=reason,
            retry_count=0,
        )
        outcome = simulate_recovery(payment, "retry_payment")
        assert outcome.success is False
        assert outcome.amount_recovered == 0


def test_unrecoverable_characteristics_never_recover_across_any_action():
    """
    Verify payments with unrecoverable characteristics yield 0% simulated recovery
    across all possible recovery actions.
    """
    all_actions = [
        "retry_payment",
        "send_payment_link",
        "send_reminder",
        "offer_alternative_method",
        "escalate_to_human",
        "do_not_retry",
    ]

    # Test 1: Fraud suspected
    p_fraud = Payment(id="p_fraud", failure_reason="fraud_suspected", amount=50000, customer_email="user@test.com")
    for action in all_actions:
        outcome = simulate_recovery(p_fraud, action)
        assert outcome.success is False
        assert outcome.amount_recovered == 0

    # Test 2: Closed account
    p_closed = Payment(id="p_closed", failure_reason="account_closed", amount=50000, customer_email="user@test.com")
    for action in all_actions:
        outcome = simulate_recovery(p_closed, action)
        assert outcome.success is False
        assert outcome.amount_recovered == 0

    # Test 3: Missing email on communication actions
    p_no_email = Payment(id="p_no_email", failure_reason="card_expired", amount=50000, customer_email=None)
    for action in ["send_payment_link", "send_reminder", "offer_alternative_method"]:
        outcome = simulate_recovery(p_no_email, action)
        assert outcome.success is False
        assert outcome.amount_recovered == 0


def test_synthetic_dataset_recovery_bound_invariant():
    """
    Verify that across all synthetic records, any record where ground_truth_recoverable=False
    cannot recover revenue under any action, ensuring recovered revenue <= ground-truth recoverable revenue.
    """
    from unittest.mock import MagicMock
    mock_db = MagicMock()

    # Collect all synthetic payments (520 total: 5 demo + 15 edge + 500 synthetic)
    payments: list[Payment] = generate_payments(mock_db, count=500, seed=42)

    gt_recoverable_pool = sum(p.amount for p in payments if p.ground_truth_recoverable)
    total_recovered_on_best_action = 0

    for payment in payments:
        # If payment is unrecoverable, no action should recover money
        if not payment.ground_truth_recoverable:
            for action in ["retry_payment", "send_payment_link", "send_reminder", "offer_alternative_method"]:
                outcome = simulate_recovery(payment, action)
                assert outcome.success is False, f"Payment {payment.id} with GT=False recovered on action {action}"
                assert outcome.amount_recovered == 0

        # Simulate on best action
        if payment.ground_truth_best_action:
            outcome = simulate_recovery(payment, payment.ground_truth_best_action)
            total_recovered_on_best_action += outcome.amount_recovered

    # Invariant: Total recovered cannot exceed ground truth pool
    assert total_recovered_on_best_action <= gt_recoverable_pool
