"""
AI Engine for RecoverAI.

This module integrates with Google Gemini API to diagnose failed payments
and recommend recovery interventions.

ARCHITECTURAL PRINCIPLES & BOUNDARIES:
1. ADVISORY ONLY: The AI engine acts strictly as an advisory recommender.
   The LLM output does NOT directly trigger financial movement or bypass rules.
2. DETERMINISTIC POLICIES GOVERN: The deterministic policy engine validates
   and may override or block any AI recommendation.
3. GROUND TRUTH ISOLATION: Internal synthetic ground truth metadata
   (ground_truth_recoverable, ground_truth_best_action, etc.) is NEVER passed
   to the LLM prompt.
4. CONFIDENCE NOT CALIBRATED: The `confidence` value is the model's self-reported
   certainty score (0.0 - 1.0), not a statistically calibrated probability.
"""

from __future__ import annotations

import json
import logging
import re
import time
import traceback
from typing import Optional

from google import genai
from google.genai import types

from app.config import Settings, get_settings
from app.models import Payment
from app.schemas import AIRecommendation

logger = logging.getLogger(__name__)

# Lazily initialized Gemini client
_client: Optional[genai.Client] = None
_cached_api_key: Optional[str] = None
_last_gemini_call_time: float = 0.0
_daily_exhausted_models: set[str] = set()


def _enforce_rate_limit(min_delay: float = 2.0) -> None:
    """Enforce minimum spacing between live Gemini API calls to respect RPM quotas."""
    global _last_gemini_call_time
    if min_delay <= 0:
        return
    now = time.time()
    elapsed = now - _last_gemini_call_time
    if elapsed < min_delay:
        sleep_time = min_delay - elapsed
        time.sleep(sleep_time)
    _last_gemini_call_time = time.time()


def _extract_retry_delay(err: Exception) -> Optional[float]:
    """Extract recommended retry delay from API error if provided by Google RPC."""
    err_str = str(err)
    match = re.search(r"retryDelay['\":\s]+(\d+)s", err_str, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, IndexError):
            pass
    match_sec = re.search(r"retry in (\d+(\.\d+)?)s", err_str, re.IGNORECASE)
    if match_sec:
        try:
            return float(match_sec.group(1))
        except (ValueError, IndexError):
            pass
    return None


def get_client(settings: Optional[Settings] = None) -> genai.Client:
    """
    Get or create the Gemini client.
    
    Args:
        settings: Application settings. If not provided, will be fetched via get_settings().
        
    Returns:
        Configured genai.Client instance.
    """
    global _client, _cached_api_key
    if settings is None:
        settings = get_settings()

    if _client is not None and _cached_api_key == settings.gemini_api_key:
        return _client

    _client = genai.Client(api_key=settings.gemini_api_key)
    _cached_api_key = settings.gemini_api_key
    return _client


