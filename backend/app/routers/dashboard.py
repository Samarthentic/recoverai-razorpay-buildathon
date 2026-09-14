from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BatchRun, Payment
from app.schemas import DashboardStats

router = APIRouter()

@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_payment_count = db.query(Payment).count()

    # 1. Running batch takes highest precedence
    running_batch = db.query(BatchRun).filter(BatchRun.status == "running").first()
    if running_batch:
        return DashboardStats(
            state="running",
            has_analysis=False,
            payment_count=total_payment_count,
            total_payments=total_payment_count,
            batch_id=running_batch.id,
        )

    # 2. Latest completed batch
    batch = (
        db.query(BatchRun)
        .filter(BatchRun.status == "completed")
        .order_by(BatchRun.completed_at.desc(), BatchRun.started_at.desc())
        .first()
    )

    if not batch:
        # 3. No running or completed batch → ready
        return DashboardStats(
            state="ready",
            has_analysis=False,
            payment_count=total_payment_count,
            total_payments=total_payment_count,
            batch_id=None,
        )

    return DashboardStats(
        state="completed",
        has_analysis=True,
        payment_count=total_payment_count,
        total_payments=batch.total_payments,
        total_at_risk=batch.total_at_risk,
        ground_truth_recoverable_revenue=batch.ground_truth_recoverable_revenue or 0,
        ai_predicted_recoverable_revenue=batch.ai_predicted_recoverable_revenue or 0,
        total_recoverable=batch.total_recoverable or 0,
        total_recovered=batch.total_recovered,
        recovery_rate=batch.recovery_rate,
        recovery_efficiency=batch.recovery_efficiency or 0.0,
        approved_count=batch.approved_count,
        blocked_count=batch.blocked_count,
        escalated_count=batch.escalated_count,
        successful_recovery_count=batch.successful_recovery_count or 0,
        # Full Pipeline
        ai_precision=batch.ai_precision or 0.0,
        ai_recall=batch.ai_recall or 0.0,
        ai_f1=batch.ai_f1 or 0.0,
        intervention_accuracy=batch.intervention_accuracy or 0.0,
        approved_action_success_rate=batch.approved_action_success_rate or 0.0,
        policy_block_rate=batch.policy_block_rate or 0.0,
        escalation_rate=batch.escalation_rate or 0.0,

        # Gemini LLM-Specific
        llm_analyzed_count=batch.llm_analyzed_count or 0,
        heuristic_fallback_count=batch.heuristic_fallback_count or 0,
        llm_precision=batch.llm_precision or 0.0,
        llm_recall=batch.llm_recall or 0.0,
        llm_f1=batch.llm_f1 or 0.0,
        llm_intervention_accuracy=batch.llm_intervention_accuracy or 0.0,

        batch_id=batch.id,
    )
