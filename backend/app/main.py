"""
FastAPI application entry point.

Configures CORS, registers routers, and handles database initialization.
Run with: uvicorn app.main:app --reload
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, engine
from app import models

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="RecoverAI",
        description="AI-powered revenue recovery engine for payment merchants",
        version="0.1.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    # Auto-seed database if empty for seamless out-of-the-box deployment
    try:
        from app.database import SessionLocal
        from app.models import Payment
        from app.seed.generate_data import seed_database

        with SessionLocal() as db:
            if db.query(Payment).count() == 0:
                seed_database(db)
                logger.info("Database auto-seeded with initial synthetic payments")
    except Exception as e:
        logger.warning(f"Auto-seed check failed or skipped: {e}")

    # Register routers (imported here to avoid circular imports)
    from app.routers import audit, batch, dashboard, payments, analysis, system

    app.include_router(payments.router, prefix="/api", tags=["Payments"])
    app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
    app.include_router(batch.router, prefix="/api", tags=["Batch"])
    app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
    app.include_router(audit.router, prefix="/api", tags=["Audit"])
    app.include_router(system.router, prefix="/api", tags=["System"])

    @app.get("/api/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "ok", "service": "RecoverAI"}

    return app


app = create_app()
