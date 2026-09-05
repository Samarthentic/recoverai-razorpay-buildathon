import pytest

from app.models import Payment
from app.schemas import AIRecommendation
from app.services.policy_engine import PolicyConfig, evaluate_policy

def make_payment(**kwargs) -> Payment:
    defaults = {
        'id': 'pay_test_001',
        'customer_id': 'cust_test',
        'merchant_id': 'merch_test',
        'amount': 100000,  # ₹1,000
        'currency': 'INR',
        'payment_method': 'upi',
        'status': 'failed',
        'failure_reason': 'upi_timeout',
        'retry_count': 0,
        'customer_email': 'test@example.com',
        'subscription_id': None,
        'is_recurring': False,
        'previous_success_count': 5,
        'previous_failure_count': 1,
    }
    defaults.update(kwargs)
    return Payment(**defaults)

def make_recommendation(**kwargs) -> AIRecommendation:
    defaults = {
        'root_cause': 'Test root cause',
        'recommendation': 'retry_payment',
        'confidence': 0.85,
        'explanation': 'Test explanation',
        'is_recoverable': True,
    }
    defaults.update(kwargs)
    return AIRecommendation(**defaults)

def test_approves_valid_retry():
    payment = make_payment(retry_count=1)
    recommendation = make_recommendation(recommendation='retry_payment')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'approved', "Valid retry should be approved"
    assert not decision.triggered_rules
    assert not decision.reasons

def test_approves_valid_payment_link():
    payment = make_payment(customer_email='test@example.com')
    recommendation = make_recommendation(recommendation='send_payment_link')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'approved', "Valid payment link should be approved"
    assert not decision.triggered_rules
    assert not decision.reasons

def test_blocks_retry_when_max_retries_exceeded():
    payment = make_payment(retry_count=4)
    recommendation = make_recommendation(recommendation='retry_payment')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'blocked', "Should block if max retries exceeded"
    assert 'max_retry_exceeded' in decision.triggered_rules
    assert len(decision.reasons) > 0

def test_blocks_retry_at_exact_max_retries():
    payment = make_payment(retry_count=3)
    recommendation = make_recommendation(recommendation='retry_payment')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'blocked', "Should block if at exact max retries"
    assert 'max_retry_exceeded' in decision.triggered_rules
    assert len(decision.reasons) > 0

def test_allows_retry_below_max():
    payment = make_payment(retry_count=2)
    recommendation = make_recommendation(recommendation='retry_payment')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'approved', "Should approve if below max retries"
    assert not decision.triggered_rules
    assert not decision.reasons

def test_escalates_high_value_payment():
    payment = make_payment(amount=6000000)
    recommendation = make_recommendation(recommendation='retry_payment')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'escalated', "Should escalate high value payments"
    assert 'high_value_human_review' in decision.triggered_rules
    assert len(decision.reasons) > 0

def test_high_value_does_not_escalate_if_already_escalate_to_human():
    payment = make_payment(amount=6000000)
    recommendation = make_recommendation(recommendation='escalate_to_human')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'approved', "Should not apply high value escalation rule if recommendation is already escalate_to_human"
    assert 'high_value_human_review' not in decision.triggered_rules

def test_escalates_low_confidence():
    payment = make_payment()
    recommendation = make_recommendation(confidence=0.3)
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'escalated', "Should escalate low AI confidence"
    assert 'low_confidence_escalate' in decision.triggered_rules
    assert len(decision.reasons) > 0

def test_approves_at_exact_confidence_threshold():
    payment = make_payment()
    recommendation = make_recommendation(confidence=0.6)
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'approved', "Should approve at exact confidence threshold"
    assert 'low_confidence_escalate' not in decision.triggered_rules

def test_blocks_repeat_failure_customer_retry():
    payment = make_payment(previous_failure_count=5)
    recommendation = make_recommendation(recommendation='retry_payment')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'blocked', "Should block retry for repeat failure customer"
    assert 'repeated_customer_failure' in decision.triggered_rules
    assert len(decision.reasons) > 0

