"""
Recovery Simulator for RecoverAI.

This module simulates the financial outcome of recommended recovery interventions
using a stable, reproducible SHA-256 PRNG seed.

KEY ARCHITECTURAL INVARIANTS:
1. INDEPENDENT SIMULATION: This module NEVER inspects or reads `ground_truth_*` fields.
   It evaluates outcomes purely as a function of (payment, action).
2. REALISTIC DOMAIN CONSISTENCY: Synthetic payment constraints (e.g. missing contact email
   for email-based links, permanent fraud flags, closed accounts) yield 0% success probability
   across all actions, ensuring non-recoverable transactions never recover money.
3. REPRODUCIBILITY: The seed is derived from `SHA-256(payment_id:action)` ensuring
   identical outcomes across interpreter restarts and platforms.
"""

from __future__ import annotations

import hashlib
import logging
import random
from dataclasses import dataclass

from app.models import Payment

logger = logging.getLogger(__name__)


@dataclass
class RecoveryOutcome:
    """Represents the outcome of a simulated recovery action."""
    success: bool
    amount_recovered: int
    details: str


def _get_stable_seed(payment_id: str, action: str) -> int:
    """
    Generate a stable, cross-interpreter 64-bit integer seed using SHA-256.
    
    Python's built-in hash() uses SipHash with a randomized process seed (PYTHONHASHSEED),
    causing hash(payment.id) to differ across application restarts.
    Using SHA-256 guarantees identical simulation outcomes across restarts and platforms.
    """
    key = f"{payment_id}:{action}".encode("utf-8")
    digest = hashlib.sha256(key).digest()
    return int.from_bytes(digest[:8], byteorder="big")


def simulate_recovery(payment: Payment, action: str) -> RecoveryOutcome:
    """
    Simulates the outcome of a recovery action based on payment characteristics
    and deterministic probability using a stable SHA-256 seed.
    
    Args:
        payment: The failed Payment instance.
        action: The recommended action to simulate.
        
    Returns:
        RecoveryOutcome containing success status, amount recovered (in paise),
        and human-readable details.
    """
    amount_inr = payment.amount / 100.0 if payment.amount else 0.0

    # 1. Non-execution actions (handoffs / no-ops) never recover revenue
    if action in ("escalate_to_human", "do_not_retry"):
        return RecoveryOutcome(
            success=False,
            amount_recovered=0,
            details=f"No recovery attempted — action is '{action}'"
        )

    # 2. Hard permanent failure constraints across all recovery actions
    permanent_all_actions = {
        "fraud_suspected",
        "account_closed",
        "subscription_cancelled",
    }
    if payment.failure_reason in permanent_all_actions:
        return RecoveryOutcome(
            success=False,
            amount_recovered=0,
            details=f"Recovery impossible: payment failure reason '{payment.failure_reason}' is permanently non-recoverable."
        )

    # 3. Communication actions strictly require a customer contact channel
    has_email = payment.customer_email is not None and payment.customer_email.strip() != ""
    if action in ("send_payment_link", "send_reminder", "offer_alternative_method") and not has_email:
        return RecoveryOutcome(
            success=False,
            amount_recovered=0,
            details=f"Action '{action}' failed: customer email is missing and cannot be delivered."
        )

    # Seed PRNG
    seed = _get_stable_seed(payment.id, action)
    rng = random.Random(seed)

    prob = 0.0

    if action == "retry_payment":
        # Guaranteed Demo Case A override
        if payment.id == "pay_demo_happy_path":
            return RecoveryOutcome(
                success=True,
                amount_recovered=payment.amount,
                details=f"Payment retry successful via {payment.payment_method} (Guaranteed Demo Case A). ₹{amount_inr:.2f} recovered."
            )

        # Non-retryable failure reasons on direct automated retry
        # (Require customer deposit, updated instrument, PIN, or payment link)
        non_retryable = {
            "card_expired",
            "mandate_revoked",
            "vpa_not_found",
            "wallet_blocked",
            "upi_pin_incorrect",
            "authentication_failed",
            "card_declined",
            "wallet_limit_exceeded",
            "insufficient_funds",
        }
        if payment.failure_reason in non_retryable:
            return RecoveryOutcome(
                success=False,
                amount_recovered=0,
                details=f"Payment retry failed: '{payment.failure_reason}' cannot succeed on direct automated retry without customer intervention."
            )

        # Exhausted retries or excessive failure history on direct retry
        retry_count = payment.retry_count or 0
        prev_failures = payment.previous_failure_count or 0
        if retry_count >= 3 or prev_failures >= 5:
            return RecoveryOutcome(
                success=False,
                amount_recovered=0,
                details=f"Payment retry failed: customer failure limits exceeded (retries={retry_count}, past_failures={prev_failures})."
            )

        # Transient network failure probability models
        failure_probs = {
            "upi_timeout": 0.70,
            "bank_server_down": 0.60,
            "session_timeout": 0.65,
        }
        prob = failure_probs.get(payment.failure_reason, 0.30)
        prob -= 0.15 * retry_count

        prob = max(0.0, min(1.0, prob))
        success = rng.random() < prob

        if success:
            return RecoveryOutcome(
                success=True,
                amount_recovered=payment.amount,
                details=f"Payment retry successful via {payment.payment_method}. ₹{amount_inr:.2f} recovered."
            )
        else:
            return RecoveryOutcome(
                success=False,
                amount_recovered=0,
                details=f"Payment retry failed. {payment.failure_reason} persists."
            )

    elif action == "send_payment_link":
        prob = 0.45
        if payment.previous_success_count and payment.previous_success_count > 5:
            prob += 0.15
        if payment.previous_failure_count and payment.previous_failure_count > 3:
            prob -= 0.10
        if payment.is_recurring:
            prob += 0.10

        prob = max(0.0, min(1.0, prob))
        success = rng.random() < prob

        if success:
            return RecoveryOutcome(
                success=True,
                amount_recovered=payment.amount,
                details=f"Customer completed payment via payment link. ₹{amount_inr:.2f} recovered."
            )
        else:
            return RecoveryOutcome(
                success=False,
                amount_recovered=0,
                details="Customer did not complete payment via link."
            )

    elif action == "send_reminder":
        prob = 0.25
        if payment.is_recurring:
            prob += 0.15
        if payment.previous_success_count and payment.previous_success_count > 10:
            prob += 0.10

        prob = max(0.0, min(1.0, prob))
        success = rng.random() < prob

        if success:
            return RecoveryOutcome(
                success=True,
                amount_recovered=payment.amount,
                details=f"Customer completed payment after reminder. ₹{amount_inr:.2f} recovered."
            )
        else:
            return RecoveryOutcome(
                success=False,
                amount_recovered=0,
                details="Customer ignored the reminder."
            )

    elif action == "offer_alternative_method":
        prob = 0.35
        card_failures = {"card_declined", "card_expired"}
        if payment.payment_method == "card" and payment.failure_reason in card_failures:
            prob += 0.10

        prob = max(0.0, min(1.0, prob))
        success = rng.random() < prob

        if success:
            return RecoveryOutcome(
                success=True,
                amount_recovered=payment.amount,
                details=f"Customer completed payment via alternative method. ₹{amount_inr:.2f} recovered."
            )
        else:
            return RecoveryOutcome(
                success=False,
                amount_recovered=0,
                details="Customer did not use the alternative payment method."
            )

    else:
        logger.warning(f"Unknown recovery action '{action}'")
        return RecoveryOutcome(
            success=False,
            amount_recovered=0,
            details=f"Simulation failed: unknown action '{action}'"
        )