def heuristic_diagnose(payment: Payment) -> AIRecommendation:
    """
    Deterministic rule-based baseline diagnostic fallback.
    
    Used when Gemini API key is not configured or in offline test environments.
    Simulates standard payment routing heuristics without external API calls.
    """
    reason = payment.failure_reason or "unknown"
    method = payment.payment_method or "upi"
    has_email = payment.customer_email is not None and payment.customer_email.strip() != ""

    # Deterministic demo scenario baselines
    if payment.id == "pay_demo_max_retries":
        return AIRecommendation(
            root_cause="Transient technical glitch on upi (upi_timeout)",
            recommendation="retry_payment",
            confidence=0.80,
            explanation="AI suggests direct retry despite retry count.",
            is_recoverable=True,
        )
    if payment.id == "pay_demo_no_email":
        return AIRecommendation(
            root_cause="Card expired and requires fresh payment link",
            recommendation="send_payment_link",
            confidence=0.75,
            explanation="AI suggests sending payment link to update card details.",
            is_recoverable=True,
        )
    if payment.id == "pay_demo_low_conf":
        return AIRecommendation(
            root_cause="Uncertain decline reason",
            recommendation="retry_payment",
            confidence=0.45,
            explanation="Model uncertain of root cause.",
            is_recoverable=True,
        )

    if reason in ("upi_timeout", "bank_server_down", "session_timeout"):
        if (payment.retry_count or 0) < 3:
            return AIRecommendation(
                root_cause=f"Transient technical glitch on {method} ({reason})",
                recommendation="retry_payment",
                confidence=0.85,
                explanation=f"Transient network error. Direct retry via {method} has high recovery likelihood.",
                is_recoverable=True,
            )
        elif has_email:
            return AIRecommendation(
                root_cause=f"Persistent technical failure on {method} after multiple retries",
                recommendation="send_payment_link",
                confidence=0.75,
                explanation="Max retries reached on automated channel. Switching to customer payment link.",
                is_recoverable=True,
            )
        else:
            return AIRecommendation(
                root_cause="Persistent technical failure with no customer email",
                recommendation="escalate_to_human",
                confidence=0.45,
                explanation="Automated retries failed and no contact channel available.",
                is_recoverable=False,
            )

    if reason in ("card_expired", "account_closed", "fraud_suspected", "mandate_revoked"):
        if reason == "fraud_suspected":
            return AIRecommendation(
                root_cause="Potential security or fraud flag detected",
                recommendation="do_not_retry",
                confidence=0.90,
                explanation="Security risk detected. Recovery retry blocked for merchant protection.",
                is_recoverable=False,
            )
        if reason == "card_expired" and has_email:
            return AIRecommendation(
                root_cause="Card instrument expired",
                recommendation="send_payment_link",
                confidence=0.80,
                explanation="Card expired. Sending payment link allows customer to enter new card details.",
                is_recoverable=True,
            )
        return AIRecommendation(
            root_cause=f"Permanent payment instrument failure ({reason})",
            recommendation="do_not_retry",
            confidence=0.85,
            explanation=f"Failure reason {reason} is non-recoverable via automated retry.",
            is_recoverable=False,
        )

    if reason == "insufficient_funds":
        if (payment.previous_success_count or 0) >= 3 and has_email:
            return AIRecommendation(
                root_cause="Temporary balance shortage for active customer",
                recommendation="send_reminder",
                confidence=0.75,
                explanation="Customer has strong history. Gentle reminder will prompt account replenishment.",
                is_recoverable=True,
            )
        elif has_email:
            return AIRecommendation(
                root_cause="Insufficient account funds",
                recommendation="send_payment_link",
                confidence=0.65,
                explanation="Sending payment link gives customer flexibility to pay once balance is available.",
                is_recoverable=True,
            )
        return AIRecommendation(
            root_cause="Insufficient account balance with no contact email",
            recommendation="do_not_retry",
            confidence=0.50,
            explanation="Insufficient funds and no customer communication channel.",
            is_recoverable=False,
        )

    # General fallback
    if has_email:
        return AIRecommendation(
            root_cause=f"Payment declined ({reason})",
            recommendation="send_payment_link",
            confidence=0.60,
            explanation="General decline. Payment link provides alternative payment avenues.",
            is_recoverable=True,
        )
    return AIRecommendation(
        root_cause=f"Payment declined ({reason})",
        recommendation="escalate_to_human",
        confidence=0.40,
        explanation="Unable to automatically resolve decline without customer contact information.",
        is_recoverable=False,
    )


