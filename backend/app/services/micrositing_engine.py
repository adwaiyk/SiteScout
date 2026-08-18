"""
Micro-Siting / Capacity Planning Engine — SiteScout Milestone 4
Land allocation, turbine/panel counts, expansion feasibility, deployment plans.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────────────────────
SOLAR_HA_PER_MW = 1.8       # hectares per MW of solar
WIND_HA_PER_TURBINE = 12.0  # hectares per turbine
WIND_MW_PER_TURBINE = 3.0   # MW per turbine
SOLAR_PANELS_PER_MW = 2500
SOLAR_PANEL_AREA_SQM = 2.0  # m² per panel

# Expansion thresholds
EXPANSION_REMAINING_HA_HIGH = 20.0   # > 20 ha remaining = expandable
EXPANSION_REMAINING_HA_LOW = 5.0     # < 5 ha = not expandable


def compute_micrositing(
    *,
    total_land_area_sqkm: float,
    energy_type: str = "hybrid",
    grid_spare_capacity_mw: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Compute land allocation, capacity, and deployment plan.

    Solar_Allocated_Land_ha = Total_Land_ha * (0.5 if hybrid else 1.0)
    Max_Solar_MW = Solar_Allocated_Land_ha / 1.8
    Solar_Panel_Count = int(Max_Solar_MW * 2500)
    Solar_Footprint_sqm = Solar_Panel_Count * 2.0

    Wind_Allocated_Land_ha = Total_Land_ha * (0.5 if hybrid else 1.0)
    Turbine_Count = max(1, int(Wind_Allocated_Land_ha / 12.0))
    Max_Wind_MW = Turbine_Count * 3.0
    """
    total_land_ha = total_land_area_sqkm * 100.0  # 1 km² = 100 ha

    if total_land_ha <= 0:
        return _empty_result(energy_type)

    is_hybrid = energy_type == "hybrid"
    allocation_factor = 0.5 if is_hybrid else 1.0

    # ── Solar allocation ────────────────────────────────────────────────
    solar_data: Dict[str, Any] = {}
    solar_mw = 0.0
    solar_used_ha = 0.0

    if energy_type in ("solar", "hybrid"):
        solar_allocated_ha = total_land_ha * allocation_factor
        max_solar_mw = solar_allocated_ha / SOLAR_HA_PER_MW
        solar_panel_count = int(max_solar_mw * SOLAR_PANELS_PER_MW)
        solar_footprint_sqm = solar_panel_count * SOLAR_PANEL_AREA_SQM
        solar_used_ha = max_solar_mw * SOLAR_HA_PER_MW
        solar_mw = max_solar_mw

        solar_data = {
            "allocated_land_ha": round(solar_allocated_ha, 2),
            "max_capacity_mw": round(max_solar_mw, 2),
            "panel_count": solar_panel_count,
            "footprint_sqm": round(solar_footprint_sqm, 2),
            "footprint_ha": round(solar_footprint_sqm / 10000.0, 2),
            "land_utilization_pct": round(solar_used_ha / solar_allocated_ha * 100, 1) if solar_allocated_ha > 0 else 0.0,
        }

    # ── Wind allocation ─────────────────────────────────────────────────
    wind_data: Dict[str, Any] = {}
    wind_mw = 0.0
    wind_used_ha = 0.0

    if energy_type in ("wind", "hybrid"):
        wind_allocated_ha = total_land_ha * allocation_factor
        turbine_count = max(1, int(wind_allocated_ha / WIND_HA_PER_TURBINE))
        max_wind_mw = turbine_count * WIND_MW_PER_TURBINE
        wind_used_ha = turbine_count * WIND_HA_PER_TURBINE
        wind_mw = max_wind_mw

        wind_data = {
            "allocated_land_ha": round(wind_allocated_ha, 2),
            "max_capacity_mw": round(max_wind_mw, 2),
            "turbine_count": turbine_count,
            "ha_per_turbine": WIND_HA_PER_TURBINE,
            "mw_per_turbine": WIND_MW_PER_TURBINE,
            "land_utilization_pct": round(wind_used_ha / wind_allocated_ha * 100, 1) if wind_allocated_ha > 0 else 0.0,
        }

    # ── Totals ──────────────────────────────────────────────────────────
    total_capacity_mw = solar_mw + wind_mw
    total_used_ha = solar_used_ha + wind_used_ha
    remaining_ha = max(0.0, total_land_ha - total_used_ha)

    # ── Expansion feasibility ───────────────────────────────────────────
    grid_headroom_ok = grid_spare_capacity_mw is None or grid_spare_capacity_mw > total_capacity_mw * 0.2

    if remaining_ha > EXPANSION_REMAINING_HA_HIGH and grid_headroom_ok:
        expansion_status = "Expandable"
        expansion_detail = f"{remaining_ha:.0f} ha available for additional capacity. Grid infrastructure supports expansion."
    elif remaining_ha > EXPANSION_REMAINING_HA_LOW:
        expansion_status = "Limited Expansion"
        expansion_detail = f"Only {remaining_ha:.0f} ha remaining. Minor expansion possible with infrastructure upgrades."
    else:
        expansion_status = "Not Expandable"
        expansion_detail = f"Insufficient remaining land ({remaining_ha:.0f} ha) for meaningful capacity expansion."

    if not grid_headroom_ok:
        expansion_status = "Limited Expansion"
        expansion_detail += " Grid hosting capacity is constrained — interconnection upgrades required."

    # ── Deployment plan ─────────────────────────────────────────────────
    if energy_type == "hybrid":
        recommended = "Hybrid (Solar + Wind)"
        remarks = f"Hybrid deployment maximizes resource complementarity. {solar_mw:.1f} MW solar + {wind_mw:.1f} MW wind across {total_land_ha:.0f} ha."
    elif energy_type == "solar":
        recommended = "Solar PV"
        remarks = f"Solar-only deployment. {solar_mw:.1f} MW using {solar_data.get('panel_count', 0):,} panels across {total_land_ha:.0f} ha."
    else:
        recommended = "Wind"
        remarks = f"Wind-only deployment. {wind_mw:.1f} MW using {wind_data.get('turbine_count', 0)} turbines across {total_land_ha:.0f} ha."

    result = {
        "total_land_area_sqkm": round(total_land_area_sqkm, 2),
        "total_land_area_ha": round(total_land_ha, 2),
        "energy_type": energy_type,
        "solar": solar_data if solar_data else None,
        "wind": wind_data if wind_data else None,
        "total_capacity_mw": round(total_capacity_mw, 2),
        "solar_capacity_mw": round(solar_mw, 2),
        "wind_capacity_mw": round(wind_mw, 2),
        "total_used_land_ha": round(total_used_ha, 2),
        "remaining_land_ha": round(remaining_ha, 2),
        "expansion_status": expansion_status,
        "expansion_detail": expansion_detail,
        "deployment_plan": {
            "recommended_technology": recommended,
            "recommended_capacity_mw": round(total_capacity_mw, 2),
            "expansion_status": expansion_status,
            "optimization_remarks": remarks,
        },
    }

    logger.info(
        "Micrositing: %s | %.1f MW total (S=%.1f, W=%.1f) | %.0f ha used / %.0f ha total | %s",
        energy_type, total_capacity_mw, solar_mw, wind_mw,
        total_used_ha, total_land_ha, expansion_status,
    )

    return result


def _empty_result(energy_type: str) -> Dict[str, Any]:
    return {
        "total_land_area_sqkm": 0.0,
        "total_land_area_ha": 0.0,
        "energy_type": energy_type,
        "solar": None,
        "wind": None,
        "total_capacity_mw": 0.0,
        "solar_capacity_mw": 0.0,
        "wind_capacity_mw": 0.0,
        "total_used_land_ha": 0.0,
        "remaining_land_ha": 0.0,
        "expansion_status": "Not Expandable",
        "expansion_detail": "No land area available for deployment.",
        "deployment_plan": {
            "recommended_technology": "None",
            "recommended_capacity_mw": 0.0,
            "expansion_status": "Not Expandable",
            "optimization_remarks": "Insufficient land area for any deployment.",
        },
    }
