"""
SiteScout — FastAPI Application Factory.

This is the main entrypoint for the SiteScout backend API.
Run with: uvicorn app.main:app --reload

Registers all route modules and configures CORS middleware.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, auth, forecasting, intelligence, projects
from app.database import Base, engine

# ── Create database tables if they don't exist ────────────────────────────
Base.metadata.create_all(bind=engine)

# ── FastAPI Application ──────────────────────────────────────────────────
app = FastAPI(
    title="SiteScout API",
    description=(
        "Solar & Wind Deployment Intelligence Platform — "
        "Multi-Objective Optimization + Explainable AI"
    ),
    version="3.0.0",
)

# ── CORS Configuration ──────────────────────────────────────────────────
_allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ─────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root() -> dict:
    """Health check — confirms the API is live."""
    return {
        "message": "SiteScout API is live.",
        "version": "3.0.0",
        "milestone": "3 — Site Intelligence & Optimization",
    }


# ── Register Routers ────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(analysis.router)
app.include_router(intelligence.router)
app.include_router(forecasting.router)
