"""
Site Suitability Scoring — SiteScout Milestone 4
Advanced 5-Component Weighted Matrix Model (0–100 scale).
Coexists with the existing ml_engine.py weighted scoring engine.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


# ── Score Normalization Functions (0–100 scale) ─────────────────────────

def normalize_solar_irradiance(ghi: float) -> float:
    """Solar Resource Score: clip((GHI - 2.0) / 5.0 * 100, 0, 100)"""
    return _clip((ghi - 2.0) / 5.0 * 100.0, 0.0, 100.0)


def normalize_wind_speed(ws: float) -> float:
    """Wind Resource Score: clip((Wind_Speed - 3.0) / 9.0 * 100, 0, 100)"""
    return _clip((ws - 3.0) / 9.0 * 100.0, 0.0, 100.0)


def normalize_slope(slope_deg: float, energy_type: str = "solar") -> float:
    """Slope score varies by energy type."""
    if energy_type == "wind":
        return max(0.0, 100.0 - slope_deg * 5.0)
    return max(0.0, 100.0 - slope_deg * 10.0)


def normalize_dist_grid(dist_km: float) -> float:
    """Grid Score: max(0, 100 - dist_grid_km * 5.0)"""
    return max(0.0, 100.0 - dist_km * 5.0)


def normalize_dist_road(dist_m: float) -> float:
    """Road Score: max(0, 100 - dist_road_m / 20.0)"""
    return max(0.0, 100.0 - dist_m / 20.0)


# ── 5-Component Weighted Matrix Model ──────────────────────────────────

def compute_resource_score(ghi: float, wind_speed: float, energy_type: str = "hybrid") -> Dict[str, float]:
    """Compute resource component score."""
    solar_score = normalize_solar_irradiance(ghi)
    wind_score = normalize_wind_speed(wind_speed)

    if energy_type == "solar":
        combined = solar_score
    elif energy_type == "wind":
        combined = wind_score
    else:  # hybrid
        combined = 0.5 * solar_score + 0.5 * wind_score

    return {
        "solar_resource_score": round(solar_score, 2),
        "wind_resource_score": round(wind_score, 2),
        "combined_score": round(combined, 2),
    }


def compute_geographic_score(
    slope_deg: float,
    elevation_m: float,
    energy_type: str = "hybrid",
) -> Dict[str, float]:
    """Compute geographic component score with solar/wind variants."""
    # Solar geographic
    solar_slope_score = max(0.0, 100.0 - slope_deg * 10.0)
    solar_elevation_score = max(0.0, 100.0 - elevation_m * 0.05)
    solar_geo = 0.7 * solar_slope_score + 0.3 * solar_elevation_score

    # Wind geographic
    wind_slope_score = max(0.0, 100.0 - slope_deg * 5.0)
    wind_elevation_score = min(100.0, elevation_m * 0.1)
    wind_geo = 0.5 * wind_slope_score + 0.5 * wind_elevation_score

    if energy_type == "solar":
        combined = solar_geo
    elif energy_type == "wind":
        combined = wind_geo
    else:  # hybrid
        combined = 0.5 * solar_geo + 0.5 * wind_geo

    return {
        "solar_geo_score": round(solar_geo, 2),
        "wind_geo_score": round(wind_geo, 2),
        "combined_score": round(combined, 2),
    }


def compute_infrastructure_score(
    dist_road_m: float,
    dist_grid_km: float,
) -> Dict[str, float]:
    """Compute infrastructure component score."""
    road_score = normalize_dist_road(dist_road_m)
    grid_score = normalize_dist_grid(dist_grid_km)
    combined = 0.5 * road_score + 0.5 * grid_score

    return {
        "road_score": round(road_score, 2),
        "grid_score": round(grid_score, 2),
        "combined_score": round(combined, 2),
    }


def compute_environmental_score(
    slope_deg: float,
    land_cover: str = "open",
) -> Dict[str, float]:
    """Compute environmental component score."""
    land_cover_lower = land_cover.lower() if land_cover else "open"

    baseline = 90.0 if slope_deg < 8.0 else 50.0

    if land_cover_lower in ("urban", "built-up", "buildings"):
        baseline = min(baseline, 25.0)

    return {
        "baseline_score": round(baseline, 2),
        "combined_score": round(baseline, 2),
    }


def compute_economic_score(
    slope_deg: float,
    land_cover: str = "open",
) -> Dict[str, float]:
    """Compute economic component score."""
    land_cover_lower = land_cover.lower() if land_cover else "open"

    baseline = max(10.0, 90.0 - slope_deg * 3.5)

    if land_cover_lower in ("urban", "built-up", "buildings"):
        baseline = min(baseline, 20.0)

    return {
        "baseline_score": round(baseline, 2),
        "combined_score": round(baseline, 2),
    }


# Default weights for the 5-component model
DEFAULT_WEIGHTS = {
    "resource": 0.35,
    "geographic": 0.25,
    "infrastructure": 0.15,
    "environmental": 0.15,
    "economic": 0.10,
}


def compute_suitability_score(
    *,
    ghi_kwh_m2_day: float,
    wind_speed_m_s: float,
    slope_deg: float = 0.0,
    elevation_m: float = 0.0,
    dist_road_km: Optional[float] = None,
    dist_grid_km: Optional[float] = None,
    land_cover: str = "open",
    energy_type: str = "hybrid",
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Compute the full 5-component suitability score.

    Overall_Score = (w_resource * Resource) + (w_geographic * Geographic) +
                    (w_infrastructure * Infrastructure) + (w_environmental * Environmental) +
                    (w_economic * Economic)
    """
    w = weights or DEFAULT_WEIGHTS.copy()

    # Defaults for missing distances
    dist_road_m = (dist_road_km * 1000.0) if dist_road_km is not None else 5000.0
    grid_km = dist_grid_km if dist_grid_km is not None else 50.0

    # Compute each component
    resource = compute_resource_score(ghi_kwh_m2_day, wind_speed_m_s, energy_type)
    geographic = compute_geographic_score(slope_deg, elevation_m, energy_type)
    infrastructure = compute_infrastructure_score(dist_road_m, grid_km)
    environmental = compute_environmental_score(slope_deg, land_cover)
    economic = compute_economic_score(slope_deg, land_cover)

    # Weighted sum
    overall_score = (
        w.get("resource", 0.35) * resource["combined_score"] +
        w.get("geographic", 0.25) * geographic["combined_score"] +
        w.get("infrastructure", 0.15) * infrastructure["combined_score"] +
        w.get("environmental", 0.15) * environmental["combined_score"] +
        w.get("economic", 0.10) * economic["combined_score"]
    )

    # Classification
    if overall_score >= 85:
        classification = "Excellent"
    elif overall_score >= 70:
        classification = "Highly Suitable"
    elif overall_score >= 50:
        classification = "Moderately Suitable"
    elif overall_score >= 30:
        classification = "Low Suitability"
    else:
        classification = "Unsuitable"

    logger.info(
        "Suitability score computed: %.1f (%s) — R=%.1f, G=%.1f, I=%.1f, E=%.1f, Ec=%.1f",
        overall_score, classification,
        resource["combined_score"], geographic["combined_score"],
        infrastructure["combined_score"], environmental["combined_score"],
        economic["combined_score"],
    )

    return {
        "overall_score": round(overall_score, 2),
        "classification": classification,
        "weights_used": w,
        "component_scores": {
            "resource": resource,
            "geographic": geographic,
            "infrastructure": infrastructure,
            "environmental": environmental,
            "economic": economic,
        },
    }


def rank_sites(
    sites: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Accept multiple evaluated sites, rank descending by overall_score.
    Each site dict must have at minimum 'site_name' and 'suitability' keys.
    """
    sorted_sites = sorted(
        sites,
        key=lambda s: s.get("suitability", {}).get("overall_score", 0.0),
        reverse=True,
    )
    for rank, site in enumerate(sorted_sites, 1):
        site["rank"] = rank
        site["is_top_site"] = rank == 1

    return sorted_sites
