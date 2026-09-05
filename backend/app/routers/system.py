"""
System status and policy configuration router.

Provides read-only operational telemetry and active deterministic policy
thresholds for the RecoverAI operations console.
"""

from fastapi import APIRouter
from app.config import get_settings
from app.schemas import SystemStatusOut, ComponentStatus, AIConfigOut, PolicyConfigOut

router = APIRouter()


@router.get("/system/status", response_model=SystemStatusOut)
def get_system_status():
    """Return operational component health and active policy configurations."""
    settings = get_settings()
    has_gemini = bool(settings.gemini_api_key and settings.gemini_api_key.strip())

    return SystemStatusOut(
        service="RecoverAI",
        status="operational",
        components=ComponentStatus(
            recovery_engine="operational",
            policy_engine="operational",
            gemini_analysis="connected" if has_gemini else "fallback_mode",
            recovery_simulator="operational",
            audit_logging="operational",
        ),
        ai_configuration=AIConfigOut(
            model=settings.gemini_model,
            batch_limit=settings.ai_batch_limit,
            fallback_enabled=True,
            safety_architecture="Policy-Gated Deterministic Authority",
            ground_truth_isolation="Enabled (Hidden from LLM Prompt)",
            gemini_configured=has_gemini,
        ),
        policy_configuration=PolicyConfigOut(
            max_retries=settings.max_retries,
            high_value_threshold=settings.high_value_threshold,
            confidence_threshold=settings.confidence_threshold,
            customer_failure_limit=settings.customer_failure_limit,
            max_auto_recovery_amount=settings.max_auto_recovery_amount,
            non_retryable_reasons=settings.non_retryable_reasons,
            decision_authority="Deterministic Policy Governor",
        ),
    )
