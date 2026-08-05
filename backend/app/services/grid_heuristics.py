"""
SiteScout — Grid Hosting Capacity Heuristic Service.

Rather than just reporting "distance to nearest substation", this service
estimates remaining grid capacity using standard electrical engineering
heuristics.

Thermal Limit (MW) ≈ √3 × Voltage(kV) × Line Rating(A) × Power Factor / 1000

The service classifies hosting capacity as:
  - High Capacity: >50 MW spare — straightforward interconnection
  - Moderate: 10–50 MW spare — feasible with network studies
  - Constrained: <10 MW spare — significant upgrades likely required
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Standard Electrical Engineering Constants & Lookup Tables
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Default power factor for grid-connected renewable plants
DEFAULT_POWER_FACTOR = 0.90

# Typical line current ratings (Amperes) by voltage class.
# Based on standard ACSR conductor ratings for overhead lines in India:
#   11 kV  → typically ACSR Dog/Rabbit → ~150–200 A
#   33 kV  → ACSR Panther/Zebra → ~300–400 A
#   66 kV  → ACSR Zebra/Moose → ~400–600 A
#   132 kV → ACSR Moose/twin bundle → ~600–800 A
#   220 kV → Twin/Triple ACSR → ~800–1200 A
#   400 kV → Quad ACSR → ~1200–2000 A
VOLTAGE_LINE_RATINGS: Dict[float, float] = {
    11.0: 175.0,
    33.0: 350.0,
    66.0: 500.0,
    132.0: 700.0,
    220.0: 1000.0,
    400.0: 1500.0,
}

# Voltage classes in ascending order for lookup
VOLTAGE_CLASSES = sorted(VOLTAGE_LINE_RATINGS.keys())


def estimate_substation_voltage_kv(
    substation_distance_km: Optional[float],
    power_line_distance_km: Optional[float],
    infrastructure_count: int,
) -> float:
    """
    Estimate the voltage class of the nearest substation based on distance
    and infrastructure density heuristics.

    Rationale:
      - Substations within ~10 km are typically 33 kV distribution level
      - Substations 10–25 km are typically 66 kV sub-transmission
      - Beyond 25 km, the nearest accessible grid is likely 132 kV+ transmission

    Infrastructure density refines the estimate:
      - High density (>15 features nearby) suggests a well-developed grid → higher voltage
      - Low density (<5 features) suggests rural/remote → lower voltage

    Parameters
    ----------
    substation_distance_km : float or None
        Distance to nearest substation. None if not found.
    power_line_distance_km : float or None
        Distance to nearest power line. None if not found.
    infrastructure_count : int
        Total infrastructure features found nearby.

    Returns
    -------
    float
        Estimated voltage in kV.
    """
    # Use the closer of substation or power line distance
    effective_distance = None
    if substation_distance_km is not None:
        effective_distance = substation_distance_km
    if power_line_distance_km is not None:
        if effective_distance is None or power_line_distance_km < effective_distance:
            effective_distance = power_line_distance_km

    # Default to 50 km if no infrastructure found (very remote)
    if effective_distance is None:
        effective_distance = 50.0

    # Base voltage estimate from distance
    if effective_distance < 5.0:
        base_voltage = 33.0
    elif effective_distance < 15.0:
        base_voltage = 33.0
    elif effective_distance < 25.0:
        base_voltage = 66.0
    elif effective_distance < 40.0:
        base_voltage = 132.0
    else:
        base_voltage = 132.0

    # Infrastructure density adjustment
    if infrastructure_count > 15:
        # Dense grid — likely higher voltage substations available
        idx = VOLTAGE_CLASSES.index(base_voltage) if base_voltage in VOLTAGE_CLASSES else 2
        upgraded_idx = min(idx + 1, len(VOLTAGE_CLASSES) - 1)
        base_voltage = VOLTAGE_CLASSES[upgraded_idx]
    elif infrastructure_count < 3:
        # Sparse grid — likely lower voltage
        idx = VOLTAGE_CLASSES.index(base_voltage) if base_voltage in VOLTAGE_CLASSES else 2
        downgraded_idx = max(idx - 1, 0)
        base_voltage = VOLTAGE_CLASSES[downgraded_idx]

    return base_voltage


def get_line_rating_for_voltage(voltage_kv: float) -> float:
    """
    Look up the typical line current rating for a given voltage class.

    If the voltage doesn't exactly match a known class, uses the nearest
    lower voltage class.
    """
    if voltage_kv in VOLTAGE_LINE_RATINGS:
        return VOLTAGE_LINE_RATINGS[voltage_kv]

    # Find nearest lower voltage class
    for v in reversed(VOLTAGE_CLASSES):
        if v <= voltage_kv:
            return VOLTAGE_LINE_RATINGS[v]

    # Fallback to lowest
    return VOLTAGE_LINE_RATINGS[VOLTAGE_CLASSES[0]]


def estimate_existing_generation_mw(
    infrastructure_count: int,
    substation_distance_km: Optional[float],
) -> float:
    """
    Estimate existing generation capacity nearby in MW.

    This is a rough proxy based on infrastructure density — areas with
    more power infrastructure typically have more existing generators
    (both conventional and renewable) competing for grid capacity.

    Parameters
    ----------
    infrastructure_count : int
        Total power infrastructure features found within search radius.
    substation_distance_km : float or None
        Distance to nearest substation.

    Returns
    -------
    float
        Estimated existing generation in MW.
    """
    # Base estimate: ~1–3 MW per infrastructure feature (very rough)
    base_gen = infrastructure_count * 2.0

    # Closer substations in India tend to serve areas with more existing generation
    if substation_distance_km is not None:
        if substation_distance_km < 5.0:
            base_gen += 15.0  # Urban/peri-urban — likely existing DG/rooftop solar
        elif substation_distance_km < 15.0:
            base_gen += 5.0   # Suburban — some existing generation
        # Beyond 15 km — minimal existing generation assumed

    return round(max(0.0, base_gen), 2)


def compute_grid_hosting_capacity(
    site_name: str,
    substation_distance_km: Optional[float],
    power_line_distance_km: Optional[float],
    road_distance_km: Optional[float],
    infrastructure_count: int,
) -> Dict[str, Any]:
    """
    Compute grid hosting capacity heuristic for a site.

    Parameters
    ----------
    site_name : str
        Human-readable site name.
    substation_distance_km : float or None
        Distance to nearest substation (km). None if not found.
    power_line_distance_km : float or None
        Distance to nearest power line (km). None if not found.
    road_distance_km : float or None
        Distance to nearest major road (km). None if not found.
    infrastructure_count : int
        Total power infrastructure features found nearby.

    Returns
    -------
    dict
        Complete grid capacity assessment including thermal limit,
        spare capacity, hosting status, and recommendations.
    """
    # ── Step 1: Estimate voltage class ───────────────────────────────────
    voltage_kv = estimate_substation_voltage_kv(
        substation_distance_km, power_line_distance_km, infrastructure_count
    )

    # ── Step 2: Get line rating ──────────────────────────────────────────
    line_rating_a = get_line_rating_for_voltage(voltage_kv)

    # ── Step 3: Compute thermal limit ────────────────────────────────────
    # Thermal Limit (MW) = √3 × V(kV) × I(A) × PF / 1000
    thermal_limit_mw = (
        math.sqrt(3) * voltage_kv * line_rating_a * DEFAULT_POWER_FACTOR
    ) / 1000.0

    # ── Step 4: Estimate existing generation ─────────────────────────────
    existing_gen_mw = estimate_existing_generation_mw(
        infrastructure_count, substation_distance_km
    )

    # ── Step 5: Calculate spare capacity ─────────────────────────────────
    spare_capacity_mw = max(0.0, thermal_limit_mw - existing_gen_mw)

    # ── Step 6: Apply distance-based derating ────────────────────────────
    # Longer lines have higher losses and voltage drop, reducing effective capacity
    effective_line_distance = power_line_distance_km or substation_distance_km or 50.0
    if effective_line_distance > 30.0:
        distance_derate = 0.70  # 30% reduction for very long lines
    elif effective_line_distance > 15.0:
        distance_derate = 0.85  # 15% reduction
    elif effective_line_distance > 5.0:
        distance_derate = 0.95  # 5% reduction
    else:
        distance_derate = 1.00  # No derating for close connections

    spare_capacity_mw *= distance_derate

    # ── Step 7: Classify hosting status ──────────────────────────────────
    if spare_capacity_mw > 50.0:
        hosting_status = "High Capacity"
    elif spare_capacity_mw > 10.0:
        hosting_status = "Moderate"
    else:
        hosting_status = "Constrained"

    # ── Step 8: Recommended maximum interconnect ─────────────────────────
    # Conservative: don't exceed 80% of spare capacity or 50% of thermal limit
    max_interconnect = min(
        spare_capacity_mw * 0.80,
        thermal_limit_mw * 0.50,
    )
    max_interconnect = max(0.0, max_interconnect)

    # ── Step 9: Build assessment narrative ───────────────────────────────
    notes = _build_assessment_notes(
        voltage_kv, thermal_limit_mw, spare_capacity_mw,
        existing_gen_mw, hosting_status, max_interconnect,
        substation_distance_km, effective_line_distance,
    )

    logger.info(
        "Grid capacity for '%s': %.1f kV, thermal=%.1f MW, spare=%.1f MW, status=%s",
        site_name, voltage_kv, thermal_limit_mw, spare_capacity_mw, hosting_status,
    )

    return {
        "substation_distance_km": substation_distance_km,
        "estimated_voltage_kv": voltage_kv,
        "line_distance_km": power_line_distance_km,
        "estimated_line_rating_a": line_rating_a,
        "existing_generation_nearby_mw": existing_gen_mw,
        "thermal_limit_mw": round(thermal_limit_mw, 2),
        "estimated_spare_capacity_mw": round(spare_capacity_mw, 2),
        "hosting_status": hosting_status,
        "max_recommended_interconnect_mw": round(max_interconnect, 2),
        "assessment_notes": notes,
    }


def _build_assessment_notes(
    voltage_kv: float,
    thermal_limit_mw: float,
    spare_capacity_mw: float,
    existing_gen_mw: float,
    hosting_status: str,
    max_interconnect_mw: float,
    substation_distance_km: Optional[float],
    line_distance_km: float,
) -> str:
    """Build a human-readable summary of the grid capacity assessment."""
    parts = []

    parts.append(
        f"Grid assessment based on estimated {voltage_kv:.0f} kV infrastructure "
        f"with thermal capacity of {thermal_limit_mw:.1f} MW."
    )

    if substation_distance_km is not None:
        parts.append(f"Nearest substation is {substation_distance_km:.1f} km away.")
    else:
        parts.append("No substations detected within search radius.")

    parts.append(
        f"Estimated existing generation nearby: {existing_gen_mw:.1f} MW, "
        f"leaving approximately {spare_capacity_mw:.1f} MW of spare hosting capacity."
    )

    if hosting_status == "High Capacity":
        parts.append(
            f"Status: HIGH CAPACITY — the grid can likely accommodate up to "
            f"{max_interconnect_mw:.1f} MW of new generation without major upgrades."
        )
    elif hosting_status == "Moderate":
        parts.append(
            f"Status: MODERATE — interconnection of up to {max_interconnect_mw:.1f} MW "
            f"is feasible but will require detailed network studies and possibly "
            f"minor line augmentation."
        )
    else:
        parts.append(
            f"Status: CONSTRAINED — only {max_interconnect_mw:.1f} MW recommended. "
            f"Significant grid augmentation (new lines, transformer upgrades) likely "
            f"required for larger installations."
        )

    if line_distance_km > 20.0:
        parts.append(
            "Note: Long line distance (>20 km) increases connection costs and "
            "transmission losses. Consider dedicated feeder construction."
        )

    return " ".join(parts)
