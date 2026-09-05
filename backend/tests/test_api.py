"""
Integration tests for FastAPI endpoints, database seeding, single analysis, and batch runs.
"""

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import Base, engine
from app.main import app

client = TestClient(app)


def setup_module():
    """Ensure clean database tables for testing."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "RecoverAI"}


def test_seed_and_list_payments():
    seed_res = client.post("/api/payments/seed")
    assert seed_res.status_code == 200
    assert "Successfully seeded 520 payments" in seed_res.json()["message"]

    list_res = client.get("/api/payments?limit=5")
    assert list_res.status_code == 200
    payments = list_res.json()
    assert len(payments) == 5
    assert payments[0]["id"] == "pay_demo_happy_path"
    assert "ground_truth_recoverable" in payments[0]


def test_get_demo_cases():
    res = client.get("/api/payments/demo-cases")
    assert res.status_code == 200
    cases = res.json()
    assert len(cases) == 5
    case_ids = {c["id"] for c in cases}
    assert "pay_demo_happy_path" in case_ids
    assert "pay_demo_max_retries" in case_ids
    assert "pay_demo_high_value" in case_ids
    assert "pay_demo_no_email" in case_ids
    assert "pay_demo_low_conf" in case_ids


def test_analyze_single_payment():
    def mock_analyze(payment, settings=None):
        return AIRecommendation(
            root_cause="High value test card decline",
            recommendation="send_payment_link",
            confidence=0.85,
            explanation="Test mock recommendation for high value decline",
            is_recoverable=True,
        ), True

    with patch("app.services.batch_processor.analyze_payment_with_source", side_effect=mock_analyze):
        # Test Case C: High value escalation
        res_hv = client.post("/api/analyze/pay_demo_high_value")
        assert res_hv.status_code == 200
        data_hv = res_hv.json()
        assert data_hv["policy_decision"]["decision"] == "escalated"
        assert "high_value_human_review" in data_hv["policy_decision"]["triggered_rules"]

        # Test Edge Case 007: Cancelled subscription block
        res_sub = client.post("/api/analyze/pay_edge_007_sub_cancelled")
        assert res_sub.status_code == 200
        data_sub = res_sub.json()
        assert data_sub["policy_decision"]["decision"] == "blocked"
        assert "subscription_cancelled" in data_sub["policy_decision"]["triggered_rules"]


from unittest.mock import patch
from app.schemas import AIRecommendation
from app.services.ai_engine import heuristic_diagnose


def test_run_batch_and_dashboard_stats():
    # Mock LLM calls to test batch processor and dashboard deterministically with varied per-payment responses
    def mock_analyze(payment, settings=None):
        return heuristic_diagnose(payment), True

    with patch("app.services.batch_processor.analyze_payment_with_source", side_effect=mock_analyze):
        batch_res = client.post("/api/batch/run")
        assert batch_res.status_code == 200
        batch = batch_res.json()
        assert batch["status"] == "completed"
        assert batch["total_payments"] == 520
    assert batch["total_at_risk"] > 0
    assert batch["ground_truth_recoverable_revenue"] > 0
    assert batch["total_recovered"] > 0
    assert batch["recovery_efficiency"] > 0.0
    assert batch["ai_precision"] > 0.0
    assert "llm_analyzed_count" in batch
    assert "heuristic_fallback_count" in batch
    assert "llm_precision" in batch

    # Check batch results endpoint for is_llm_generated field
    results_res = client.get(f"/api/batch/{batch['id']}/results?limit=5")
    assert results_res.status_code == 200
    results_data = results_res.json()
    assert len(results_data) == 5
    assert "is_llm_generated" in results_data[0]

    dash_res = client.get("/api/dashboard/stats")
    assert dash_res.status_code == 200
    stats = dash_res.json()
    assert stats["total_payments"] == 520
    assert stats["ground_truth_recoverable_revenue"] == batch["ground_truth_recoverable_revenue"]
    assert stats["recovery_efficiency"] == batch["recovery_efficiency"]
    assert "llm_analyzed_count" in stats


def test_get_system_status():
    res = client.get("/api/system/status")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == "RecoverAI"
    assert data["status"] == "operational"
    assert "components" in data
    assert data["components"]["recovery_engine"] == "operational"
    assert data["components"]["policy_engine"] == "operational"
    assert "ai_configuration" in data
    assert data["ai_configuration"]["model"] == "gemini-3.5-flash"
    assert data["ai_configuration"]["batch_limit"] == get_settings().ai_batch_limit
    assert "policy_configuration" in data
    assert data["policy_configuration"]["max_retries"] == 3
    assert data["policy_configuration"]["high_value_threshold"] == 5_000_000
    assert "gemini_api_key" not in str(data)  # Guaranteed zero secret leakage

