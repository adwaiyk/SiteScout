"""
Pipeline Routes — SiteScout Milestone 4
Endpoints for the unified analysis pipeline, AI narrative, Q&A, and yield calculator.
"""
from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.models import Project, ScanLog, Site, User
from app.schemas.pipeline import (
    FullAnalysisRequest,
    NarrativeResponse,
    QARequest,
    QAResponse,
    YieldCalculatorRequest,
)
from app.services.analysis_pipeline import run_full_analysis
from app.services.energy_yield_engine import compute_energy_yield
from app.services.financial_engine import compute_financial_analysis
from app.services.llm_service import answer_site_question, generate_investment_narrative
from app.services.micrositing_engine import compute_micrositing

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["Unified Analysis Pipeline"])


# ── Full Pipeline (ad-hoc coordinates) ──────────────────────────────────

@router.post("/full-pipeline", summary="Run the complete analysis pipeline for any coordinates")
async def full_pipeline(request: FullAnalysisRequest) -> dict:
    """
    Location → Environmental → Infrastructure → Conflicts → ML Prediction
    → Feasibility → Suitability → Energy Yield → Financial → Micrositing
    → AI Narrative → Recommendation
    """
    try:
        result = await run_full_analysis(
            latitude=request.latitude,
            longitude=request.longitude,
            system_capacity_kw=request.system_capacity_kw,
            land_area_sqkm=request.land_area_sqkm,
            elevation_m=request.elevation_m,
            slope_deg=request.slope_deg,
            energy_type=request.energy_type,
            fit_usd_per_mwh=request.fit_usd_per_mwh,
            ndvi=request.ndvi,
            land_cover=request.land_cover,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Full pipeline failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline error: {type(e).__name__}: {str(e)}",
        )


# ── Full Pipeline (for a saved site) ───────────────────────────────────

