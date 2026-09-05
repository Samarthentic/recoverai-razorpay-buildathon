"""
Synthetic payment data generator with deterministic ground truth.

This module generates realistic synthetic Indian payment events with hidden
ground-truth evaluation metadata.

KEY ARCHITECTURAL BOUNDARY:
The ground-truth fields (`ground_truth_recoverable`, `ground_truth_best_action`,
`ground_truth_recovery_probability`, `ground_truth_reason`) represent the objective
synthetic-world truth. They are stored in the database for post-hoc evaluation
and MUST NEVER be passed to the LLM prompt.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.database import engine
from app.models import Base, Payment


def compute_ground_truth(payment_data: dict[str, Any] | Payment) -> tuple[bool, str, float, str]:
    """
    Computes deterministic ground-truth recovery labels for a payment.
    
    This acts as an independent evaluation target for benchmarking AI accuracy,
    precision, recall, and recovery efficiency.
    
    Rules:
    - Fraud suspected / closed account / customer cancelled subscription -> NOT recoverable (do_not_retry)
    - Card expired / mandate revoked -> Recoverable IF customer email exists (send_payment_link / offer_alternative_method)
    - Transient network timeouts (UPI, Netbanking, Server Down) -> High recovery probability via retry if retry_count < 3
    - Insufficient funds -> Conditionally recoverable via reminder (for established customers) or payment link
    - User input errors (PIN / Auth) -> Recoverable via fresh payment link if email available
    
    Returns:
        tuple of (ground_truth_recoverable, ground_truth_best_action, ground_truth_recovery_probability, ground_truth_reason)
    """
    def _get(attr: str, default: Any = None) -> Any:
        if isinstance(payment_data, dict):
            return payment_data.get(attr, default)
        return getattr(payment_data, attr, default)

    method = _get("payment_method", "upi")
    reason = _get("failure_reason", "unknown")
    retry_count = _get("retry_count", 0) or 0
    email = _get("customer_email")
    is_recurring = _get("is_recurring", False)
    sub_id = _get("subscription_id")
    prev_success = _get("previous_success_count", 0) or 0
    prev_failure = _get("previous_failure_count", 0) or 0

    has_contact = email is not None and str(email).strip() != ""

    # 1. Unrecoverable permanent failures
    if reason == "fraud_suspected":
        return False, "do_not_retry", 0.0, "High risk security and fraud flag; payment blocked permanently"

    if reason == "account_closed":
        return False, "do_not_retry", 0.0, "Customer bank account closed permanently"

    if reason == "subscription_cancelled" or (sub_id is not None and reason == "mandate_revoked" and not is_recurring):
        return False, "do_not_retry", 0.0, "Subscription cancelled by customer; respecting intent"

    # 2. Method-specific permanent failure requiring channel switch / fresh link
    if reason == "card_expired":
        if has_contact:
            return True, "send_payment_link", 0.55, "Card expired; customer can provide updated card or alternate method via link"
        return False, "do_not_retry", 0.0, "Card expired and customer has no contact channel"

    if reason == "mandate_revoked":
        if has_contact:
            return True, "send_payment_link", 0.40, "Mandate revoked; manual payment link required"
        return False, "do_not_retry", 0.0, "Mandate revoked and customer has no contact email"

    if reason == "vpa_not_found":
        if has_contact:
            return True, "offer_alternative_method", 0.45, "UPI VPA inactive; customer needs alternate payment method"
        return False, "do_not_retry", 0.0, "Invalid VPA and no contact email"

    if reason == "wallet_blocked":
        if has_contact:
            return True, "offer_alternative_method", 0.40, "Wallet blocked; customer must use card/UPI"
        return False, "do_not_retry", 0.0, "Blocked wallet and no contact email"

    # 3. Transient technical failures (Timeouts, Server Down)
    if reason in ("upi_timeout", "bank_server_down", "session_timeout"):
        if retry_count < 3 and prev_failure < 5:
            return True, "retry_payment", 0.70, "Transient gateway/bank network glitch; direct retry highly viable"
        elif has_contact:
            return True, "send_payment_link", 0.50, "Direct retries exhausted for transient issue; link offered as backup"
        else:
            return False, "do_not_retry", 0.0, "Retries exhausted and no contact email available"

    # 4. Insufficient funds
    if reason == "insufficient_funds":
        if prev_success >= 3 and prev_failure <= 2 and has_contact:
            return True, "send_reminder", 0.45, "Established customer with temporary cashflow issue; gentle reminder effective"
        elif has_contact:
            return True, "send_payment_link", 0.35, "Customer has insufficient funds; payment link gives grace period to add balance"
        else:
            return False, "do_not_retry", 0.0, "Insufficient funds and no customer contact method available"

    # 5. User authentication / PIN errors
    if reason in ("upi_pin_incorrect", "authentication_failed", "card_declined"):
        if has_contact:
            return True, "send_payment_link", 0.50, "User authentication or PIN error; sending fresh payment link enables clean retry"
        return False, "do_not_retry", 0.0, "Authentication failed and no contact method available"

    if reason == "wallet_limit_exceeded":
        if has_contact:
            return True, "offer_alternative_method", 0.40, "Wallet spending limit exceeded; alternate payment method recommended"
        return False, "do_not_retry", 0.0, "Wallet limit exceeded and no email contact"

    # Default fallback
    if retry_count < 3:
        return True, "retry_payment", 0.30, "Unclassified transient failure; single bounded retry attempted"
    return False, "do_not_retry", 0.0, "Retries exhausted without resolution"


def clear_database(db: Session) -> None:
    """Delete and recreate all tables in the database."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db.commit()


