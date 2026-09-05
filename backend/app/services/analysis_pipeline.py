"""
Unified Analysis Pipeline — SiteScout Milestone 4
Orchestrates: Location → Environment → Infrastructure → Conflicts → ML Prediction
→ Feasibility → Suitability → Energy Yield → Financial → Micrositing → AI Narrative
→ Final Recommendation
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from app.services.conflict_detector import detect_land_use_conflicts
from app.services.energy_yield_engine import compute_energy_yield
from app.services.feasibility_engine import evaluate_feasibility, infer_land_cover_from_conflicts
from app.services.financial_engine import compute_financial_analysis
from app.services.infrastructure_engine import fetch_osm_infrastructure
from app.services.llm_service import generate_investment_narrative
from app.services.micrositing_engine import compute_micrositing
from app.services.nasa_power import fetch_nasa_environmental_data
from app.services.prediction_engine import predict_solar_potential, predict_wind_potential
from app.services.suitability_scoring import compute_suitability_score

logger = logging.getLogger(__name__)


def _validate_coordinates(latitude: float, longitude: float) -> None:
    """Validate lat/lon range."""
    if not (-90.0 <= latitude <= 90.0):
        raise ValueError(
            f"Invalid latitude: {latitude}. Must be between -90 and 90.")
    if not (-180.0 <= longitude <= 180.0):
        raise ValueError(
            f"Invalid longitude: {longitude}. Must be between -180 and 180.")


async def run_full_analysis(
    *,
    latitude: float,
    longitude: float,
    system_capacity_kw: float = 1000.0,
    land_area_sqkm: float = 5.0,
    elevation_m: float = 0.0,
    slope_deg: float = 0.0,
    energy_type: str = "hybrid",
    fit_usd_per_mwh: float = 65.0,
    ndvi: Optional[float] = None,
    land_cover: Optional[str] = None,
    suitability_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Run the complete analysis pipeline end-to-end.
    Returns a single consolidated response with all stages' outputs.
    """
    # ── Validation ──────────────────────────────────────────────────────
    _validate_coordinates(latitude, longitude)
    if system_capacity_kw <= 0:
        raise ValueError("system_capacity_kw must be positive.")
    if land_area_sqkm < 0:
        raise ValueError("land_area_sqkm must be non-negative.")

    logger.info(
        "Starting full analysis pipeline for (%.4f, %.4f) | %s | %.0f kW | %.1f km²",
        latitude, longitude, energy_type, system_capacity_kw, land_area_sqkm,
    )

    # ── Stage 1: Environmental Data + Infrastructure + Conflicts ────────
    # Run all external API calls concurrently
    nasa_task = fetch_nasa_environmental_data(latitude, longitude)
    osm_task = fetch_osm_infrastructure(latitude, longitude, radius_m=10000)
    conflict_task = detect_land_use_conflicts(latitude, longitude)

    nasa_data, osm_data, conflict_data = await asyncio.gather(
        nasa_task, osm_task, conflict_task
    )

    ghi = float(nasa_data.get("annual_solar_irradiance_kwh_m2_day", 0.0))
    wind_speed = float(nasa_data.get("annual_wind_speed_50m_m_s", 0.0))
    avg_temp = float(nasa_data.get("annual_avg_temp_c", 25.0))

    # Infrastructure distances
    dist_grid_km = osm_data.get(
        "nearest_substation_km") or osm_data.get("nearest_power_line_km")
    dist_road_km = osm_data.get("nearest_major_road_km")

    # Infer land cover if not provided
    effective_land_cover = land_cover or infer_land_cover_from_conflicts(
        conflict_data)

    logger.info(
        "Stage 1 complete: GHI=%.2f, Wind=%.2f m/s, Temp=%.1f°C, LandCover=%s",
        ghi, wind_speed, avg_temp, effective_land_cover,
    )

    # ── Stage 2: ML Prediction ──────────────────────────────────────────
    solar_prediction = predict_solar_potential(
        irradiance_kwh_m2_day=ghi,
        avg_temp_c=avg_temp,
        system_capacity_kw=system_capacity_kw,
    )
    wind_prediction = predict_wind_potential(
        wind_speed_m_s=wind_speed,
        system_capacity_kw=system_capacity_kw,
    )

    logger.info(
        "Stage 2 complete: Solar MWh=%.1f, Wind MWh=%.1f",
        solar_prediction.get("annual_energy_output_mwh", 0),
        wind_prediction.get("annual_energy_output_mwh", 0),
    )

    # ── Stage 3: Technical Feasibility ──────────────────────────────────
    feasibility = evaluate_feasibility(
        ghi_kwh_m2_day=ghi,
        wind_speed_m_s=wind_speed,
        slope_deg=slope_deg,
        dist_grid_km=dist_grid_km,
        dist_road_km=dist_road_km,
        land_cover=effective_land_cover,
        ndvi=ndvi,
        energy_type=energy_type,
    )

    # Use recommended energy type from feasibility check
    effective_energy_type = feasibility.get(
        "recommended_energy_type", energy_type)

    logger.info(
        "Stage 3 complete: Feasible=%s, Score=%.1f, Type=%s",
        feasibility["is_feasible"], feasibility["feasibility_score"], effective_energy_type,
    )

    # ── Stage 4: Suitability Scoring ────────────────────────────────────
    suitability = compute_suitability_score(
        ghi_kwh_m2_day=ghi,
        wind_speed_m_s=wind_speed,
        slope_deg=slope_deg,
        elevation_m=elevation_m,
        dist_road_km=dist_road_km,
        dist_grid_km=dist_grid_km,
        land_cover=effective_land_cover,
        energy_type=effective_energy_type,
        weights=suitability_weights,
    )

    logger.info(
        "Stage 4 complete: Score=%.1f (%s)",
        suitability["overall_score"], suitability["classification"],
    )

    # ── Stage 5: Micro-Siting / Capacity Planning ───────────────────────
    micrositing = compute_micrositing(
        total_land_area_sqkm=land_area_sqkm,
        energy_type=effective_energy_type,
    )

    solar_mw = micrositing.get("solar_capacity_mw", 0.0)
    wind_mw = micrositing.get("wind_capacity_mw", 0.0)

    logger.info(
        "Stage 5 complete: Solar=%.1f MW, Wind=%.1f MW, Total=%.1f MW",
        solar_mw, wind_mw, micrositing.get("total_capacity_mw", 0),
    )

    # ── Stage 6: Energy Yield ───────────────────────────────────────────
    energy_yield = compute_energy_yield(
        ghi_kwh_m2_day=ghi,
        wind_speed_m_s=wind_speed,
        avg_temp_c=avg_temp,
        slope_deg=slope_deg,
        energy_type=effective_energy_type,
        solar_capacity_mw=solar_mw,
        wind_capacity_mw=wind_mw,
    )

    annual_mwh = energy_yield.get("annual_energy_yield_mwh", 0.0)

    # Split for financial model
    if effective_energy_type == "hybrid":
        solar_yield = energy_yield.get("solar_yield", {})
        wind_yield_data = energy_yield.get("wind_yield", {})
        base_solar_mwh = solar_yield.get(
            "annual_yield_mwh", 0.0) if solar_yield else 0.0
        base_wind_mwh = wind_yield_data.get(
            "annual_yield_mwh", 0.0) if wind_yield_data else 0.0
    elif effective_energy_type == "solar":
        base_solar_mwh = annual_mwh
        base_wind_mwh = 0.0
    else:
        base_solar_mwh = 0.0
        base_wind_mwh = annual_mwh

    logger.info(
        "Stage 6 complete: Annual=%.1f MWh (Solar=%.1f, Wind=%.1f)",
        annual_mwh, base_solar_mwh, base_wind_mwh,
    )

    # ── Stage 7: Financial Analysis ─────────────────────────────────────
    financial = compute_financial_analysis(
        solar_capacity_mw=solar_mw,
        wind_capacity_mw=wind_mw,
        base_solar_mwh=base_solar_mwh,
        base_wind_mwh=base_wind_mwh,
        fit_usd_per_mwh=fit_usd_per_mwh,
    )
    financial["technical_feasibility"] = feasibility["is_feasible"]

    logger.info(
        "Stage 7 complete: CAPEX=$%s, NPV=$%s, LCOE=$%.2f, Payback=%s yrs",
        f"{financial['estimated_project_cost_usd']:,.0f}",
        f"{financial['npv_usd']:,.0f}",
        financial["lcoe_usd_per_mwh"],
        financial.get("payback_period_years", "N/A"),
    )

    # ── Stage 8: Final Recommendation ───────────────────────────────────
    recommendation = _build_recommendation(
        feasibility=feasibility,
        suitability=suitability,
        energy_yield=energy_yield,
        financial=financial,
        micrositing=micrositing,
    )

    # ── Build consolidated response ─────────────────────────────────────
    result = {
        "status": "success",
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "environmental_data": nasa_data,
        "infrastructure_data": osm_data,
        "land_use_conflicts": conflict_data,
        "predictions": {
            "solar": solar_prediction,
            "wind": wind_prediction,
        },
        "feasibility": feasibility,
        "suitability": suitability,
        "micrositing": micrositing,
        "energy_yield": energy_yield,
        "financial": financial,
        "recommendation": recommendation,
        "ai_narrative": None,  # Filled below
    }

    # ── Stage 9: AI Narrative (non-blocking) ────────────────────────────
    try:
        narrative_result = generate_investment_narrative(result)
        result["ai_narrative"] = narrative_result
    except Exception as e:
        logger.warning("AI narrative generation failed: %s", e)
        result["ai_narrative"] = {
            "narrative": None,
            "available": False,
            "error": f"AI summary unavailable — {type(e).__name__}",
        }

    logger.info("Full analysis pipeline complete for (%.4f, %.4f)",
                latitude, longitude)
    return result


