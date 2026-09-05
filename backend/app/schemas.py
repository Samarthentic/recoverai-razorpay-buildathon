"""
Pydantic schemas for API request/response validation.

These are separate from SQLAlchemy models to keep the API contract
independent of the database schema.
"""

from datetime import datetime
from pydantic import BaseModel


# ---------- Payment ----------

class PaymentOut(BaseModel):
    """Payment data returned by the API."""
    id: str
    customer_id: str
    merchant_id: str
    amount: int                     # paise
    currency: str
    payment_method: str
    status: str
    failure_reason: str | None = None
    retry_count: int
    customer_email: str | None = None
    subscription_id: str | None = None
    is_recurring: bool
    previous_success_count: int
    previous_failure_count: int
    created_at: datetime | None = None

    # Hidden synthetic ground truth (for evaluation/debugging, never sent to LLM)
    ground_truth_recoverable: bool | None = None
    ground_truth_best_action: str | None = None
    ground_truth_recovery_probability: float | None = None
    ground_truth_reason: str | None = None

    model_config = {"from_attributes": True}


# ---------- AI Analysis ----------

class AIRecommendation(BaseModel):
    """Structured output from the AI engine."""
    root_cause: str
    recommendation: str             # intervention enum
    confidence: float               # 0.0 - 1.0 (self-reported AI confidence, not calibrated probability)
    explanation: str
    is_recoverable: bool


# ---------- Policy ----------

class PolicyDecisionOut(BaseModel):
    """Result of the deterministic policy evaluation."""
    decision: str                   # approved, blocked, escalated
    triggered_rules: list[str]
    reasons: list[str]


# ---------- Recovery Result ----------

class RecoveryResultOut(BaseModel):
    """Full result of analyzing + attempting recovery on a payment."""
    payment_id: str
    batch_id: str
    ai_root_cause: str | None = None
    ai_recommendation: str | None = None
    ai_confidence: float | None = None
    ai_explanation: str | None = None
    ai_is_recoverable: bool | None = None
    is_llm_generated: bool = False
    policy_decision: str | None = None
    policy_reasons: list[str] | None = None
    action_taken: str | None = None
    recovery_successful: bool | None = None
    amount_recovered: int = 0
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------- Audit ----------

class AuditLogOut(BaseModel):
    """Single audit trail entry."""
    id: int
    batch_id: str | None = None
    payment_id: str | None = None
    event_type: str
    details: str | None = None      # JSON string
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------- Batch ----------

class BatchRunOut(BaseModel):
    """Batch run summary with comprehensive evaluation metrics."""
    id: str
    status: str
    total_payments: int
    total_at_risk: int                               # paise (all analyzed failed payments)
    ground_truth_recoverable_revenue: int = 0        # paise (ground truth)
    ai_predicted_recoverable_revenue: int = 0        # paise (AI predicted)
    total_recoverable: int = 0                       # alias for backwards compatibility
    total_recovered: int                             # paise (actually recovered)
    recovery_rate: float                             # recovered / at_risk * 100
    recovery_efficiency: float = 0.0                 # recovered / ground_truth_recoverable * 100
    approved_count: int
    blocked_count: int
    escalated_count: int
    successful_recovery_count: int = 0

    # Full Pipeline Metrics (all records)
    ai_precision: float = 0.0                        # AI recoverability precision (%)
    ai_recall: float = 0.0                           # AI recoverability recall (%)
    ai_f1: float = 0.0                               # AI recoverability F1 (%)
    intervention_accuracy: float = 0.0               # AI rec == GT best action (%)
    approved_action_success_rate: float = 0.0        # success / approved (%)
    policy_block_rate: float = 0.0                   # blocked / total (%)
    escalation_rate: float = 0.0                     # escalated / total (%)

    # Gemini LLM-Specific Metrics (records where is_llm_generated == True)
    llm_analyzed_count: int = 0
    heuristic_fallback_count: int = 0
    llm_precision: float = 0.0
    llm_recall: float = 0.0
    llm_f1: float = 0.0
    llm_intervention_accuracy: float = 0.0

    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------- Dashboard ----------

class DashboardStats(BaseModel):
    """Aggregated KPIs for the dashboard."""
    total_payments: int
    total_at_risk: int                               # paise
    ground_truth_recoverable_revenue: int = 0        # paise
    ai_predicted_recoverable_revenue: int = 0        # paise
    total_recoverable: int = 0                       # paise (backward compat)
    total_recovered: int                             # paise
    recovery_rate: float                             # percentage
    recovery_efficiency: float = 0.0                 # percentage
    approved_count: int
    blocked_count: int
    escalated_count: int
    successful_recovery_count: int = 0

    # Full Pipeline Metrics
    ai_precision: float = 0.0
    ai_recall: float = 0.0
    ai_f1: float = 0.0
    intervention_accuracy: float = 0.0
    approved_action_success_rate: float = 0.0
    policy_block_rate: float = 0.0
    escalation_rate: float = 0.0

    # Gemini LLM-Specific Metrics
    llm_analyzed_count: int = 0
    heuristic_fallback_count: int = 0
    llm_precision: float = 0.0
    llm_recall: float = 0.0
    llm_f1: float = 0.0
    llm_intervention_accuracy: float = 0.0

    batch_id: str | None = None


# ---------- Single Analysis ----------

class AnalysisResponse(BaseModel):
    """Response for analyzing a single payment."""
    payment: PaymentOut
    ai_recommendation: AIRecommendation
    policy_decision: PolicyDecisionOut
    action_taken: str
    recovery_successful: bool | None = None
    amount_recovered: int = 0


# ---------- System Status & Policy Controls ----------

class ComponentStatus(BaseModel):
    recovery_engine: str = "operational"
    policy_engine: str = "operational"
    gemini_analysis: str = "connected"  # connected | fallback_mode
    recovery_simulator: str = "operational"
    audit_logging: str = "operational"


class AIConfigOut(BaseModel):
    model: str
    batch_limit: int
    fallback_enabled: bool = True
    safety_architecture: str = "Policy-Gated Deterministic Authority"
    ground_truth_isolation: str = "Enabled (Hidden from LLM Prompt)"
    gemini_configured: bool


class PolicyConfigOut(BaseModel):
    max_retries: int
    high_value_threshold: int
    confidence_threshold: float
    customer_failure_limit: int
    max_auto_recovery_amount: int
    non_retryable_reasons: list[str]
    decision_authority: str = "Deterministic Policy Governor"


class SystemStatusOut(BaseModel):
    service: str = "RecoverAI"
    status: str = "operational"
    components: ComponentStatus
    ai_configuration: AIConfigOut
    policy_configuration: PolicyConfigOut