def test_allows_payment_link_for_repeat_failure_customer():
    payment = make_payment(previous_failure_count=8)
    recommendation = make_recommendation(recommendation='send_payment_link')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'approved', "Should allow payment link even if repeat failure limit is reached"
    assert 'repeated_customer_failure' not in decision.triggered_rules

@pytest.mark.parametrize("failure_reason", ["card_expired", "account_closed", "fraud_suspected"])
def test_blocks_retry_on_non_retryable_reasons(failure_reason):
    payment = make_payment(failure_reason=failure_reason)
    recommendation = make_recommendation(recommendation='retry_payment')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'blocked', f"Should block retry for failure_reason {failure_reason}"
    assert 'invalid_action_for_reason' in decision.triggered_rules
    assert len(decision.reasons) > 0

def test_allows_payment_link_on_expired_card():
    payment = make_payment(failure_reason='card_expired')
    recommendation = make_recommendation(recommendation='send_payment_link')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'approved', "Should allow payment link for expired card"
    assert 'invalid_action_for_reason' not in decision.triggered_rules

def test_blocks_payment_link_without_email():
    payment = make_payment(customer_email=None)
    recommendation = make_recommendation(recommendation='send_payment_link')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'blocked', "Should block payment link if email is missing"
    assert 'missing_contact_info' in decision.triggered_rules
    assert len(decision.reasons) > 0

def test_blocks_reminder_without_email():
    payment = make_payment(customer_email=None)
    recommendation = make_recommendation(recommendation='send_reminder')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'blocked', "Should block reminder if email is missing"
    assert 'missing_contact_info' in decision.triggered_rules
    assert len(decision.reasons) > 0

def test_allows_retry_with_email_present():
    payment = make_payment(customer_email='test@example.com')
    recommendation = make_recommendation(recommendation='retry_payment')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'approved', "Should allow retry when email is present"
    assert 'missing_contact_info' not in decision.triggered_rules

def test_blocks_cancelled_subscription():
    payment = make_payment(subscription_id='sub_123', failure_reason='subscription_cancelled')
    recommendation = make_recommendation(recommendation='retry_payment')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'blocked', "Should block action on cancelled subscription"
    assert 'subscription_cancelled' in decision.triggered_rules
    assert len(decision.reasons) > 0

def test_escalates_amount_cap():
    payment = make_payment(amount=11000000)
    recommendation = make_recommendation(recommendation='retry_payment')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'escalated', "Should escalate due to max auto recovery amount cap"
    assert 'amount_cap' in decision.triggered_rules
    assert len(decision.reasons) > 0

def test_multiple_rules_fire_simultaneously():
    payment = make_payment(retry_count=5, amount=8000000, failure_reason='card_expired')
    recommendation = make_recommendation(recommendation='retry_payment')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'blocked', "Block should take precedence over escalated"
    assert 'max_retry_exceeded' in decision.triggered_rules
    assert 'high_value_human_review' in decision.triggered_rules
    assert 'invalid_action_for_reason' in decision.triggered_rules
    assert len(decision.reasons) >= 3

def test_custom_config_thresholds():
    payment = make_payment(retry_count=2, amount=4000000)
    recommendation = make_recommendation(recommendation='retry_payment', confidence=0.5)
    
    config = PolicyConfig(
        max_retries=2, 
        high_value_threshold=3000000,
        confidence_threshold=0.8
    )
    
    decision = evaluate_policy(payment, recommendation, config)
    
    assert decision.decision == 'blocked', "Custom threshold blocked max_retry_exceeded"
    assert 'max_retry_exceeded' in decision.triggered_rules
    assert 'high_value_human_review' in decision.triggered_rules
    assert 'low_confidence_escalate' in decision.triggered_rules

def test_do_not_retry_is_always_approved():
    payment = make_payment()
    recommendation = make_recommendation(recommendation='do_not_retry')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'approved', "Do not retry should be approved"
    assert not decision.triggered_rules

def test_escalate_to_human_is_always_approved():
    payment = make_payment()
    recommendation = make_recommendation(recommendation='escalate_to_human')
    decision = evaluate_policy(payment, recommendation)
    
    assert decision.decision == 'approved', "Escalate to human should be approved"
    assert not decision.triggered_rules
