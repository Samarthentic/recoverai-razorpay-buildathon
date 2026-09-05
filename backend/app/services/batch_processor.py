"""
Batch processor — orchestrates the full revenue recovery pipeline and benchmarks
against synthetic ground truth.

WORKFLOW:
1. DETECT / PRE-SCREEN: Evaluate candidates to filter out non-actionable cases.
2. AI DIAGNOSIS: Gemini 3.5 Flash diagnoses root cause and recommends intervention.
3. POLICY EVALUATION: Deterministic safety engine validates/blocks/escalates.
4. SIMULATION: Stable SHA-256 simulation executes approved actions.
5. BENCHMARK & AUDIT: Metrics calculated against synthetic ground truth (isolated LLM vs composite).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import AuditLog, BatchRun, Payment, RecoveryResult
from app.schemas import AIRecommendation
from app.services.ai_engine import analyze_payment_with_source, heuristic_diagnose
from app.services.policy_engine import (
    PolicyConfig,
    create_policy_config_from_settings,
    evaluate_policy,
)
from app.services.recovery_simulator import simulate_recovery

logger = logging.getLogger(__name__)


def _log_audit(
    db: Session,
    batch_id: str,
    payment_id: str,
    event_type: str,
    details: dict,
) -> None:
    """Write an immutable audit log entry."""
    entry = AuditLog(
        batch_id=batch_id,
        payment_id=payment_id,
        event_type=event_type,
        details=json.dumps(details),
    )
    db.add(entry)


def pre_screen_payment(payment: Payment) -> tuple[bool, str]:
    """
    Deterministic pre-screening stage.
    
    Filters out obviously dead payments before LLM dispatch to avoid unnecessary
    API costs and latency.
    
    Returns:
        (is_candidate, reason)
    """
    if payment.failure_reason == "fraud_suspected":
        return False, "Pre-screen skipped: fraud flag requires security freeze, not revenue recovery"
    
    if payment.failure_reason == "account_closed" and not payment.customer_email:
        return False, "Pre-screen skipped: closed bank account with no alternate contact channel"
        
    if payment.failure_reason == "subscription_cancelled":
        return False, "Pre-screen skipped: subscription cancelled by customer"

    return True, "Pre-screen passed: viable candidate for recovery diagnosis"


def process_single_payment(
    db: Session,
    payment: Payment,
    batch_id: str,
    policy_config: PolicyConfig,
    settings: Settings | None = None,
    use_llm: bool = True,
) -> RecoveryResult:
    """
    Run the full recovery pipeline on a single payment.
    
    Returns a RecoveryResult containing AI recommendation, policy decision,
    simulated outcome, is_llm_generated indicator, and stored is_recoverable flag.
    """
    settings = settings or get_settings()

    # Step 1: Pre-screening check
    is_candidate, pre_screen_reason = pre_screen_payment(payment)
    is_llm_generated = False
    
    if not is_candidate:
        ai_rec = AIRecommendation(
            root_cause=pre_screen_reason,
            recommendation="do_not_retry",
            confidence=0.95,
            explanation=pre_screen_reason,
            is_recoverable=False,
        )
        is_llm_generated = False
    elif use_llm:
        logger.info(f"Analyzing payment {payment.id} (₹{payment.amount / 100:.2f}) with AI")
        ai_rec, is_llm_generated = analyze_payment_with_source(payment, settings)
    else:
        # Fast heuristic diagnosis (when batch limit is reached or in offline mode)
        ai_rec = heuristic_diagnose(payment)
        is_llm_generated = False

    _log_audit(db, batch_id, payment.id, "ai_analysis", {
        "root_cause": ai_rec.root_cause,
        "recommendation": ai_rec.recommendation,
        "confidence": ai_rec.confidence,
        "explanation": ai_rec.explanation,
        "is_recoverable": ai_rec.is_recoverable,
        "is_llm_generated": is_llm_generated,
        "pre_screen_passed": is_candidate,
    })

    # Step 2: Policy Evaluation (Deterministic - uses Payment DB record directly)
    policy_decision = evaluate_policy(payment, ai_rec, policy_config)

    _log_audit(db, batch_id, payment.id, "policy_check", {
        "decision": policy_decision.decision,
        "triggered_rules": policy_decision.triggered_rules,
        "reasons": policy_decision.reasons,
    })

    # Step 3: Execute or block via Simulator
    action_taken = "none"
    recovery_successful = None
    amount_recovered = 0

    if policy_decision.decision == "approved":
        action_taken = ai_rec.recommendation
        outcome = simulate_recovery(payment, ai_rec.recommendation)
        recovery_successful = outcome.success
        amount_recovered = outcome.amount_recovered

        _log_audit(db, batch_id, payment.id, "action_executed", {
            "action": action_taken,
            "success": outcome.success,
            "amount_recovered": amount_recovered,
            "details": outcome.details,
        })

    elif policy_decision.decision == "blocked":
        action_taken = "blocked"
        recovery_successful = False
        amount_recovered = 0

        _log_audit(db, batch_id, payment.id, "action_blocked", {
            "intended_action": ai_rec.recommendation,
            "triggered_rules": policy_decision.triggered_rules,
            "reasons": policy_decision.reasons,
        })

    elif policy_decision.decision == "escalated":
        action_taken = "escalated"
        recovery_successful = False
        amount_recovered = 0

        _log_audit(db, batch_id, payment.id, "escalated", {
            "intended_action": ai_rec.recommendation,
            "triggered_rules": policy_decision.triggered_rules,
            "reasons": policy_decision.reasons,
        })

    # Step 4: Save result with ai_is_recoverable and is_llm_generated recorded
    result = RecoveryResult(
        payment_id=payment.id,
        batch_id=batch_id,
        ai_root_cause=ai_rec.root_cause,
        ai_recommendation=ai_rec.recommendation,
        ai_confidence=ai_rec.confidence,
        ai_explanation=ai_rec.explanation,
        ai_is_recoverable=ai_rec.is_recoverable,
        is_llm_generated=is_llm_generated,
        policy_decision=policy_decision.decision,
        policy_reasons=json.dumps(policy_decision.triggered_rules),
        action_taken=action_taken,
        recovery_successful=recovery_successful,
        amount_recovered=amount_recovered,
    )
    db.add(result)

    return result


def _calculate_subset_classification_metrics(
    pairs: list[tuple[Payment, RecoveryResult]]
) -> tuple[float, float, float, float]:
    """Helper to calculate precision, recall, F1, and intervention accuracy on a pair subset."""
    if not pairs:
        return 0.0, 0.0, 0.0, 0.0

    total = len(pairs)
    tp = sum(
        1 for p, r in pairs
        if (getattr(r, "ai_is_recoverable", False) is True)
        and (getattr(p, "ground_truth_recoverable", False) is True)
    )
    fp = sum(
        1 for p, r in pairs
        if (getattr(r, "ai_is_recoverable", False) is True)
        and (getattr(p, "ground_truth_recoverable", False) is not True)
    )
    fn = sum(
        1 for p, r in pairs
        if (getattr(r, "ai_is_recoverable", False) is not True)
        and (getattr(p, "ground_truth_recoverable", False) is True)
    )

    prec = (tp / (tp + fp) * 100.0) if (tp + fp) > 0 else 0.0
    rec = (tp / (tp + fn) * 100.0) if (tp + fn) > 0 else 0.0
    f1 = (2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

    correct_interventions = sum(
        1 for p, r in pairs
        if r.ai_recommendation == getattr(p, "ground_truth_best_action", None)
    )
    acc = (correct_interventions / total * 100.0) if total > 0 else 0.0

    return round(prec, 2), round(rec, 2), round(f1, 2), round(acc, 2)


def calculate_metrics(
    payments: list[Payment],
    results: list[RecoveryResult],
) -> dict:
    """
    Computes rigorous evaluation metrics comparing AI predictions, policy decisions,
    and simulated outcomes against synthetic ground truth.
    
    Provides both:
    1. Full Pipeline Metrics (all records combined)
    2. Gemini LLM Metrics (strictly evaluated over the is_llm_generated == True subset)
    """
    total_analyzed = len(payments)
    if total_analyzed == 0:
        return {}

    total_at_risk = sum(p.amount for p in payments)
    
    # Ground-truth recoverable revenue (ground_truth_recoverable == True)
    gt_recoverable_rev = sum(
        p.amount for p in payments if getattr(p, "ground_truth_recoverable", False) is True
    )
    
    # AI predicted recoverable revenue (AI is_recoverable == True)
    ai_predicted_rev = sum(
        p.amount for p, r in zip(payments, results) if getattr(r, "ai_is_recoverable", False) is True
    )

    total_recovered = sum(r.amount_recovered for r in results)

    approved_count = sum(1 for r in results if r.policy_decision == "approved")
    blocked_count = sum(1 for r in results if r.policy_decision == "blocked")
    escalated_count = sum(1 for r in results if r.policy_decision == "escalated")
    successful_recoveries = sum(1 for r in results if r.recovery_successful is True)

    all_pairs = list(zip(payments, results))
    llm_pairs = [(p, r) for p, r in all_pairs if getattr(r, "is_llm_generated", False) is True]
    fallback_pairs = [(p, r) for p, r in all_pairs if getattr(r, "is_llm_generated", False) is not True]

    llm_count = len(llm_pairs)
    fallback_count = len(fallback_pairs)

    # Full pipeline classification metrics
    ai_precision, ai_recall, ai_f1, intervention_accuracy = _calculate_subset_classification_metrics(all_pairs)

    # Gemini LLM-specific classification metrics (isolated)
    llm_precision, llm_recall, llm_f1, llm_intervention_accuracy = _calculate_subset_classification_metrics(llm_pairs)

    # Rates
    recovery_rate = (total_recovered / total_at_risk * 100.0) if total_at_risk > 0 else 0.0
    recovery_efficiency = (
        (total_recovered / gt_recoverable_rev * 100.0) if gt_recoverable_rev > 0 else 0.0
    )
    approved_action_success_rate = (
        (successful_recoveries / approved_count * 100.0) if approved_count > 0 else 0.0
    )
    policy_block_rate = (blocked_count / total_analyzed * 100.0)
    escalation_rate = (escalated_count / total_analyzed * 100.0)

    return {
        "total_at_risk": total_at_risk,
        "ground_truth_recoverable_revenue": gt_recoverable_rev,
        "ai_predicted_recoverable_revenue": ai_predicted_rev,
        "total_recoverable": gt_recoverable_rev,
        "total_recovered": total_recovered,
        "recovery_rate": round(recovery_rate, 2),
        "recovery_efficiency": round(recovery_efficiency, 2),
        "approved_count": approved_count,
        "blocked_count": blocked_count,
        "escalated_count": escalated_count,
        "successful_recovery_count": successful_recoveries,
        
        # Full Pipeline Metrics
        "ai_precision": ai_precision,
        "ai_recall": ai_recall,
        "ai_f1": ai_f1,
        "intervention_accuracy": intervention_accuracy,
        "approved_action_success_rate": round(approved_action_success_rate, 2),
        "policy_block_rate": round(policy_block_rate, 2),
        "escalation_rate": round(escalation_rate, 2),

        # Gemini LLM-Specific Metrics
        "llm_analyzed_count": llm_count,
        "heuristic_fallback_count": fallback_count,
        "llm_precision": llm_precision,
        "llm_recall": llm_recall,
        "llm_f1": llm_f1,
        "llm_intervention_accuracy": llm_intervention_accuracy,
    }


def run_batch(db: Session, settings: Settings | None = None) -> BatchRun:
    """
    Process all failed payments in a single batch run.
    
    Creates a BatchRun record, executes AI -> Policy -> Simulator pipeline,
    computes ground-truth benchmarks and KPIs, and updates the database.
    """
    settings = settings or get_settings()
    policy_config = create_policy_config_from_settings(settings)

    batch_id = f"batch_{uuid.uuid4().hex[:10]}"
    batch = BatchRun(id=batch_id, status="running")
    db.add(batch)
    db.commit()

    logger.info(f"Starting batch run {batch_id}")

    # Fetch all failed payments
    payments = db.query(Payment).filter(Payment.status == "failed").all()

    if not payments:
        batch.status = "completed"
        batch.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.warning("No failed payments found for batch processing")
        return batch

    results: list[RecoveryResult] = []
    llm_calls_made = 0
    max_llm_calls = settings.ai_batch_limit  # 50 by default, 0 = unlimited

    for i, payment in enumerate(payments):
        try:
            # Check if we should call the live LLM or heuristic fallback
            use_llm = True
            if max_llm_calls > 0 and llm_calls_made >= max_llm_calls:
                use_llm = False
            elif not settings.gemini_api_key:
                use_llm = False

            result = process_single_payment(
                db, payment, batch_id, policy_config, settings, use_llm=use_llm
            )
            results.append(result)

            if result.is_llm_generated:
                llm_calls_made += 1

            if (i + 1) % 50 == 0:
                db.commit()
                logger.info(f"Processed {i + 1}/{len(payments)} payments (Live LLM calls: {llm_calls_made})")

        except Exception as e:
            logger.error(f"Error processing payment {payment.id}: {e}", exc_info=True)
            _log_audit(db, batch_id, payment.id, "error", {"error": str(e)})

    # Compute comprehensive metrics
    metrics = calculate_metrics(payments, results)

    batch.status = "completed"
    batch.total_payments = len(payments)
    batch.total_at_risk = metrics.get("total_at_risk", 0)
    batch.ground_truth_recoverable_revenue = metrics.get("ground_truth_recoverable_revenue", 0)
    batch.ai_predicted_recoverable_revenue = metrics.get("ai_predicted_recoverable_revenue", 0)
    batch.total_recoverable = metrics.get("total_recoverable", 0)
    batch.total_recovered = metrics.get("total_recovered", 0)
    batch.recovery_rate = metrics.get("recovery_rate", 0.0)
    batch.recovery_efficiency = metrics.get("recovery_efficiency", 0.0)
    batch.approved_count = metrics.get("approved_count", 0)
    batch.blocked_count = metrics.get("blocked_count", 0)
    batch.escalated_count = metrics.get("escalated_count", 0)
    batch.successful_recovery_count = metrics.get("successful_recovery_count", 0)
    
    # Full Pipeline Metrics
    batch.ai_precision = metrics.get("ai_precision", 0.0)
    batch.ai_recall = metrics.get("ai_recall", 0.0)
    batch.ai_f1 = metrics.get("ai_f1", 0.0)
    batch.intervention_accuracy = metrics.get("intervention_accuracy", 0.0)
    batch.approved_action_success_rate = metrics.get("approved_action_success_rate", 0.0)
    batch.policy_block_rate = metrics.get("policy_block_rate", 0.0)
    batch.escalation_rate = metrics.get("escalation_rate", 0.0)

    # Gemini LLM-Specific Metrics
    batch.llm_analyzed_count = metrics.get("llm_analyzed_count", 0)
    batch.heuristic_fallback_count = metrics.get("heuristic_fallback_count", 0)
    batch.llm_precision = metrics.get("llm_precision", 0.0)
    batch.llm_recall = metrics.get("llm_recall", 0.0)
    batch.llm_f1 = metrics.get("llm_f1", 0.0)
    batch.llm_intervention_accuracy = metrics.get("llm_intervention_accuracy", 0.0)

    batch.completed_at = datetime.now(timezone.utc)

    db.commit()

    logger.info(
        f"Batch {batch_id} completed: {len(payments)} payments | "
        f"At Risk: ₹{batch.total_at_risk/100:.2f} | "
        f"GT Recoverable: ₹{batch.ground_truth_recoverable_revenue/100:.2f} | "
        f"AI Predicted: ₹{batch.ai_predicted_recoverable_revenue/100:.2f} | "
        f"Recovered: ₹{batch.total_recovered/100:.2f} (Rate: {batch.recovery_rate:.1f}%, Efficiency: {batch.recovery_efficiency:.1f}%) | "
        f"Pipeline F1: {batch.ai_f1:.1f}% | LLM F1 (n={batch.llm_analyzed_count}): {batch.llm_f1:.1f}%"
    )

    return batch
