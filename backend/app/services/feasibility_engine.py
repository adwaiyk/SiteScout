"""
Technical Feasibility Engine — SiteScout Milestone 4
Hard constraint validation + soft scoring for site deployment feasibility.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Hard Constraint Thresholds ──────────────────────────────────────────
NDVI_EXCLUSION_THRESHOLD = 0.40
SENSITIVE_LAND_COVERS = {"forest", "water", "urban", "buildings", "built-up"}
EXTREME_TERRAIN_SLOPE_DEG = 15.0
SOLAR_PANEL_SLOPE_LIMIT_DEG = 10.0
TURBINE_CIVIL_SLOPE_LIMIT_DEG = 18.0
MIN_COMMERCIAL_SOLAR_GHI = 3.5        # kWh/m²/day
MIN_COMMERCIAL_WIND_SPEED = 4.0       # m/s
MAX_GRID_DISTANCE_KM = 15.0
MAX_ROAD_DISTANCE_M = 2000.0


def _check_hard_constraints(
    *,
    ghi_kwh_m2_day: float,
    wind_speed_m_s: float,
    slope_deg: float,
    dist_grid_km: Optional[float],
    dist_road_m: Optional[float],
    land_cover: str,
    ndvi: Optional[float],
    energy_type: str,
) -> List[Dict[str, Any]]:
    """Evaluate all hard constraints. Returns a list of constraint results."""
    constraints: List[Dict[str, Any]] = []
    land_cover_lower = land_cover.lower() if land_cover else "unknown"

    # 1. NDVI check
    if ndvi is not None and ndvi > NDVI_EXCLUSION_THRESHOLD:
        constraints.append({
            "constraint": "High Vegetation Exclusion",
            "threshold": f"NDVI > {NDVI_EXCLUSION_THRESHOLD}",
            "actual_value": round(ndvi, 3),
            "passed": False,
            "severity": "hard",
            "detail": f"NDVI {ndvi:.3f} exceeds vegetation threshold — likely dense vegetation cover."
        })
    elif ndvi is not None:
        constraints.append({
            "constraint": "High Vegetation Exclusion",
            "threshold": f"NDVI > {NDVI_EXCLUSION_THRESHOLD}",
            "actual_value": round(ndvi, 3),
            "passed": True,
            "severity": "hard",
            "detail": "Vegetation density within acceptable range."
        })
    else:
        constraints.append({
            "constraint": "High Vegetation Exclusion",
            "threshold": f"NDVI > {NDVI_EXCLUSION_THRESHOLD}",
            "actual_value": None,
            "passed": True,
            "severity": "info",
            "detail": "NDVI data not available — constraint not evaluated. Manual survey recommended."
        })

    # 2. Sensitive land cover
    is_sensitive = land_cover_lower in SENSITIVE_LAND_COVERS
    constraints.append({
        "constraint": "Sensitive Land Cover Exclusion",
        "threshold": f"Not in {SENSITIVE_LAND_COVERS}",
        "actual_value": land_cover,
        "passed": not is_sensitive,
        "severity": "hard",
        "detail": f"Land cover '{land_cover}' {'is a restricted category' if is_sensitive else 'is acceptable'}."
    })

    # 3. Extreme terrain
    constraints.append({
        "constraint": "Extreme Terrain Grade Exclusion",
        "threshold": f"Slope ≤ {EXTREME_TERRAIN_SLOPE_DEG}°",
        "actual_value": round(slope_deg, 2),
        "passed": slope_deg <= EXTREME_TERRAIN_SLOPE_DEG,
        "severity": "hard",
        "detail": f"Slope {slope_deg:.1f}° {'exceeds' if slope_deg > EXTREME_TERRAIN_SLOPE_DEG else 'within'} extreme terrain limit."
    })

    # 4. Technology-specific slope limits
    if energy_type in ("solar", "hybrid"):
        constraints.append({
            "constraint": "Solar Panel Slope Limit",
            "threshold": f"Slope ≤ {SOLAR_PANEL_SLOPE_LIMIT_DEG}°",
            "actual_value": round(slope_deg, 2),
            "passed": slope_deg <= SOLAR_PANEL_SLOPE_LIMIT_DEG,
            "severity": "hard",
            "detail": f"Slope {slope_deg:.1f}° {'exceeds' if slope_deg > SOLAR_PANEL_SLOPE_LIMIT_DEG else 'within'} solar panel installation limit."
        })

    if energy_type in ("wind", "hybrid"):
        constraints.append({
            "constraint": "Turbine Civil Work Slope Limit",
            "threshold": f"Slope ≤ {TURBINE_CIVIL_SLOPE_LIMIT_DEG}°",
            "actual_value": round(slope_deg, 2),
            "passed": slope_deg <= TURBINE_CIVIL_SLOPE_LIMIT_DEG,
            "severity": "hard",
            "detail": f"Slope {slope_deg:.1f}° {'exceeds' if slope_deg > TURBINE_CIVIL_SLOPE_LIMIT_DEG else 'within'} turbine civil works limit."
        })

    # 5. Minimum solar GHI
    if energy_type in ("solar", "hybrid"):
        constraints.append({
            "constraint": "Minimum Commercial Solar GHI",
            "threshold": f"GHI ≥ {MIN_COMMERCIAL_SOLAR_GHI} kWh/m²/day",
            "actual_value": round(ghi_kwh_m2_day, 2),
            "passed": ghi_kwh_m2_day >= MIN_COMMERCIAL_SOLAR_GHI,
            "severity": "hard",
            "detail": f"Solar irradiance {ghi_kwh_m2_day:.2f} kWh/m²/day {'below' if ghi_kwh_m2_day < MIN_COMMERCIAL_SOLAR_GHI else 'meets'} commercial minimum."
        })

    # 6. Minimum wind speed
    if energy_type in ("wind", "hybrid"):
        constraints.append({
            "constraint": "Minimum Commercial Wind Speed",
            "threshold": f"Wind ≥ {MIN_COMMERCIAL_WIND_SPEED} m/s",
            "actual_value": round(wind_speed_m_s, 2),
            "passed": wind_speed_m_s >= MIN_COMMERCIAL_WIND_SPEED,
            "severity": "hard",
            "detail": f"Wind speed {wind_speed_m_s:.2f} m/s {'below' if wind_speed_m_s < MIN_COMMERCIAL_WIND_SPEED else 'meets'} commercial minimum."
        })

    # 7. Grid distance
    if dist_grid_km is not None:
        constraints.append({
            "constraint": "Max Economic Transmission Distance",
            "threshold": f"Grid ≤ {MAX_GRID_DISTANCE_KM} km",
            "actual_value": round(dist_grid_km, 2),
            "passed": dist_grid_km <= MAX_GRID_DISTANCE_KM,
            "severity": "hard",
            "detail": f"Grid distance {dist_grid_km:.1f} km {'exceeds' if dist_grid_km > MAX_GRID_DISTANCE_KM else 'within'} economic transmission limit."
        })
    else:
        constraints.append({
            "constraint": "Max Economic Transmission Distance",
            "threshold": f"Grid ≤ {MAX_GRID_DISTANCE_KM} km",
            "actual_value": None,
            "passed": True,
            "severity": "info",
            "detail": "Grid distance data not available — constraint not evaluated."
        })

    # 8. Road distance
    if dist_road_m is not None:
        constraints.append({
            "constraint": "Transport Equipment Road Limit",
            "threshold": f"Road ≤ {MAX_ROAD_DISTANCE_M} m",
            "actual_value": round(dist_road_m, 1),
            "passed": dist_road_m <= MAX_ROAD_DISTANCE_M,
            "severity": "hard",
            "detail": f"Road distance {dist_road_m:.0f} m {'exceeds' if dist_road_m > MAX_ROAD_DISTANCE_M else 'within'} transport equipment limit."
        })
    else:
        constraints.append({
            "constraint": "Transport Equipment Road Limit",
            "threshold": f"Road ≤ {MAX_ROAD_DISTANCE_M} m",
            "actual_value": None,
            "passed": True,
            "severity": "info",
            "detail": "Road distance data not available — constraint not evaluated."
        })

    return constraints


def _compute_soft_scores(
    *,
    dist_grid_km: Optional[float],
    dist_road_m: Optional[float],
    slope_deg: float,
) -> Dict[str, Any]:
    """Score soft constraints (infrastructure proximity, accessibility)."""
    # Infrastructure proximity score (0-100)
    grid_score = max(0.0, 100.0 - (dist_grid_km or 50.0) * 5.0)
    road_score = max(0.0, 100.0 - (dist_road_m or 5000.0) / 20.0)
    infra_score = 0.5 * grid_score + 0.5 * road_score

    # Accessibility score (0-100)
    access_score = max(0.0, 100.0 - slope_deg * 5.0)

    # Overall soft score
    soft_score = 0.6 * infra_score + 0.4 * access_score

    return {
        "infrastructure_proximity_score": round(infra_score, 2),
        "accessibility_score": round(access_score, 2),
        "overall_soft_score": round(soft_score, 2),
        "components": {
            "grid_proximity_score": round(grid_score, 2),
            "road_proximity_score": round(road_score, 2),
            "terrain_accessibility_score": round(access_score, 2),
        }
    }


def infer_land_cover_from_conflicts(conflict_data: Dict[str, Any]) -> str:
    """Derive land cover type from OSM conflict detector output."""
    hard_flags = conflict_data.get("hard_flags", [])
    warnings = conflict_data.get("warnings", [])
    all_flags = [f.lower() for f in hard_flags + warnings]

    for flag in all_flags:
        if "water" in flag:
            return "water"
        if "protected" in flag or "nature_reserve" in flag:
            return "forest"
    for flag in all_flags:
        if "forest" in flag:
            return "forest"
        if "urban" in flag or "built" in flag or "building" in flag:
            return "urban"
        if "agricultural" in flag or "farmland" in flag:
            return "agricultural"
    return "open"


def evaluate_feasibility(
    *,
    ghi_kwh_m2_day: float,
    wind_speed_m_s: float,
    slope_deg: float = 0.0,
    dist_grid_km: Optional[float] = None,
    dist_road_km: Optional[float] = None,
    land_cover: str = "open",
    ndvi: Optional[float] = None,
    energy_type: str = "hybrid",
) -> Dict[str, Any]:
    """
    Run full feasibility evaluation.

    Returns pass/fail per hard constraint, an overall feasibility score,
    and a structured constraint summary.
    """
    # Convert road distance to meters for threshold comparison
    dist_road_m = dist_road_km * 1000.0 if dist_road_km is not None else None

    # Determine best energy type if hybrid and one resource fails
    if energy_type == "hybrid":
        solar_viable = ghi_kwh_m2_day >= MIN_COMMERCIAL_SOLAR_GHI
        wind_viable = wind_speed_m_s >= MIN_COMMERCIAL_WIND_SPEED
        if solar_viable and not wind_viable:
            recommended_type = "solar"
        elif wind_viable and not solar_viable:
            recommended_type = "wind"
        elif solar_viable and wind_viable:
            recommended_type = "hybrid"
        else:
            recommended_type = "hybrid"  # let hard constraints catch it
    else:
        recommended_type = energy_type

    hard_constraints = _check_hard_constraints(
        ghi_kwh_m2_day=ghi_kwh_m2_day,
        wind_speed_m_s=wind_speed_m_s,
        slope_deg=slope_deg,
        dist_grid_km=dist_grid_km,
        dist_road_m=dist_road_m,
        land_cover=land_cover,
        ndvi=ndvi,
        energy_type=energy_type,
    )

    soft_scores = _compute_soft_scores(
        dist_grid_km=dist_grid_km,
        dist_road_m=dist_road_m,
        slope_deg=slope_deg,
    )

    # Determine overall pass/fail
    hard_failures = [c for c in hard_constraints if not c["passed"] and c["severity"] == "hard"]
    is_feasible = len(hard_failures) == 0

    # Overall feasibility score (0-100)
    if not is_feasible:
        # Penalize heavily for hard failures
        penalty = min(100, len(hard_failures) * 30)
        feasibility_score = max(0.0, soft_scores["overall_soft_score"] - penalty)
    else:
        feasibility_score = soft_scores["overall_soft_score"]

    total_constraints = len(hard_constraints)
    passed_constraints = len([c for c in hard_constraints if c["passed"]])

    logger.info(
        "Feasibility evaluation: %d/%d hard constraints passed, feasible=%s, score=%.1f",
        passed_constraints, total_constraints, is_feasible, feasibility_score,
    )

    return {
        "is_feasible": is_feasible,
        "feasibility_score": round(feasibility_score, 2),
        "recommended_energy_type": recommended_type,
        "hard_constraints": hard_constraints,
        "hard_constraint_summary": {
            "total": total_constraints,
            "passed": passed_constraints,
            "failed": total_constraints - passed_constraints,
            "failure_reasons": [c["constraint"] for c in hard_failures],
        },
        "soft_scores": soft_scores,
    }
