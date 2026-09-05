"""
Deterministic Policy Engine for RecoverAI.

CRITICAL ARCHITECTURAL BOUNDARY:
- AI RECOMMENDS; DETERMINISTIC CODE CONTROLS.
- The LLM is NEVER authoritative for financial amounts, retry limits, permission checks,
  or monetary thresholds.
- This engine reads authoritative values directly from the database record (Payment model),
  completely ignoring any claims about amounts or limits that might originate in LLM text.
- This engine is a pure, side-effect-free deterministic function with ZERO external API
  or LLM dependencies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.config import Settings
from app.models import Payment
from app.schemas import AIRecommendation

logger = logging.getLogger(__name__)


@dataclass
class PolicyConfig:
    """Configuration for the deterministic policy engine."""
    max_retries: int = 3
    high_value_threshold: int = 5_000_000
    confidence_threshold: float = 0.6
    customer_failure_limit: int = 5
    max_auto_recovery_amount: int = 10_000_000
    non_retryable_reasons: list[str] = field(
        default_factory=lambda: ["card_expired", "account_closed", "fraud_suspected"]
    )


@dataclass
class PolicyDecision:
    """Result of policy evaluation."""
    decision: str
    triggered_rules: list[str]
    reasons: list[str]


def create_policy_config_from_settings(settings: Settings) -> PolicyConfig:
    """Creates a PolicyConfig from the application Settings."""
    return PolicyConfig(
        max_retries=settings.max_retries,
        high_value_threshold=settings.high_value_threshold,
        confidence_threshold=settings.confidence_threshold,
        customer_failure_limit=settings.customer_failure_limit,
        max_auto_recovery_amount=settings.max_auto_recovery_amount,
        non_retryable_reasons=settings.non_retryable_reasons,
    )


def evaluate_policy(
    payment: Payment,
    recommendation: AIRecommendation,
    config: PolicyConfig | None = None,
) -> PolicyDecision:
    """
    Evaluates the payment and AI recommendation against deterministic business rules.
    Returns a final decision (approved, blocked, escalated) with reasons.
    """
    if config is None:
        config = PolicyConfig()

    triggered_rules: list[str] = []
    reasons: list[str] = []

    is_blocked = False
    is_escalated = False

    # 1. max_retry_exceeded
    if payment.retry_count is not None and payment.retry_count >= config.max_retries and recommendation.recommendation == "retry_payment":
        triggered_rules.append("max_retry_exceeded")
        reasons.append(f"Payment has been retried {payment.retry_count} times (max: {config.max_retries})")
        is_blocked = True

    # 2. high_value_human_review
    if payment.amount is not None and payment.amount > config.high_value_threshold and recommendation.recommendation not in ("escalate_to_human", "do_not_retry"):
        triggered_rules.append("high_value_human_review")
        reasons.append(f"High-value payment (₹{payment.amount/100:.2f}) requires human review (threshold: ₹{config.high_value_threshold/100:.2f})")
        is_escalated = True

    # 3. low_confidence_escalate
    if recommendation.confidence is not None and recommendation.confidence < config.confidence_threshold:
        triggered_rules.append("low_confidence_escalate")
        reasons.append(f"AI confidence ({recommendation.confidence:.2f}) below threshold ({config.confidence_threshold})")
        is_escalated = True

    # 4. repeated_customer_failure
    if payment.previous_failure_count is not None and payment.previous_failure_count >= config.customer_failure_limit and recommendation.recommendation == "retry_payment":
        triggered_rules.append("repeated_customer_failure")
        reasons.append(f"Customer has {payment.previous_failure_count} previous failures (limit: {config.customer_failure_limit})")
        is_blocked = True

    # 5. invalid_action_for_reason
    if recommendation.recommendation == "retry_payment" and payment.failure_reason in config.non_retryable_reasons:
        triggered_rules.append("invalid_action_for_reason")
        reasons.append(f"Cannot retry: failure reason '{payment.failure_reason}' is non-retryable")
        is_blocked = True

    # 6. missing_contact_info
    if recommendation.recommendation in ("send_payment_link", "send_reminder") and payment.customer_email is None:
        triggered_rules.append("missing_contact_info")
        reasons.append("Cannot send communication: customer email is missing")
        is_blocked = True

    # 7. subscription_cancelled
    if payment.subscription_id is not None and payment.failure_reason == "subscription_cancelled":
        triggered_rules.append("subscription_cancelled")
        reasons.append("Subscription has been cancelled by customer — respecting cancellation")
        is_blocked = True

    # 8. amount_cap
    if payment.amount is not None and payment.amount > config.max_auto_recovery_amount:
        triggered_rules.append("amount_cap")
        reasons.append(f"Payment amount (₹{payment.amount/100:.2f}) exceeds auto-recovery cap (₹{config.max_auto_recovery_amount/100:.2f})")
        is_escalated = True

    # Decide final outcome
    if is_blocked:
        decision = "blocked"
    elif is_escalated:
        decision = "escalated"
    else:
        decision = "approved"

    logger.debug(
        "Policy evaluation for payment %s: decision=%s, triggered_rules=%s",
        payment.id,
        decision,
        triggered_rules,
    )

    return PolicyDecision(
        decision=decision,
        triggered_rules=triggered_rules,
        reasons=reasons,
    )