def _build_recommendation(
    *,
    feasibility: Dict[str, Any],
    suitability: Dict[str, Any],
    energy_yield: Dict[str, Any],
    financial: Dict[str, Any],
    micrositing: Dict[str, Any],
) -> Dict[str, Any]:
    """Build final recommendation summary."""
    is_feasible = feasibility.get("is_feasible", False)
    score = suitability.get("overall_score", 0)
    classification = suitability.get("classification", "Unknown")
    npv = financial.get("npv_usd", 0)

    if not is_feasible:
        verdict = "Not Recommended"
        summary = "Site fails one or more hard technical constraints. Deployment is not viable without significant remediation."
        confidence = "High"
    elif score >= 70 and npv > 0:
        verdict = "Strongly Recommended"
        summary = f"Site scores {score:.0f}/100 ({classification}) with positive NPV of ${npv:,.0f}. Strong candidate for deployment."
        confidence = "High"
    elif score >= 50 and npv > 0:
        verdict = "Recommended with Conditions"
        summary = f"Site scores {score:.0f}/100 ({classification}) with positive NPV. Viable but may require infrastructure improvements."
        confidence = "Medium"
    elif score >= 50:
        verdict = "Marginal"
        summary = f"Site scores {score:.0f}/100 but financial returns are weak (NPV ${npv:,.0f}). Consider adjusting tariff assumptions or capacity."
        confidence = "Medium"
    else:
        verdict = "Not Recommended"
        summary = f"Site scores only {score:.0f}/100 ({classification}). Financial viability is poor."
        confidence = "High"

    dp = micrositing.get("deployment_plan", {})

    return {
        "verdict": verdict,
        "confidence": confidence,
        "summary": summary,
        "recommended_technology": dp.get("recommended_technology", "N/A"),
        "recommended_capacity_mw": dp.get("recommended_capacity_mw", 0),
        "expansion_potential": dp.get("expansion_status", "Unknown"),
        "suitability_score": score,
        "suitability_class": classification,
        "is_feasible": is_feasible,
    }
