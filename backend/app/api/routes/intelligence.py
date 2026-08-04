"""
SiteScout — Intelligence API Routes (Milestone 3 Centerpiece).

Three project-scoped, authenticated endpoints that expose the core
AI engines:

  POST /api/projects/{project_id}/score-sites     → Weighted Scoring
  POST /api/projects/{project_id}/optimize         → NSGA-II Pareto Frontier
  POST /api/projects/{project_id}/explain-site     → SHAP Explainability

All endpoints require JWT authentication and validate project ownership.
Sites must have been analyzed (have at least one ScanLog) before they
can be processed by these engines.
"""

from __future__ import annotations

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.models import Project, ScanLog, Site, User
from app.schemas.scoring import (
    ExplainSiteRequest,
    OptimizationRequest,
    ParetoFrontierResponse,
    ScoreSitesResponse,
    SHAPExplanationResponse,
    SiteFeatureVector,
    SiteScoringWeights,
)
from app.services.ml_engine import (
    compute_weighted_scores,
    get_shap_explainer,
    run_pareto_optimization,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/projects",
    tags=["Intelligence Engine"],
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Shared Helpers
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


def _extract_site_features(
    sites: List[Site], db: Session
) -> List[SiteFeatureVector]:
    """
    Build SiteFeatureVector instances from sites and their latest ScanLog data.

    Only sites with at least one ScanLog (i.e., that have been analyzed) are included.
    The feature vector is constructed by parsing `full_analysis_json` from the
    most recent ScanLog for each site.
    """
    feature_vectors: List[SiteFeatureVector] = []

    for site in sites:
        # Get the most recent scan log for this site
        latest_log: ScanLog | None = (
            db.query(ScanLog)
            .filter(ScanLog.site_id == site.id)
            .order_by(ScanLog.created_at.desc())
            .first()
        )

        if latest_log is None or latest_log.full_analysis_json is None:
            logger.debug("Site %s has no analysis data — skipping", site.name)
            continue

        analysis = latest_log.full_analysis_json

        # Extract coordinates
        point = to_shape(site.coordinates)

        # Parse environmental baseline
        env_data = analysis.get("environmental_baseline", {})
        solar_irradiance = env_data.get("annual_solar_irradiance_kwh_m2_day", 0.0)
        wind_speed = env_data.get("annual_wind_speed_50m_m_s", 0.0)
        avg_temp = env_data.get("annual_avg_temp_c", 25.0)

        # Parse predictions
        predictions = analysis.get("predictions", {})
        solar_pred = predictions.get("solar", {})
        wind_pred = predictions.get("wind", {})
        solar_cf = solar_pred.get("capacity_factor_percent", 0.0)
        wind_cf = wind_pred.get("capacity_factor_percent", 0.0)
        solar_mwh = solar_pred.get("annual_energy_output_mwh", 0.0)
        wind_mwh = wind_pred.get("annual_energy_output_mwh", 0.0)

        # Parse infrastructure
        infra_data = analysis.get("infrastructure_baseline", {})
        nearest_sub = infra_data.get("nearest_substation_km") or 50.0
        nearest_pline = infra_data.get("nearest_power_line_km") or 50.0
        nearest_road = infra_data.get("nearest_major_road_km") or 50.0
        infra_count = (
            infra_data.get("substations_found_in_radius", 0)
            + infra_data.get("power_lines_found_in_radius", 0)
            + infra_data.get("roads_found_in_radius", 0)
        )

        # Parse conflicts
        conflict_data = analysis.get("land_use_conflicts", {})
        conflict_count = conflict_data.get("total_conflicts_found", 0)
        is_unsuitable = conflict_data.get("is_unsuitable", False)

        feature_vectors.append(
            SiteFeatureVector(
                site_id=site.id,
                site_name=site.name,
                solar_irradiance_kwh_m2_day=float(solar_irradiance),
                wind_speed_50m_m_s=float(wind_speed),
                solar_capacity_factor_pct=float(solar_cf),
                wind_capacity_factor_pct=float(wind_cf),
                elevation_m=float(site.elevation_m or 0),
                land_area_sqkm=float(site.land_area_sqkm or 1.0),
                nearest_substation_km=float(nearest_sub),
                nearest_power_line_km=float(nearest_pline),
                nearest_road_km=float(nearest_road),
                conflict_count=int(conflict_count),
                is_unsuitable=bool(is_unsuitable),
                infrastructure_count=int(infra_count),
                estimated_annual_mwh=float(solar_mwh + wind_mwh),
                avg_temp_c=float(avg_temp),
            )
        )

    return feature_vectors


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TASK A: Weighted Scoring Endpoint
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.post(
    "/{project_id}/score-sites",
    response_model=ScoreSitesResponse,
    summary="Score all sites in a project with user-adjustable weights",
    description=(
        "A fast triage layer that calculates weighted suitability scores for "
        "all analyzed sites in a project. Adjust weights to match your "
        "priorities — for a full trade-off view, use the /optimize endpoint."
    ),
)
def score_sites(
    project_id: UUID,
    weights: SiteScoringWeights = SiteScoringWeights(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScoreSitesResponse:
    """Score all analyzed sites in a project using user-adjustable weights."""
    project = _get_project_or_404(project_id, current_user, db)

    # Fetch all sites for this project
    sites = db.query(Site).filter(Site.project_id == project.id).all()
    if not sites:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sites found in this project. Register and analyze sites first.",
        )

    # Build feature vectors from analyzed sites
    feature_vectors = _extract_site_features(sites, db)
    if not feature_vectors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No analyzed sites found. Run the /analyze endpoint on your "
                "sites before scoring."
            ),
        )

    # Run the scoring engine
    scored_sites = compute_weighted_scores(feature_vectors, weights)

    return ScoreSitesResponse(
        project_id=project.id,
        weights_used=weights,
        total_sites_scored=len(scored_sites),
        scored_sites=scored_sites,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TASK B: Multi-Objective Optimization (Pareto Frontier)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.post(
    "/{project_id}/optimize",
    response_model=ParetoFrontierResponse,
    summary="Run NSGA-II multi-objective optimization across project sites",
    description=(
        "The centerpiece of SiteScout. Evaluates sites simultaneously across "
        "three competing objectives (energy output, environmental impact, "
        "infrastructure cost) and returns the Pareto frontier of non-dominated "
        "options — revealing the real trade-offs between your best sites."
    ),
)
def optimize_sites(
    project_id: UUID,
    config: OptimizationRequest = OptimizationRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ParetoFrontierResponse:
    """Run NSGA-II Pareto optimization on all analyzed sites in a project."""
    project = _get_project_or_404(project_id, current_user, db)

    sites = db.query(Site).filter(Site.project_id == project.id).all()
    if not sites:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sites found in this project.",
        )

    feature_vectors = _extract_site_features(sites, db)
    if not feature_vectors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No analyzed sites found. Run the /analyze endpoint on your "
                "sites before optimization."
            ),
        )

    # Run NSGA-II
    pareto_solutions, dominated_solutions = run_pareto_optimization(
        sites=feature_vectors,
        population_size=config.population_size,
        n_generations=config.n_generations,
    )

    return ParetoFrontierResponse(
        project_id=project.id,
        algorithm="NSGA-II",
        population_size=config.population_size,
        generations_evolved=config.n_generations,
        total_sites_evaluated=len(feature_vectors),
        pareto_front_size=len(pareto_solutions),
        pareto_solutions=pareto_solutions,
        dominated_solutions=dominated_solutions,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TASK C: SHAP Explainability
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.post(
    "/{project_id}/explain-site",
    response_model=SHAPExplanationResponse,
    summary="Explain a site's suitability score using SHAP",
    description=(
        "See exactly which factors drove a site's score up or down. Uses "
        "SHAP (SHapley Additive exPlanations) to decompose the ML model's "
        "prediction into per-feature contributions — turning a black box "
        "into a transparent decision-support tool."
    ),
)
def explain_site(
    project_id: UUID,
    request: ExplainSiteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SHAPExplanationResponse:
    """Generate SHAP-based explanations for a specific site's suitability."""
    project = _get_project_or_404(project_id, current_user, db)

    # Verify the target site exists and belongs to this project
    target_site_orm = (
        db.query(Site)
        .filter(Site.id == request.site_id, Site.project_id == project.id)
        .first()
    )
    if not target_site_orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site {request.site_id} not found in project {project_id}.",
        )

    # Build feature vectors for all project sites (background data for SHAP)
    all_sites_orm = db.query(Site).filter(Site.project_id == project.id).all()
    all_features = _extract_site_features(all_sites_orm, db)

    if not all_features:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No analyzed sites found. Run /analyze first.",
        )

    # Find the target site's feature vector
    target_features = [f for f in all_features if f.site_id == request.site_id]
    if not target_features:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Site {request.site_id} has not been analyzed yet. "
                f"Run /analyze on this site first."
            ),
        )

    target_fv = target_features[0]

    # Run SHAP explainer
    explainer = get_shap_explainer()
    explanation = explainer.explain_site(target_fv, all_features)

    return SHAPExplanationResponse(
        project_id=project.id,
        site_id=target_fv.site_id,
        site_name=target_fv.site_name,
        model_type=explanation["model_type"],
        base_value=explanation["base_value"],
        predicted_value=explanation["predicted_value"],
        feature_contributions=explanation["feature_contributions"],
        top_positive_drivers=explanation["top_positive_drivers"],
        top_negative_drivers=explanation["top_negative_drivers"],
    )
