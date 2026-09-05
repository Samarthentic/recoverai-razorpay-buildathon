"""
Tests for AI engine diagnostics, fallback handling, and LLM source tracking.
"""

from unittest.mock import MagicMock, patch

from app.config import Settings
from app.models import Payment
from app.services.ai_engine import analyze_payment, analyze_payment_with_source, heuristic_diagnose


def test_heuristic_diagnose_transient_upi():
    payment = Payment(
        id="pay_h1",
        payment_method="upi",
        failure_reason="upi_timeout",
        retry_count=0,
        amount=50000,
        customer_email="test@example.com",
    )
    rec = heuristic_diagnose(payment)
    assert rec.recommendation == "retry_payment"
    assert rec.is_recoverable is True
    assert rec.confidence >= 0.70


def test_heuristic_diagnose_fraud_suspected():
    payment = Payment(
        id="pay_h2",
        payment_method="card",
        failure_reason="fraud_suspected",
        amount=50000,
        customer_email="test@example.com",
    )
    rec = heuristic_diagnose(payment)
    assert rec.recommendation == "do_not_retry"
    assert rec.is_recoverable is False


def test_analyze_payment_fallback_when_no_api_key():
    settings = Settings(gemini_api_key="", gemini_model="gemini-3.5-flash")
    payment = Payment(
        id="pay_h3",
        payment_method="card",
        failure_reason="card_expired",
        customer_email="test@example.com",
        amount=50000,
    )
    rec, is_llm = analyze_payment_with_source(payment, settings)
    assert rec is not None
    assert is_llm is False


def test_analyze_payment_with_source_success():
    """Verify is_llm_generated is True when Gemini successfully returns."""
    settings = Settings(gemini_api_key="valid_key", gemini_model="gemini-3.5-flash")
    payment = Payment(
        id="pay_h4",
        payment_method="upi",
        failure_reason="upi_timeout",
        retry_count=0,
        amount=50000,
    )

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"root_cause": "Timeout", "recommendation": "retry_payment", "confidence": 0.9, "explanation": "Retry", "is_recoverable": true}'
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.services.ai_engine.get_client", return_value=mock_client):
        rec, is_llm = analyze_payment_with_source(payment, settings)
        assert is_llm is True
        assert rec.recommendation == "retry_payment"
        assert rec.is_recoverable is True


def test_analyze_payment_with_source_failure_fallback():
    """Verify is_llm_generated is False and fallback to heuristic when Gemini raises an exception."""
    settings = Settings(gemini_api_key="valid_key", gemini_model="gemini-3.5-flash", gemini_rate_limit_delay=0.0)
    payment = Payment(
        id="pay_h5",
        payment_method="upi",
        failure_reason="upi_timeout",
        retry_count=0,
        amount=50000,
    )

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("General API connection failure")

    with patch("app.services.ai_engine.get_client", return_value=mock_client):
        rec, is_llm = analyze_payment_with_source(payment, settings)
        assert is_llm is False
        assert rec.recommendation == "retry_payment"  # heuristic for transient upi timeout
        assert rec.is_recoverable is True


def test_sequential_payments_receive_independent_analyses():
    """Verify two distinct payments receive independent Gemini analyses and never reuse cached results."""
    settings = Settings(gemini_api_key="valid_key", gemini_model="gemini-3.5-flash", gemini_rate_limit_delay=0.0)
    
    pay_1 = Payment(
        id="pay_seq_1",
        payment_method="upi",
        failure_reason="upi_timeout",
        retry_count=0,
        amount=50000,
    )
    pay_2 = Payment(
        id="pay_seq_2",
        payment_method="card",
        failure_reason="card_expired",
        retry_count=0,
        amount=150000,
        customer_email="customer@example.com",
    )

    def dynamic_generate_content(*args, **kwargs):
        contents = kwargs.get("contents", "")
        mock_resp = MagicMock()
        if "pay_seq_1" in contents:
            mock_resp.text = '{"root_cause": "UPI PSP Timeout", "recommendation": "retry_payment", "confidence": 0.92, "explanation": "Transient network glitch", "is_recoverable": true}'
        elif "pay_seq_2" in contents:
            mock_resp.text = '{"root_cause": "Card Expiry Date Passed", "recommendation": "send_payment_link", "confidence": 0.88, "explanation": "Card expired, link needed", "is_recoverable": true}'
        else:
            mock_resp.text = '{"root_cause": "Unknown", "recommendation": "escalate_to_human", "confidence": 0.5, "explanation": "Default", "is_recoverable": false}'
        return mock_resp

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = dynamic_generate_content

    with patch("app.services.ai_engine.get_client", return_value=mock_client):
        rec1, is_llm1 = analyze_payment_with_source(pay_1, settings)
        rec2, is_llm2 = analyze_payment_with_source(pay_2, settings)

        assert is_llm1 is True
        assert is_llm2 is True
        assert rec1.recommendation == "retry_payment"
        assert rec2.recommendation == "send_payment_link"
        assert rec1.root_cause == "UPI PSP Timeout"
        assert rec2.root_cause == "Card Expiry Date Passed"
        assert rec1.root_cause != rec2.root_cause


