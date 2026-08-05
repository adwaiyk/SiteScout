"""
SiteScout — Forecasting & Grid Capacity API Routes (Milestone 3 Part 2).

Two project-scoped, authenticated endpoints:

  POST /api/projects/{project_id}/forecast       → Energy Forecasting (P10/P50/P90)
  POST /api/projects/{project_id}/grid-capacity   → Grid Hosting Capacity Heuristic

Both endpoints require JWT authentication and validate project ownership.
Sites must have been analyzed (have at least one ScanLog) before they
can be processed by these engines.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.models import Project, ScanLog, Site, User
from app.schemas.forecasting import (
    ForecastRequest,
    ForecastResponse,
    GridCapacityRequest,
    GridCapacityResponse,
)
from app.services.forecasting import compute_energy_forecast
from app.services.grid_heuristics import compute_grid_hosting_capacity

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/projects",
    tags=["Forecasting & Grid Capacity"],
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Shared Helpers (mirrors intelligence.py pattern)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _get_project_or_404(
    project_id: UUID,
    current_user: User,
    db: Session,
) -> Project:
    """Fetch project by ID, verify ownership, or raise 404."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found or you do not have access.",
        )
    return project


def _get_site_with_analysis(
    site_id: UUID,
    project_id: UUID,
    db: Session,
) -> tuple:
    """
    Fetch a site and its latest ScanLog analysis data.

    Returns
    -------
    tuple
        (Site ORM instance, ScanLog ORM instance, parsed analysis dict)

    Raises
    ------
    HTTPException 404
        If the site doesn't exist in the project.
    HTTPException 422
        If the site has not been analyzed yet.
    """
    site = (
        db.query(Site)
        .filter(Site.id == site_id, Site.project_id == project_id)
        .first()
    )
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site {site_id} not found in project {project_id}.",
        )

    latest_log = (
        db.query(ScanLog)
        .filter(ScanLog.site_id == site.id)
        .order_by(ScanLog.created_at.desc())
        .first()
    )

    if latest_log is None or latest_log.full_analysis_json is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Site {site_id} has not been analyzed yet. "
                f"Run the /analyze endpoint on this site first."
            ),
        )

    return site, latest_log, latest_log.full_analysis_json


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TASK A: Uncertainty-Aware Energy Forecasting
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.post(
    "/{project_id}/forecast",
    response_model=ForecastResponse,
    summary="Generate uncertainty-aware energy forecast with P10/P50/P90 bands",
    description=(
        "Produces monthly seasonality profiles and 25-year lifespan projections "
        "with confidence bands (P10=conservative, P50=expected, P90=optimistic). "
        "Includes degradation modelling for realistic long-term estimates. "
        "Standard energy models give misleading single-point numbers — this "
        "endpoint provides the full probability range that investors need."
    ),
)
def generate_forecast(
    project_id: UUID,
    request: ForecastRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ForecastResponse:
    """Generate P10/P50/P90 energy forecast for a specific site."""
    project = _get_project_or_404(project_id, current_user, db)
    site, scan_log, analysis = _get_site_with_analysis(
        request.site_id, project.id, db
    )

    # ── Extract environmental data from analysis ─────────────────────────
    env_data = analysis.get("environmental_baseline", {})
    solar_irradiance = float(env_data.get("annual_solar_irradiance_kwh_m2_day", 0.0))
    wind_speed = float(env_data.get("annual_wind_speed_50m_m_s", 0.0))
    avg_temp = float(env_data.get("annual_avg_temp_c", 25.0))

    # ── Extract prediction data ──────────────────────────────────────────
    predictions = analysis.get("predictions", {})
    solar_pred = predictions.get("solar", {})
    wind_pred = predictions.get("wind", {})
    solar_cf = float(solar_pred.get("capacity_factor_percent", 0.0))
    wind_cf = float(wind_pred.get("capacity_factor_percent", 0.0))

    logger.info(
        "Generating forecast for site '%s' (%.1f MW): "
        "solar_irr=%.2f, wind_speed=%.2f, temp=%.1f",
        site.name, request.capacity_mw, solar_irradiance, wind_speed, avg_temp,
    )

    # ── Run forecasting engine ───────────────────────────────────────────
    result = compute_energy_forecast(
        site_name=site.name,
        capacity_mw=request.capacity_mw,
        system_loss_pct=request.system_loss_pct,
        solar_irradiance_kwh_m2_day=solar_irradiance,
        wind_speed_50m_m_s=wind_speed,
        solar_capacity_factor_pct=solar_cf,
        wind_capacity_factor_pct=wind_cf,
        avg_temp_c=avg_temp,
    )

    return ForecastResponse(
        project_id=project.id,
        site_id=site.id,
        site_name=site.name,
        capacity_mw=request.capacity_mw,
        system_loss_pct=request.system_loss_pct,
        energy_type=result["energy_type"],
        monthly_forecasts=result["monthly_forecasts"],
        annual_forecasts=result["annual_forecasts"],
        cumulative=result["cumulative"],
        first_year_p50_mwh=result["first_year_p50_mwh"],
        capacity_factor_pct=result["capacity_factor_pct"],
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TASK B: Grid Hosting Capacity Heuristic
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.post(
    "/{project_id}/grid-capacity",
    response_model=GridCapacityResponse,
    summary="Estimate grid hosting capacity for a site",
    description=(
        "Rather than just reporting 'distance to nearest substation', this "
        "endpoint estimates remaining grid hosting capacity in MW using "
        "standard electrical engineering heuristics (thermal limits, voltage "
        "class inference, existing generation estimation). Returns hosting "
        "status classification and maximum recommended interconnection size."
    ),
)
def assess_grid_capacity(
    project_id: UUID,
    request: GridCapacityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GridCapacityResponse:
    """Assess grid hosting capacity for a specific site."""
    project = _get_project_or_404(project_id, current_user, db)
    site, scan_log, analysis = _get_site_with_analysis(
        request.site_id, project.id, db
    )

    # ── Extract infrastructure data from analysis ────────────────────────
    infra_data = analysis.get("infrastructure_baseline", {})
    substation_km = infra_data.get("nearest_substation_km")
    power_line_km = infra_data.get("nearest_power_line_km")
    road_km = infra_data.get("nearest_major_road_km")

    # Convert None-like values
    if substation_km is not None:
        substation_km = float(substation_km)
    if power_line_km is not None:
        power_line_km = float(power_line_km)
    if road_km is not None:
        road_km = float(road_km)

    infrastructure_count = (
        int(infra_data.get("substations_found_in_radius", 0))
        + int(infra_data.get("power_lines_found_in_radius", 0))
        + int(infra_data.get("roads_found_in_radius", 0))
    )

    logger.info(
        "Assessing grid capacity for site '%s': "
        "substation=%.1f km, power_line=%.1f km, infra_count=%d",
        site.name,
        substation_km or -1,
        power_line_km or -1,
        infrastructure_count,
    )

    # ── Run grid heuristic engine ────────────────────────────────────────
    result = compute_grid_hosting_capacity(
        site_name=site.name,
        substation_distance_km=substation_km,
        power_line_distance_km=power_line_km,
        road_distance_km=road_km,
        infrastructure_count=infrastructure_count,
    )

    return GridCapacityResponse(
        project_id=project.id,
        site_id=site.id,
        site_name=site.name,
        substation_distance_km=result["substation_distance_km"],
        estimated_voltage_kv=result["estimated_voltage_kv"],
        line_distance_km=result["line_distance_km"],
        estimated_line_rating_a=result["estimated_line_rating_a"],
        existing_generation_nearby_mw=result["existing_generation_nearby_mw"],
        thermal_limit_mw=result["thermal_limit_mw"],
        estimated_spare_capacity_mw=result["estimated_spare_capacity_mw"],
        hosting_status=result["hosting_status"],
        max_recommended_interconnect_mw=result["max_recommended_interconnect_mw"],
        assessment_notes=result["assessment_notes"],
    )
