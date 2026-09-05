"""
SQLAlchemy ORM models.

All monetary amounts are stored in paise (1 INR = 100 paise) to avoid
floating-point precision issues. Convert to INR only at the display layer.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Payment(Base):
    """A payment attempt from a customer."""

    __tablename__ = "payments"

    id = Column(String, primary_key=True)                    # pay_XXXXXXXXXX
    customer_id = Column(String, nullable=False)             # cust_XXXXXXXX
    merchant_id = Column(String, nullable=False)             # merch_XXXX
    amount = Column(Integer, nullable=False)                 # paise
    currency = Column(String, default="INR")
    payment_method = Column(String, nullable=False)          # upi, card, netbanking, wallet, emandate
    status = Column(String, nullable=False)                  # failed, authorized, captured
    failure_reason = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    customer_email = Column(String, nullable=True)
    subscription_id = Column(String, nullable=True)
    is_recurring = Column(Boolean, default=False)
    previous_success_count = Column(Integer, default=0)
    previous_failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    # Hidden synthetic ground-truth fields for independent evaluation
    # WARNING: These fields must NEVER be sent to the LLM.
    ground_truth_recoverable = Column(Boolean, nullable=True)
    ground_truth_best_action = Column(String, nullable=True)
    ground_truth_recovery_probability = Column(Float, nullable=True)
    ground_truth_reason = Column(Text, nullable=True)


class RecoveryResult(Base):
    """Result of analyzing and attempting to recover a failed payment."""

    __tablename__ = "recovery_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(String, ForeignKey("payments.id"), nullable=False)
    batch_id = Column(String, nullable=False)
    ai_root_cause = Column(Text, nullable=True)
    ai_recommendation = Column(String, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    ai_is_recoverable = Column(Boolean, nullable=True)
    is_llm_generated = Column(Boolean, default=False)        # True only if response came from Gemini LLM
    policy_decision = Column(String, nullable=True)          # approved, blocked, escalated
    policy_reasons = Column(Text, nullable=True)             # JSON array of rule names
    action_taken = Column(String, nullable=True)
    recovery_successful = Column(Boolean, nullable=True)
    amount_recovered = Column(Integer, default=0)            # paise
    created_at = Column(DateTime, server_default=func.now())


class AuditLog(Base):
    """Immutable audit trail entry for every significant action."""

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String, nullable=True)
    payment_id = Column(String, ForeignKey("payments.id"), nullable=True)
    event_type = Column(String, nullable=False)              # ai_analysis, policy_check, action_executed, action_blocked, escalated
    details = Column(Text, nullable=True)                    # JSON blob
    created_at = Column(DateTime, server_default=func.now())


class BatchRun(Base):
    """Record of a batch processing run with aggregate metrics."""

    __tablename__ = "batch_runs"

    id = Column(String, primary_key=True)                    # batch_XXXXXXXXXX
    status = Column(String, default="running")               # running, completed, failed
    total_payments = Column(Integer, default=0)
    total_at_risk = Column(Integer, default=0)               # paise (analyzed failed payments)
    ground_truth_recoverable_revenue = Column(Integer, default=0)  # paise (ground truth)
    ai_predicted_recoverable_revenue = Column(Integer, default=0)  # paise (AI predicted)
    total_recoverable = Column(Integer, default=0)           # alias for backwards compatibility
    total_recovered = Column(Integer, default=0)             # paise (actually recovered)
    recovery_rate = Column(Float, default=0.0)               # recovered / at_risk * 100
    recovery_efficiency = Column(Float, default=0.0)         # recovered / ground_truth_recoverable * 100
    approved_count = Column(Integer, default=0)
    blocked_count = Column(Integer, default=0)
    escalated_count = Column(Integer, default=0)
    successful_recovery_count = Column(Integer, default=0)
    
    # Full Pipeline Metrics
    ai_precision = Column(Float, default=0.0)                # AI recoverability precision (%)
    ai_recall = Column(Float, default=0.0)                   # AI recoverability recall (%)
    ai_f1 = Column(Float, default=0.0)                       # AI recoverability F1 score (%)
    intervention_accuracy = Column(Float, default=0.0)       # AI rec == GT best action (%)
    approved_action_success_rate = Column(Float, default=0.0) # success / approved (%)
    policy_block_rate = Column(Float, default=0.0)           # blocked / total (%)
    escalation_rate = Column(Float, default=0.0)             # escalated / total (%)

    # Gemini LLM-Specific Metrics (is_llm_generated == True subset)
    llm_analyzed_count = Column(Integer, default=0)
    heuristic_fallback_count = Column(Integer, default=0)
    llm_precision = Column(Float, default=0.0)
    llm_recall = Column(Float, default=0.0)
    llm_f1 = Column(Float, default=0.0)
    llm_intervention_accuracy = Column(Float, default=0.0)

    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
