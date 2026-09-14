"""
Tests for the Reset + Ready State lifecycle and concurrency guardrails.
"""

from unittest.mock import patch
from fastapi.testclient import TestClient

from app.database import Base, engine, SessionLocal
from app.models import BatchRun, Payment, RecoveryResult, AuditLog
from app.main import app
from app.services.ai_engine import heuristic_diagnose

client = TestClient(app)


def setup_function():
    """Reset test database with fresh 520 payments before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    res = client.post("/api/payments/seed")
    assert res.status_code == 200


def test_initial_ready_state():
    """Initial seeded state has 520 payments and is in READY state."""
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["state"] == "ready"
    assert data["has_analysis"] is False
    assert data["payment_count"] == 520
    assert data["batch_id"] is None
    assert data["total_recovered"] == 0


def test_batch_run_to_completed_state():
    """Running a batch transitions state to COMPLETED with persisted metrics."""
    def mock_analyze(payment, settings=None):
        return heuristic_diagnose(payment), True

    with patch("app.services.batch_processor.analyze_payment_with_source", side_effect=mock_analyze):
        run_res = client.post("/api/batch/run")
        assert run_res.status_code == 200
        batch = run_res.json()
        assert batch["status"] == "completed"

    dash_res = client.get("/api/dashboard/stats")
    assert dash_res.status_code == 200
    stats = dash_res.json()
    assert stats["state"] == "completed"
    assert stats["has_analysis"] is True
    assert stats["payment_count"] == 520
    assert stats["batch_id"] == batch["id"]
    assert stats["total_recovered"] > 0
    assert stats["recovery_efficiency"] > 0.0


def test_reset_analysis_lifecycle():
    """Resetting clears analysis artifacts, preserves 520 payments, and returns to READY state."""
    def mock_analyze(payment, settings=None):
        return heuristic_diagnose(payment), True

    # 1. Run batch to get into COMPLETED state
    with patch("app.services.batch_processor.analyze_payment_with_source", side_effect=mock_analyze):
        run_res = client.post("/api/batch/run")
        assert run_res.status_code == 200

    with SessionLocal() as db:
        assert db.query(Payment).count() == 520
        assert db.query(BatchRun).count() >= 1
        assert db.query(RecoveryResult).count() > 0
        assert db.query(AuditLog).count() > 0

    # 2. Reset analysis
    reset_res = client.post("/api/batch/reset")
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    assert reset_data["status"] == "reset"
    assert reset_data["state"] == "ready"
    assert reset_data["payment_count"] == 520
    assert reset_data["batch_id"] is None

    # 3. Verify database state
    with SessionLocal() as db:
        assert db.query(Payment).count() == 520  # PRESERVED!
        assert db.query(BatchRun).count() == 0   # CLEARED!
        assert db.query(RecoveryResult).count() == 0  # CLEARED!
        assert db.query(AuditLog).count() == 0   # CLEARED!

    # 4. Verify dashboard stats return READY state
    dash_res = client.get("/api/dashboard/stats")
    assert dash_res.status_code == 200
    stats = dash_res.json()
    assert stats["state"] == "ready"
    assert stats["has_analysis"] is False
    assert stats["payment_count"] == 520
    assert stats["batch_id"] is None
    assert stats["total_recovered"] == 0

    # 5. Calling reset repeatedly is safe and idempotent
    repeat_res = client.post("/api/batch/reset")
    assert repeat_res.status_code == 200
    assert repeat_res.json()["state"] == "ready"
    assert repeat_res.json()["payment_count"] == 520


def test_rerun_batch_after_reset():
    """Can run a completely new batch after reset and persist new results."""
    def mock_analyze(payment, settings=None):
        return heuristic_diagnose(payment), True

    with patch("app.services.batch_processor.analyze_payment_with_source", side_effect=mock_analyze):
        # First run
        run1 = client.post("/api/batch/run").json()
        # Reset
        client.post("/api/batch/reset")
        # Second run
        run2 = client.post("/api/batch/run").json()
        assert run2["status"] == "completed"
        assert run2["id"] != run1["id"]

    dash_res = client.get("/api/dashboard/stats")
    assert dash_res.status_code == 200
    stats = dash_res.json()
    assert stats["state"] == "completed"
    assert stats["has_analysis"] is True
    assert stats["batch_id"] == run2["id"]


def test_concurrent_batch_run_protection():
    """Attempting to run a batch when one is already in running status returns 409."""
    with SessionLocal() as db:
        dummy_running = BatchRun(id="batch_running_test", status="running")
        db.add(dummy_running)
        db.commit()

    res = client.post("/api/batch/run")
    assert res.status_code == 409
    assert "already in progress" in res.json()["detail"]