@router.post(
    "/projects/{project_id}/sites/{site_id}/full-analysis",
    summary="Run the complete analysis pipeline for a saved site",
)
async def site_full_analysis(
    project_id: UUID,
    site_id: UUID,
    energy_type: str = "hybrid",
    fit_usd_per_mwh: float = 65.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Run the full analysis pipeline for a site already registered in a project."""
    project = db.query(Project).filter(
        Project.id == project_id, Project.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    site = db.query(Site).filter(Site.id == site_id, Site.project_id == project.id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    point = to_shape(site.coordinates)
    longitude, latitude = point.x, point.y

    try:
        result = await run_full_analysis(
            latitude=latitude,
            longitude=longitude,
            system_capacity_kw=1000.0,
            land_area_sqkm=float(site.land_area_sqkm or 5.0),
            elevation_m=float(site.elevation_m or 0.0),
            slope_deg=0.0,
            energy_type=energy_type,
            fit_usd_per_mwh=fit_usd_per_mwh,
        )

        # Save full analysis to ScanLog
        scan_log = ScanLog(
            site_id=site.id,
            solar_yield_mwh=result.get("energy_yield", {}).get("solar_yield", {}).get("annual_yield_mwh") if result.get("energy_yield", {}).get("solar_yield") else None,
            wind_yield_mwh=result.get("energy_yield", {}).get("wind_yield", {}).get("annual_yield_mwh") if result.get("energy_yield", {}).get("wind_yield") else None,
            is_unsuitable=not result.get("feasibility", {}).get("is_feasible", True),
            full_analysis_json=result,
        )
        db.add(scan_log)
        db.commit()

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Site full analysis failed")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


# ── AI Investment Narrative ─────────────────────────────────────────────

@router.post(
    "/projects/{project_id}/sites/{site_id}/narrative",
    response_model=NarrativeResponse,
    summary="Generate AI-powered investment narrative for a site",
)
def generate_narrative(
    project_id: UUID,
    site_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NarrativeResponse:
    """Generate a plain-English feasibility summary using Groq LLM."""
    project = db.query(Project).filter(
        Project.id == project_id, Project.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    site = db.query(Site).filter(Site.id == site_id, Site.project_id == project.id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # Get latest analysis
    latest_log = db.query(ScanLog).filter(
        ScanLog.site_id == site.id
    ).order_by(ScanLog.created_at.desc()).first()

    if not latest_log or not latest_log.full_analysis_json:
        raise HTTPException(
            status_code=422,
            detail="Site has not been analyzed yet. Run the full analysis first.",
        )

    result = generate_investment_narrative(latest_log.full_analysis_json)
    return NarrativeResponse(**result)


# ── AI Q&A ──────────────────────────────────────────────────────────────

@router.post(
    "/projects/{project_id}/sites/{site_id}/ask",
    response_model=QAResponse,
    summary="Ask a question about a site's analysis",
)
def ask_about_site(
    project_id: UUID,
    site_id: UUID,
    request: QARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QAResponse:
    """Answer a natural-language question grounded in the site's analysis data."""
    project = db.query(Project).filter(
        Project.id == project_id, Project.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    site = db.query(Site).filter(Site.id == site_id, Site.project_id == project.id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    latest_log = db.query(ScanLog).filter(
        ScanLog.site_id == site.id
    ).order_by(ScanLog.created_at.desc()).first()

    if not latest_log or not latest_log.full_analysis_json:
        raise HTTPException(status_code=422, detail="Site has not been analyzed yet.")

    result = answer_site_question(
        question=request.question,
        analysis_data=latest_log.full_analysis_json,
    )
    return QAResponse(**result)


# ── Yield Calculator ────────────────────────────────────────────────────

@router.post(
    "/yield-calculator",
    summary="Interactive yield and financial calculator",
)
def yield_calculator(request: YieldCalculatorRequest) -> dict:
    """
    Recompute energy yield and financials for adjusted parameters.
    Used by the frontend yield calculator for live slider feedback.
    """
    try:
        # Micrositing for capacity
        micrositing = compute_micrositing(
            total_land_area_sqkm=request.land_area_sqkm,
            energy_type=request.energy_type,
        )

        # Override micrositing capacities with user-specified values if provided
        solar_mw = request.solar_capacity_mw if request.energy_type != "wind" else 0.0
        wind_mw = request.wind_capacity_mw if request.energy_type != "solar" else 0.0

        # Energy yield
        energy_yield = compute_energy_yield(
            ghi_kwh_m2_day=request.ghi_kwh_m2_day,
            wind_speed_m_s=request.wind_speed_m_s,
            avg_temp_c=request.avg_temp_c,
            slope_deg=request.slope_deg,
            energy_type=request.energy_type,
            solar_capacity_mw=solar_mw,
            wind_capacity_mw=wind_mw,
        )

        # Financial
        annual_mwh = energy_yield.get("annual_energy_yield_mwh", 0.0)
        if request.energy_type == "hybrid":
            solar_yield = energy_yield.get("solar_yield", {})
            wind_yield_data = energy_yield.get("wind_yield", {})
            base_solar_mwh = solar_yield.get("annual_yield_mwh", 0.0) if solar_yield else 0.0
            base_wind_mwh = wind_yield_data.get("annual_yield_mwh", 0.0) if wind_yield_data else 0.0
        elif request.energy_type == "solar":
            base_solar_mwh = annual_mwh
            base_wind_mwh = 0.0
        else:
            base_solar_mwh = 0.0
            base_wind_mwh = annual_mwh

        financial = compute_financial_analysis(
            solar_capacity_mw=solar_mw,
            wind_capacity_mw=wind_mw,
            base_solar_mwh=base_solar_mwh,
            base_wind_mwh=base_wind_mwh,
            fit_usd_per_mwh=request.fit_usd_per_mwh,
        )

        return {
            "energy_yield": energy_yield,
            "financial": financial,
            "micrositing": micrositing,
        }
    except Exception as e:
        logger.exception("Yield calculator error")
        raise HTTPException(status_code=400, detail=str(e))
