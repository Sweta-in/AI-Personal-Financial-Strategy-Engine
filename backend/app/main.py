"""
FastAPI application entry point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.config import get_settings
from backend.app.database import init_db
from backend.app.middleware import setup_metrics_endpoint, setup_middleware
from backend.app.routers import auth, assets, decisions, financial, insurance, loans, portfolio
from backend.app.services.cache_service import cache_service
from backend.app.schemas.models import HealthCheck

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — startup and shutdown."""
    # Startup
    await init_db()
    try:
        await cache_service.connect()
    except Exception:
        pass  # Redis optional for local dev
    yield
    # Shutdown
    await cache_service.disconnect()


app = FastAPI(
    title="Personal Financial Intelligence Engine",
    description=(
        "Production-grade multi-agent AI system for quantified, simulation-backed "
        "financial decision support. Educational decision support only. Not financial advice."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Setup middleware
setup_middleware(app)
setup_metrics_endpoint(app)

# Register routers
app.include_router(auth.router)
app.include_router(loans.router)
app.include_router(insurance.router)
app.include_router(assets.router)
app.include_router(portfolio.router)
app.include_router(financial.router)
app.include_router(decisions.router)


@app.get("/api/health", response_model=HealthCheck, tags=["System"])
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        version="1.0.0",
        environment=settings.APP_ENV,
    )


@app.get("/", tags=["System"])
async def root():
    """Root endpoint."""
    return {
        "service": "Personal Financial Intelligence Engine",
        "version": "1.0.0",
        "docs": "/docs",
        "disclaimer": "Educational decision support only. Not financial advice.",
    }
