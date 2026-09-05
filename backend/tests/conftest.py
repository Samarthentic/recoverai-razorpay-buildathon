"""
Pytest configuration and environment isolation.

Ensures that test execution uses a dedicated test database (test_recoverai.db)
and zero rate-limit delays, so the live development database (recoverai.db)
is never overwritten or polluted by automated test runs.
"""

import os
import pytest

# Ensure test DB is isolated before any app modules are imported
os.environ["RECOVERAI_DATABASE_URL"] = "sqlite:///./test_recoverai.db"
os.environ["RECOVERAI_GEMINI_RATE_LIMIT_DELAY"] = "0.0"

from app.config import get_settings
get_settings.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """Clean up test database file after test session finishes."""
    yield
    test_db_path = "test_recoverai.db"
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except OSError:
            pass
