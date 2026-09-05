"""
Tests for evaluation metrics: precision, recall, F1, accuracy, efficiency,
and isolated Gemini LLM vs. Fallback metrics.
"""

from app.models import Payment, RecoveryResult
from app.services.batch_processor import calculate_metrics


def test_metrics_calculation_perfect_alignment():
    p1 = Payment(
        id="pay_m1",
        amount=100000,
        ground_truth_recoverable=True,
        ground_truth_best_action="retry_payment",
    )
    p2 = Payment(
        id="pay_m2",
        amount=200000,
        ground_truth_recoverable=False,
        ground_truth_best_action="do_not_retry",
    )
    
    r1 = RecoveryResult(
        payment_id="pay_m1",
        batch_id="b1",
        ai_recommendation="retry_payment",
        ai_is_recoverable=True,
        is_llm_generated=True,
        policy_decision="approved",
        recovery_successful=True,
        amount_recovered=100000,
    )
    r2 = RecoveryResult(
        payment_id="pay_m2",
        batch_id="b1",
        ai_recommendation="do_not_retry",
        ai_is_recoverable=False,
        is_llm_generated=True,
        policy_decision="approved",
        recovery_successful=False,
        amount_recovered=0,
    )

    metrics = calculate_metrics([p1, p2], [r1, r2])

    assert metrics["total_at_risk"] == 300000
    assert metrics["ground_truth_recoverable_revenue"] == 100000
    assert metrics["ai_predicted_recoverable_revenue"] == 100000
    assert metrics["total_recovered"] == 100000
    assert metrics["recovery_rate"] == 33.33  # 100K / 300K
    assert metrics["recovery_efficiency"] == 100.0  # 100K / 100K GT
    assert metrics["ai_precision"] == 100.0
    assert metrics["ai_recall"] == 100.0
    assert metrics["ai_f1"] == 100.0
    assert metrics["intervention_accuracy"] == 100.0
    assert metrics["llm_analyzed_count"] == 2
    assert metrics["heuristic_fallback_count"] == 0
    assert metrics["llm_precision"] == 100.0
    assert metrics["llm_recall"] == 100.0
    assert metrics["llm_f1"] == 100.0
    assert metrics["llm_intervention_accuracy"] == 100.0


def test_metrics_calculation_fallback_only():
    """When Gemini is not used, llm_analyzed_count is 0 and llm_* metrics are 0.0."""
    p1 = Payment(id="p1", amount=100, ground_truth_recoverable=True, ground_truth_best_action="retry_payment")
    p2 = Payment(id="p2", amount=200, ground_truth_recoverable=False, ground_truth_best_action="do_not_retry")

    r1 = RecoveryResult(payment_id="p1", batch_id="b", ai_recommendation="retry_payment", ai_is_recoverable=True, is_llm_generated=False, policy_decision="approved", recovery_successful=True, amount_recovered=100)
    r2 = RecoveryResult(payment_id="p2", batch_id="b", ai_recommendation="do_not_retry", ai_is_recoverable=False, is_llm_generated=False, policy_decision="approved", recovery_successful=False, amount_recovered=0)

    metrics = calculate_metrics([p1, p2], [r1, r2])

    assert metrics["llm_analyzed_count"] == 0
    assert metrics["heuristic_fallback_count"] == 2
    assert metrics["llm_precision"] == 0.0
    assert metrics["llm_recall"] == 0.0
    assert metrics["llm_f1"] == 0.0
    assert metrics["llm_intervention_accuracy"] == 0.0
    # Full pipeline metrics are still calculated
    assert metrics["ai_precision"] == 100.0
    assert metrics["ai_recall"] == 100.0
    assert metrics["ai_f1"] == 100.0


def test_metrics_calculation_mixed_llm_and_fallback():
    """Verify separate metrics for LLM subset and full composite pipeline."""
    # LLM records (2 items): 1 TP, 1 FP -> LLM precision = 50%
    p_llm1 = Payment(id="pl1", amount=100, ground_truth_recoverable=True, ground_truth_best_action="retry_payment")
    p_llm2 = Payment(id="pl2", amount=100, ground_truth_recoverable=False, ground_truth_best_action="do_not_retry")
    r_llm1 = RecoveryResult(payment_id="pl1", batch_id="b", ai_recommendation="retry_payment", ai_is_recoverable=True, is_llm_generated=True, policy_decision="approved", recovery_successful=True, amount_recovered=100)
    r_llm2 = RecoveryResult(payment_id="pl2", batch_id="b", ai_recommendation="retry_payment", ai_is_recoverable=True, is_llm_generated=True, policy_decision="blocked", recovery_successful=False, amount_recovered=0)

    # Fallback records (2 items): 1 TP, 1 TN -> Fallback precision = 100%
    p_fb1 = Payment(id="pf1", amount=100, ground_truth_recoverable=True, ground_truth_best_action="send_payment_link")
    p_fb2 = Payment(id="pf2", amount=100, ground_truth_recoverable=False, ground_truth_best_action="do_not_retry")
    r_fb1 = RecoveryResult(payment_id="pf1", batch_id="b", ai_recommendation="send_payment_link", ai_is_recoverable=True, is_llm_generated=False, policy_decision="approved", recovery_successful=True, amount_recovered=100)
    r_fb2 = RecoveryResult(payment_id="pf2", batch_id="b", ai_recommendation="do_not_retry", ai_is_recoverable=False, is_llm_generated=False, policy_decision="approved", recovery_successful=False, amount_recovered=0)

    payments = [p_llm1, p_llm2, p_fb1, p_fb2]
    results = [r_llm1, r_llm2, r_fb1, r_fb2]

    metrics = calculate_metrics(payments, results)

    assert metrics["llm_analyzed_count"] == 2
    assert metrics["heuristic_fallback_count"] == 2

    # LLM-only: TP=1, FP=1 -> 50%
    assert metrics["llm_precision"] == 50.0
    assert metrics["llm_recall"] == 100.0  # TP=1, FN=0 in LLM subset
    assert metrics["llm_f1"] == 66.67
    assert metrics["llm_intervention_accuracy"] == 50.0

    # Full pipeline: TP=2 (pl1, pf1), FP=1 (pl2), FN=0 -> Precision = 2/3 = 66.67%
    assert metrics["ai_precision"] == 66.67
    assert metrics["ai_recall"] == 100.0
    assert metrics["ai_f1"] == 80.0
    assert metrics["intervention_accuracy"] == 75.0  # 3 of 4 match best action
