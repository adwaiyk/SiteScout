"""SiteScout API — Milestone 4.0.0"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, auth, forecasting, intelligence, projects
from app.api.routes import pipeline
from app.database import Base, engine

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SiteScout API",
    description=(
        "Solar & Wind Deployment Intelligence Platform — "
        "Multi-Objective Optimization + Explainable AI + Full Analysis Pipeline"
    ),
    version="4.0.0",
)

# CORS
_allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root() -> dict:
    return {
        "message": "SiteScout API is live.",
        "version": "4.0.0",
        "milestone": "4 — Full Analysis Pipeline + AI Narrative",
    }


# Register routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(analysis.router)
app.include_router(intelligence.router)
app.include_router(forecasting.router)
app.include_router(pipeline.router)
