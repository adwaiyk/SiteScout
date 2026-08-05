from __future__ import annotations
import logging
import math
from typing import Any, Dict, Optional
logger = logging.getLogger(__name__)
DEFAULT_POWER_FACTOR = 0.9
VOLTAGE_LINE_RATINGS: Dict[float, float] = {11.0: 175.0, 33.0: 350.0, 66.0: 500.0, 132.0: 700.0, 220.0: 1000.0, 400.0: 1500.0}
VOLTAGE_CLASSES = sorted(VOLTAGE_LINE_RATINGS.keys())

def estimate_substation_voltage_kv(substation_distance_km: Optional[float], power_line_distance_km: Optional[float], infrastructure_count: int) -> float:
    effective_distance = None
    if substation_distance_km is not None:
        effective_distance = substation_distance_km
    if power_line_distance_km is not None:
        if effective_distance is None or power_line_distance_km < effective_distance:
            effective_distance = power_line_distance_km
    if effective_distance is None:
        effective_distance = 50.0
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
    if infrastructure_count > 15:
        idx = VOLTAGE_CLASSES.index(base_voltage) if base_voltage in VOLTAGE_CLASSES else 2
        upgraded_idx = min(idx + 1, len(VOLTAGE_CLASSES) - 1)
        base_voltage = VOLTAGE_CLASSES[upgraded_idx]
    elif infrastructure_count < 3:
        idx = VOLTAGE_CLASSES.index(base_voltage) if base_voltage in VOLTAGE_CLASSES else 2
        downgraded_idx = max(idx - 1, 0)
        base_voltage = VOLTAGE_CLASSES[downgraded_idx]
    return base_voltage

def get_line_rating_for_voltage(voltage_kv: float) -> float:
    if voltage_kv in VOLTAGE_LINE_RATINGS:
        return VOLTAGE_LINE_RATINGS[voltage_kv]
    for v in reversed(VOLTAGE_CLASSES):
        if v <= voltage_kv:
            return VOLTAGE_LINE_RATINGS[v]
    return VOLTAGE_LINE_RATINGS[VOLTAGE_CLASSES[0]]

def estimate_existing_generation_mw(infrastructure_count: int, substation_distance_km: Optional[float]) -> float:
    base_gen = infrastructure_count * 2.0
    if substation_distance_km is not None:
        if substation_distance_km < 5.0:
            base_gen += 15.0
        elif substation_distance_km < 15.0:
            base_gen += 5.0
    return round(max(0.0, base_gen), 2)

def compute_grid_hosting_capacity(site_name: str, substation_distance_km: Optional[float], power_line_distance_km: Optional[float], road_distance_km: Optional[float], infrastructure_count: int) -> Dict[str, Any]:
    voltage_kv = estimate_substation_voltage_kv(substation_distance_km, power_line_distance_km, infrastructure_count)
    line_rating_a = get_line_rating_for_voltage(voltage_kv)
    thermal_limit_mw = math.sqrt(3) * voltage_kv * line_rating_a * DEFAULT_POWER_FACTOR / 1000.0
    existing_gen_mw = estimate_existing_generation_mw(infrastructure_count, substation_distance_km)
    spare_capacity_mw = max(0.0, thermal_limit_mw - existing_gen_mw)
    effective_line_distance = power_line_distance_km or substation_distance_km or 50.0
    if effective_line_distance > 30.0:
        distance_derate = 0.7
    elif effective_line_distance > 15.0:
        distance_derate = 0.85
    elif effective_line_distance > 5.0:
        distance_derate = 0.95
    else:
        distance_derate = 1.0
    spare_capacity_mw *= distance_derate
    if spare_capacity_mw > 50.0:
        hosting_status = 'High Capacity'
    elif spare_capacity_mw > 10.0:
        hosting_status = 'Moderate'
    else:
        hosting_status = 'Constrained'
    max_interconnect = min(spare_capacity_mw * 0.8, thermal_limit_mw * 0.5)
    max_interconnect = max(0.0, max_interconnect)
    notes = _build_assessment_notes(voltage_kv, thermal_limit_mw, spare_capacity_mw, existing_gen_mw, hosting_status, max_interconnect, substation_distance_km, effective_line_distance)
    logger.info("Grid capacity for '%s': %.1f kV, thermal=%.1f MW, spare=%.1f MW, status=%s", site_name, voltage_kv, thermal_limit_mw, spare_capacity_mw, hosting_status)
    return {'substation_distance_km': substation_distance_km, 'estimated_voltage_kv': voltage_kv, 'line_distance_km': power_line_distance_km, 'estimated_line_rating_a': line_rating_a, 'existing_generation_nearby_mw': existing_gen_mw, 'thermal_limit_mw': round(thermal_limit_mw, 2), 'estimated_spare_capacity_mw': round(spare_capacity_mw, 2), 'hosting_status': hosting_status, 'max_recommended_interconnect_mw': round(max_interconnect, 2), 'assessment_notes': notes}

def _build_assessment_notes(voltage_kv: float, thermal_limit_mw: float, spare_capacity_mw: float, existing_gen_mw: float, hosting_status: str, max_interconnect_mw: float, substation_distance_km: Optional[float], line_distance_km: float) -> str:
    parts = []
    parts.append(f'Grid assessment based on estimated {voltage_kv:.0f} kV infrastructure with thermal capacity of {thermal_limit_mw:.1f} MW.')
    if substation_distance_km is not None:
        parts.append(f'Nearest substation is {substation_distance_km:.1f} km away.')
    else:
        parts.append('No substations detected within search radius.')
    parts.append(f'Estimated existing generation nearby: {existing_gen_mw:.1f} MW, leaving approximately {spare_capacity_mw:.1f} MW of spare hosting capacity.')
    if hosting_status == 'High Capacity':
        parts.append(f'Status: HIGH CAPACITY — the grid can likely accommodate up to {max_interconnect_mw:.1f} MW of new generation without major upgrades.')
    elif hosting_status == 'Moderate':
        parts.append(f'Status: MODERATE — interconnection of up to {max_interconnect_mw:.1f} MW is feasible but will require detailed network studies and possibly minor line augmentation.')
    else:
        parts.append(f'Status: CONSTRAINED — only {max_interconnect_mw:.1f} MW recommended. Significant grid augmentation (new lines, transformer upgrades) likely required for larger installations.')
    if line_distance_km > 20.0:
        parts.append('Note: Long line distance (>20 km) increases connection costs and transmission losses. Consider dedicated feeder construction.')
    return ' '.join(parts)