def generate_payments(db: Session, count: int = 500, seed: int = 42) -> list[Payment]:
    """
    Generate reproducible synthetic Indian payment events and insert them into the DB.
    
    Includes:
    - 5 Core Demo Scenarios (Cases A-E)
    - 15 Extended Deterministic Edge Cases
    - `count` Randomized payments generated with stable PRNG seed.
    
    Args:
        db: SQLAlchemy session
        count: Number of randomized payments (in addition to the 20 deterministic cases)
        seed: Random seed for 100% reproducible generation
        
    Returns:
        List of generated Payment objects
    """
    rng = random.Random(seed)
    payments: list[Payment] = []
    
    # Pre-generate deterministic customer IDs
    customer_ids = [f"cust_syn_{i:03d}" for i in range(100)]
    merchant_ids = ["merch_razorshop", "merch_quickbuy", "merch_payeasy", "merch_shopcart", "merch_billpay"]
    
    # Fixed base timestamp for total reproducibility across calendar days
    base_time = datetime(2026, 8, 25, 12, 0, 0)
    
    # -------------------------------------------------------------------------
    # 20 DETERMINISTIC DEMO & EDGE CASES (Cases A-E + Edge 06-20)
    # -------------------------------------------------------------------------
    edge_cases_config = [
        # CASE A: APPROVED HAPPY PATH
        {
            "id": "pay_demo_happy_path",
            "amount": 50000,  # ₹500
            "payment_method": "upi",
            "failure_reason": "upi_timeout",
            "retry_count": 0,
            "customer_email": "demo_happy@example.com",
            "previous_success_count": 8,
            "previous_failure_count": 0,
        },
        # CASE B: POLICY BLOCK (Max retries exceeded)
        {
            "id": "pay_demo_max_retries",
            "amount": 250000,  # ₹2,500
            "payment_method": "upi",
            "failure_reason": "upi_timeout",
            "retry_count": 4,  # > max 3
            "customer_email": "demo_max_retry@example.com",
            "previous_success_count": 10,
            "previous_failure_count": 0,
        },
        # CASE C: HIGH VALUE ESCALATION
        {
            "id": "pay_demo_high_value",
            "amount": 7500000,  # ₹75,000 (> ₹50,000 threshold)
            "payment_method": "card",
            "failure_reason": "insufficient_funds",
            "retry_count": 0,
            "customer_email": "demo_high_value@example.com",
            "previous_success_count": 5,
            "previous_failure_count": 1,
        },
        # CASE D: MISSING CONTACT BLOCK
        {
            "id": "pay_demo_no_email",
            "amount": 300000,  # ₹3,000
            "payment_method": "card",
            "failure_reason": "card_expired",
            "retry_count": 0,
            "customer_email": None,  # Missing email
            "previous_success_count": 2,
            "previous_failure_count": 0,
        },
        # CASE E: LOW CONFIDENCE ESCALATION / CUSTOMER CONFLICT
        {
            "id": "pay_demo_low_conf",
            "amount": 200000,  # ₹2,000
            "payment_method": "netbanking",
            "failure_reason": "session_timeout",
            "retry_count": 1,
            "customer_email": "demo_low_conf@example.com",
            "previous_success_count": 1,
            "previous_failure_count": 4,
        },
        # Edge 06: Repeated customer failure -> Policy Blocks retry
        {
            "id": "pay_edge_006_repeat_fail",
            "amount": 150000,
            "payment_method": "card",
            "failure_reason": "card_declined",
            "retry_count": 1,
            "previous_failure_count": 8,  # > limit 5
            "customer_email": "edge_repeat@example.com",
            "previous_success_count": 0,
        },
        # Edge 07: Cancelled Subscription -> Policy Blocks retry
        {
            "id": "pay_edge_007_sub_cancelled",
            "amount": 99900,
            "payment_method": "emandate",
            "failure_reason": "subscription_cancelled",
            "is_recurring": True,
            "subscription_id": "sub_edge_007",
            "retry_count": 0,
            "customer_email": "edge_sub@example.com",
            "previous_success_count": 12,
            "previous_failure_count": 0,
        },
        # Edge 08: Amount Cap Exceeded -> Escalated
        {
            "id": "pay_edge_008_amount_cap",
            "amount": 12000000,  # ₹1,20,000 (> ₹1,00,000 cap)
            "payment_method": "netbanking",
            "failure_reason": "bank_server_down",
            "retry_count": 0,
            "customer_email": "edge_cap@example.com",
            "previous_success_count": 50,
            "previous_failure_count": 0,
        },
        # Edge 09: Wallet limit exceeded -> Send link / alternate
        {
            "id": "pay_edge_009_wallet_limit",
            "amount": 25000,
            "payment_method": "wallet",
            "failure_reason": "wallet_limit_exceeded",
            "retry_count": 1,
            "customer_email": "edge_wallet@example.com",
            "previous_success_count": 20,
            "previous_failure_count": 2,
        },
        # Edge 10: Mandate revoked
        {
            "id": "pay_edge_010_mandate_revoked",
            "amount": 19900,
            "payment_method": "emandate",
            "failure_reason": "mandate_revoked",
            "retry_count": 0,
            "is_recurring": True,
            "subscription_id": "sub_edge_010",
            "customer_email": "edge_mandate@example.com",
            "previous_success_count": 6,
            "previous_failure_count": 1,
        },
        # Edge 11: Netbanking high value session timeout
        {
            "id": "pay_edge_011_netbank_timeout",
            "amount": 5000000,
            "payment_method": "netbanking",
            "failure_reason": "session_timeout",
            "retry_count": 2,
            "customer_email": "edge_netbank@example.com",
            "previous_success_count": 1,
            "previous_failure_count": 0,
        },
        # Edge 12: VPA Not Found
        {
            "id": "pay_edge_012_vpa_not_found",
            "amount": 15000,
            "payment_method": "upi",
            "failure_reason": "vpa_not_found",
            "retry_count": 0,
            "customer_email": "edge_vpa@example.com",
            "previous_success_count": 0,
            "previous_failure_count": 0,
        },
        # Edge 13: Fraud Suspected -> Non-retryable
        {
            "id": "pay_edge_013_fraud_suspected",
            "amount": 9000000,
            "payment_method": "card",
            "failure_reason": "fraud_suspected",
            "retry_count": 0,
            "customer_email": "edge_fraud@example.com",
            "previous_success_count": 0,
            "previous_failure_count": 5,
        },
        # Edge 14: Wallet Blocked
        {
            "id": "pay_edge_014_wallet_blocked",
            "amount": 60000,
            "payment_method": "wallet",
            "failure_reason": "wallet_blocked",
            "retry_count": 0,
            "customer_email": "edge_wblock@example.com",
            "previous_success_count": 3,
            "previous_failure_count": 0,
        },
        # Edge 15: Account Closed
        {
            "id": "pay_edge_015_account_closed",
            "amount": 149900,
            "payment_method": "emandate",
            "failure_reason": "account_closed",
            "retry_count": 0,
            "is_recurring": True,
            "subscription_id": "sub_edge_015",
            "customer_email": "edge_closed@example.com",
            "previous_success_count": 24,
            "previous_failure_count": 0,
        },
        # Edge 16: Bank Server Down - Fresh UPI
        {
            "id": "pay_edge_016_bank_down",
            "amount": 40000,
            "payment_method": "upi",
            "failure_reason": "bank_server_down",
            "retry_count": 0,
            "customer_email": "edge_bankdown@example.com",
            "previous_success_count": 15,
            "previous_failure_count": 1,
        },
        # Edge 17: Card Authentication Failed
        {
            "id": "pay_edge_017_auth_failed",
            "amount": 1200000,
            "payment_method": "card",
            "failure_reason": "authentication_failed",
            "retry_count": 1,
            "customer_email": "edge_auth@example.com",
            "previous_success_count": 4,
            "previous_failure_count": 0,
        },
        # Edge 18: Card Insufficient Funds - Established user
        {
            "id": "pay_edge_018_card_funds",
            "amount": 100000,
            "payment_method": "card",
            "failure_reason": "insufficient_funds",
            "retry_count": 0,
            "customer_email": "edge_cfunds@example.com",
            "previous_success_count": 7,
            "previous_failure_count": 0,
        },
        # Edge 19: Expired Card with Email
        {
            "id": "pay_edge_019_card_expired",
            "amount": 300000,
            "payment_method": "card",
            "failure_reason": "card_expired",
            "retry_count": 0,
            "customer_email": "edge_expired@example.com",
            "previous_success_count": 4,
            "previous_failure_count": 0,
        },
        # Edge 20: Simple UPI Timeout - Happy Path
        {
            "id": "pay_edge_020_upi_timeout",
            "amount": 85000,
            "payment_method": "upi",
            "failure_reason": "upi_timeout",
            "retry_count": 0,
            "customer_email": "edge_upi20@example.com",
            "previous_success_count": 3,
            "previous_failure_count": 0,
        },
    ]

    for idx, config in enumerate(edge_cases_config):
        hours_offset = (idx * 7) % 168
        created_at = base_time - timedelta(hours=hours_offset)
        
        gt_rec, gt_action, gt_prob, gt_reason = compute_ground_truth(config)
        
        payment = Payment(
            id=config["id"],
            customer_id=customer_ids[idx % len(customer_ids)],
            merchant_id=merchant_ids[idx % len(merchant_ids)],
            amount=config["amount"],
            currency="INR",
            payment_method=config["payment_method"],
            status="failed",
            failure_reason=config["failure_reason"],
            retry_count=config.get("retry_count", 0),
            customer_email=config.get("customer_email"),
            subscription_id=config.get("subscription_id"),
            is_recurring=config.get("is_recurring", False),
            previous_success_count=config.get("previous_success_count", 0),
            previous_failure_count=config.get("previous_failure_count", 0),
            created_at=created_at,
            ground_truth_recoverable=gt_rec,
            ground_truth_best_action=gt_action,
            ground_truth_recovery_probability=gt_prob,
            ground_truth_reason=gt_reason,
        )
        db.add(payment)
        payments.append(payment)
        
    db.commit()

    # -------------------------------------------------------------------------
    # RANDOMIZED DATA GENERATION (Fully Deterministic PRNG)
    # -------------------------------------------------------------------------
    for i in range(count):
        pay_id = f"pay_syn_{i+1:04d}"
        cust_id = rng.choice(customer_ids)
        merch_id = rng.choice(merchant_ids)
        
        # Amount distribution
        amt_roll = rng.random()
        if amt_roll < 0.60:
            amount = rng.randint(10000, 500000)      # ₹100 - ₹5,000
        elif amt_roll < 0.85:
            amount = rng.randint(500000, 2500000)    # ₹5,000 - ₹25,000
        elif amt_roll < 0.95:
            amount = rng.randint(2500000, 7500000)   # ₹25,000 - ₹75,000
        else:
            amount = rng.randint(7500000, 15000000)  # ₹75,000 - ₹1,50,000
            
        # Payment Methods
        methods = ["upi", "card", "netbanking", "wallet", "emandate"]
        method_weights = [0.45, 0.25, 0.15, 0.10, 0.05]
        method = rng.choices(methods, weights=method_weights, k=1)[0]
        
        # Failure Reasons
        if method == "upi":
            reasons = ["upi_timeout", "vpa_not_found", "bank_server_down", "insufficient_funds", "upi_pin_incorrect"]
            weights = [0.40, 0.15, 0.20, 0.20, 0.05]
        elif method == "card":
            reasons = ["insufficient_funds", "card_expired", "card_declined", "bank_server_down", "fraud_suspected", "authentication_failed"]
            weights = [0.30, 0.15, 0.20, 0.15, 0.05, 0.15]
        elif method == "netbanking":
            reasons = ["bank_server_down", "session_timeout", "authentication_failed", "insufficient_funds"]
            weights = [0.40, 0.30, 0.20, 0.10]
        elif method == "wallet":
            reasons = ["insufficient_funds", "wallet_limit_exceeded", "wallet_blocked"]
            weights = [0.50, 0.30, 0.20]
        else:  # emandate
            reasons = ["mandate_revoked", "insufficient_funds", "account_closed", "bank_server_down"]
            weights = [0.30, 0.40, 0.20, 0.10]
            
        failure_reason = rng.choices(reasons, weights=weights, k=1)[0]
        
        # Retry count
        retry_roll = rng.random()
        if retry_roll < 0.70:
            retry_count = 0
        elif retry_roll < 0.85:
            retry_count = 1
        elif retry_roll < 0.95:
            retry_count = 2
        else:
            retry_count = rng.randint(3, 5)
            
        # Email presence
        has_email = rng.random() < 0.90
        customer_email = f"{cust_id}@example.com" if has_email else None
        
        # Subscription
        is_recurring = rng.random() < 0.20
        subscription_id = f"sub_syn_{i+1:04d}" if is_recurring else None
        
        previous_success_count = int(rng.triangular(0, 50, 5))
        previous_failure_count = int(rng.triangular(0, 15, 1))
        
        days_ago = rng.randint(0, 7)
        hour = int(rng.triangular(0, 23, 14))
        minute = rng.randint(0, 59)
        second = rng.randint(0, 59)
        created_at = base_time.replace(hour=hour, minute=minute, second=second) - timedelta(days=days_ago)
        
        raw_dict = {
            "payment_method": method,
            "failure_reason": failure_reason,
            "retry_count": retry_count,
            "customer_email": customer_email,
            "is_recurring": is_recurring,
            "subscription_id": subscription_id,
            "previous_success_count": previous_success_count,
            "previous_failure_count": previous_failure_count,
        }
        gt_rec, gt_action, gt_prob, gt_reason = compute_ground_truth(raw_dict)
        
        payment = Payment(
            id=pay_id,
            customer_id=cust_id,
            merchant_id=merch_id,
            amount=amount,
            currency="INR",
            payment_method=method,
            status="failed",
            failure_reason=failure_reason,
            retry_count=retry_count,
            customer_email=customer_email,
            subscription_id=subscription_id,
            is_recurring=is_recurring,
            previous_success_count=previous_success_count,
            previous_failure_count=previous_failure_count,
            created_at=created_at,
            ground_truth_recoverable=gt_rec,
            ground_truth_best_action=gt_action,
            ground_truth_recovery_probability=gt_prob,
            ground_truth_reason=gt_reason,
        )
        db.add(payment)
        payments.append(payment)
        
    db.commit()
    return payments


def seed_database(db: Session, count: int = 500, seed: int = 42) -> int:
    """
    Seed database with reproducible synthetic payment data.
    
    Returns total count of payments seeded.
    """
    payments = generate_payments(db, count=count, seed=seed)
    return len(payments)