def test_gemini_failure_on_payment_a_does_not_affect_payment_b():
    """Verify Gemini failure on payment A falls back to heuristic without marking payment B as failed or fallback."""
    settings = Settings(gemini_api_key="valid_key", gemini_model="gemini-3.5-flash", gemini_rate_limit_delay=0.0)

    pay_a = Payment(
        id="pay_fail_a",
        payment_method="card",
        failure_reason="fraud_suspected",
        amount=50000,
    )
    pay_b = Payment(
        id="pay_success_b",
        payment_method="upi",
        failure_reason="upi_timeout",
        amount=50000,
    )

    def selective_generate_content(*args, **kwargs):
        contents = kwargs.get("contents", "")
        if "pay_fail_a" in contents:
            raise Exception("503 Service Unavailable")
        mock_resp = MagicMock()
        mock_resp.text = '{"root_cause": "UPI Gateway Glitch", "recommendation": "retry_payment", "confidence": 0.90, "explanation": "Retryable UPI failure", "is_recoverable": true}'
        return mock_resp

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = selective_generate_content

    with patch("app.services.ai_engine.get_client", return_value=mock_client):
        rec_a, is_llm_a = analyze_payment_with_source(pay_a, settings)
        rec_b, is_llm_b = analyze_payment_with_source(pay_b, settings)

        # Payment A failed LLM -> fell back to heuristic -> is_llm_generated=False
        assert is_llm_a is False
        assert rec_a.recommendation == "do_not_retry"  # fraud_suspected heuristic

        # Payment B succeeded with LLM -> is_llm_generated=True
        assert is_llm_b is True
        assert rec_b.recommendation == "retry_payment"
        assert rec_b.root_cause == "UPI Gateway Glitch"


def test_429_rate_limit_retry_and_fallback():
    """Verify 429 rate limit triggers retry attempts with backoff and falls back cleanly to heuristic."""
    settings = Settings(
        gemini_api_key="valid_key",
        gemini_model="gemini-3.5-flash",
        gemini_max_retries=2,
        gemini_rate_limit_delay=0.0,
    )
    payment = Payment(
        id="pay_rate_limit",
        payment_method="card",
        failure_reason="card_expired",
        customer_email="test@example.com",
        amount=100000,
    )

    mock_client = MagicMock()
    # Always raise 429 quota exhaustion
    mock_client.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED Quota exceeded")

    with patch("app.services.ai_engine.get_client", return_value=mock_client), \
         patch("time.sleep") as mock_sleep:
        rec, is_llm = analyze_payment_with_source(payment, settings)

        # Should fall back cleanly to heuristic
        assert is_llm is False
        assert rec.recommendation == "send_payment_link"  # card_expired heuristic with email
        # Verify retries occurred
        assert mock_client.models.generate_content.call_count > 1
        assert mock_sleep.called


def test_only_valid_gemini_response_marked_as_llm_generated():
    """Verify that malformed or non-JSON Gemini responses fall back to heuristic with is_llm_generated=False."""
    settings = Settings(gemini_api_key="valid_key", gemini_model="gemini-3.5-flash", gemini_rate_limit_delay=0.0)
    payment = Payment(
        id="pay_malformed",
        payment_method="upi",
        failure_reason="upi_timeout",
        amount=50000,
    )

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "NOT JSON OUTPUT AT ALL"
    mock_client.models.generate_content.return_value = mock_resp

    with patch("app.services.ai_engine.get_client", return_value=mock_client):
        rec, is_llm = analyze_payment_with_source(payment, settings)
        assert is_llm is False
        assert rec.recommendation == "retry_payment"  # heuristic fallback