def analyze_payment_with_source(payment: Payment, settings: Optional[Settings] = None) -> tuple[AIRecommendation, bool]:
    """
    Analyze a failed payment and return (recommendation, is_llm_generated).
    
    is_llm_generated is strictly True only when the response was successfully
    generated by the live Gemini LLM for THIS specific payment.
    
    If Gemini fails, times out, or is rate-limited after exponential backoff,
    it falls back immediately and exclusively for this payment to the deterministic
    heuristic engine, with is_llm_generated=False.
    """
    if settings is None:
        settings = get_settings()

    # If API key is not configured, fall back to the deterministic heuristic engine
    if not settings.gemini_api_key or settings.gemini_api_key.strip() == "" or settings.gemini_api_key.startswith("your_"):
        logger.info(f"Gemini API key not configured. Using deterministic diagnostic engine for payment {payment.id}")
        return heuristic_diagnose(payment), False

    # Deterministic demo scenarios for policy engine showcase
    if payment.id in ("pay_demo_max_retries", "pay_demo_no_email", "pay_demo_low_conf"):
        return heuristic_diagnose(payment), False

    client = get_client(settings)

    prompt = f"""You are a payment recovery analyst for an Indian payment gateway (similar to Razorpay).

Analyze this failed payment and recommend a recovery action.

PAYMENT DATA:
- Payment ID: {payment.id}
- Amount: ₹{payment.amount / 100:.2f}
- Payment Method: {payment.payment_method}
- Failure Reason: {payment.failure_reason}
- Retry Count: {payment.retry_count}
- Is Recurring: {payment.is_recurring}
- Subscription ID: {payment.subscription_id or 'None'}
- Customer Email Available: {'Yes' if payment.customer_email else 'No'}
- Previous Successful Payments: {payment.previous_success_count}
- Previous Failed Payments: {payment.previous_failure_count}

AVAILABLE INTERVENTIONS:
- retry_payment: Retry the same payment method (best for transient errors like timeouts or temporary server issues)
- send_payment_link: Send a new payment link to the customer via email (best when the original method won't work)
- send_reminder: Send a gentle reminder to the customer (best for temporary issues where customer action is needed)
- offer_alternative_method: Suggest a different payment method (best when the current method has persistent issues)
- escalate_to_human: Flag for human review (when the situation is complex or high-risk)
- do_not_retry: Do not attempt recovery (when recovery is unlikely or inappropriate)

Consider:
1. The failure reason and whether it's transient or permanent
2. The customer's payment history (success vs failure ratio)
3. Whether the payment is recurring/subscription
4. The retry count so far
5. Available contact methods

Provide your analysis as a JSON object.
"""

    response_schema = {
        "type": "object",
        "properties": {
            "root_cause": {"type": "string"},
            "recommendation": {
                "type": "string",
                "enum": [
                    "retry_payment",
                    "send_payment_link",
                    "send_reminder",
                    "offer_alternative_method",
                    "escalate_to_human",
                    "do_not_retry"
                ]
            },
            "confidence": {"type": "number"},
            "explanation": {"type": "string"},
            "is_recoverable": {"type": "boolean"}
        },
        "required": ["root_cause", "recommendation", "confidence", "explanation", "is_recoverable"]
    }

    max_retries = getattr(settings, "gemini_max_retries", 2)
    rate_delay = getattr(settings, "gemini_rate_limit_delay", 2.0)

    global _daily_exhausted_models
    # Models to attempt: primary model first (if not daily-exhausted), fallback model if API rejects primary
    candidate_models = [m for m in [settings.gemini_model, "gemini-3.5-flash-lite"] if m not in _daily_exhausted_models]
    if not candidate_models:
        candidate_models = ["gemini-3.5-flash-lite"]

    last_exception = None

    for model_name in candidate_models:
        for attempt in range(max_retries + 1):
            try:
                _enforce_rate_limit(rate_delay)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema
                    )
                )
                
                result_dict = json.loads(response.text)
                return AIRecommendation(**result_dict), True

            except Exception as e:
                last_exception = e
                err_str = str(e).lower()
                is_rate_limit = "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str
                is_daily_exhaustion = "perday" in err_str or "per_day" in err_str or "limit: 20" in err_str
                
                # If primary model has daily quota exhausted, record it and immediately try fallback model
                if is_daily_exhaustion:
                    _daily_exhausted_models.add(model_name)
                    if model_name != candidate_models[-1]:
                        logger.warning(
                            f"Gemini model {model_name} daily quota exhausted for payment {payment.id}. "
                            f"Recording exclusion and attempting fallback model."
                        )
                        break

                if is_rate_limit and attempt < max_retries:
                    extracted = _extract_retry_delay(e)
                    if extracted and extracted > 10.0:
                        logger.warning(
                            f"Gemini requested long cooldown of {extracted:.1f}s for payment {payment.id}. "
                            f"Falling back to heuristic to prevent batch stalling."
                        )
                        break
                    retry_delay = min(5.0, extracted or (2.0 * (2 ** attempt)))
                    logger.warning(
                        f"Gemini 429 rate limit on payment {payment.id} using {model_name} "
                        f"(attempt {attempt+1}/{max_retries+1}). Retrying in {retry_delay:.1f}s..."
                    )
                    time.sleep(retry_delay)
                    continue
                
                # For non-rate-limit errors or if final attempt for this model
                logger.warning(
                    f"Gemini call attempt {attempt+1} failed with {model_name} for payment {payment.id}: {e}"
                )
                break  # try next candidate model or fallback to heuristic

    logger.warning(
        f"Gemini API unavailable for payment {payment.id} after retries ({last_exception}). "
        f"Falling back to deterministic heuristic diagnostic for this payment."
    )
    return heuristic_diagnose(payment), False


def analyze_payment(payment: Payment, settings: Optional[Settings] = None) -> AIRecommendation:
    """
    Analyze a failed payment and recommend a recovery action using Gemini 3.5 Flash.
    
    GROUND TRUTH ISOLATION:
    Notice that only payment.id, amount, payment_method, failure_reason, retry_count,
    is_recurring, subscription_id, customer_email, and customer history counts
    are provided. `ground_truth_*` fields are strictly excluded.
    
    Args:
        payment: The Payment ORM model instance to analyze.
        settings: Application settings. If not provided, will be fetched via get_settings().
        
    Returns:
        AIRecommendation containing root cause, recommendation enum, AI confidence,
        explanation, and is_recoverable boolean flag.
    """
    rec, _ = analyze_payment_with_source(payment, settings)
    return rec
