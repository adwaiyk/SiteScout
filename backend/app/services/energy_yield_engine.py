"""
Energy Yield Engine — SiteScout Milestone 4
Solar, wind, and hybrid yield calculations using exact spec formulas.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


# ── Solar Yield ─────────────────────────────────────────────────────────

def compute_solar_yield(
    *,
    ghi_kwh_m2_day: float,
    avg_temp_c: float,
    slope_deg: float = 0.0,
    installed_capacity_mw: float = 1.0,
) -> Dict[str, Any]:
    """
    Compute solar energy yield using exact spec formulas:
    T_cell = T_ambient + 0.03 * (GHI / 5.0) * 1000
    temp_loss = clip(0.004 * (T_cell - 25), -0.05, 0.30)
    PSH = max(0, GHI / 1.0)
    PR_pct = clip(82.0 - (T_ambient - 25) * 0.4, 50, 90)
    Shading_Loss_pct = min(15.0, slope_deg * 0.8)
    Net_PR = (PR_pct / 100) * (1 - Shading_Loss_pct / 100)
    Daily_Yield_kWh_per_MW = 1000 * PSH * Net_PR
    """
    if ghi_kwh_m2_day <= 0 or installed_capacity_mw <= 0:
        return {
            "daily_yield_kwh_per_mw": 0.0,
            "annual_yield_mwh": 0.0,
            "capacity_factor_pct": 0.0,
            "performance_ratio_pct": 0.0,
            "t_cell_c": avg_temp_c,
            "temp_loss_fraction": 0.0,
            "shading_loss_pct": 0.0,
        }

    t_cell = avg_temp_c + 0.03 * (ghi_kwh_m2_day / 5.0) * 1000.0
    temp_loss = _clip(0.004 * (t_cell - 25.0), -0.05, 0.30)
    psh = max(0.0, ghi_kwh_m2_day / 1.0)
    pr_pct = _clip(82.0 - (avg_temp_c - 25.0) * 0.4, 50.0, 90.0)
    shading_loss_pct = min(15.0, slope_deg * 0.8)
    net_pr = (pr_pct / 100.0) * (1.0 - shading_loss_pct / 100.0)

    daily_yield_kwh_per_mw = 1000.0 * psh * net_pr
    annual_yield_mwh = daily_yield_kwh_per_mw * 365.0 * installed_capacity_mw / 1000.0

    # Capacity factor
    max_annual_mwh = installed_capacity_mw * 8760.0
    capacity_factor_pct = (annual_yield_mwh / max_annual_mwh * 100.0) if max_annual_mwh > 0 else 0.0

    return {
        "daily_yield_kwh_per_mw": round(daily_yield_kwh_per_mw, 2),
        "annual_yield_mwh": round(annual_yield_mwh, 2),
        "capacity_factor_pct": round(capacity_factor_pct, 2),
        "performance_ratio_pct": round(net_pr * 100.0, 2),
        "t_cell_c": round(t_cell, 1),
        "temp_loss_fraction": round(temp_loss, 4),
        "shading_loss_pct": round(shading_loss_pct, 2),
    }


# ── Wind Yield ──────────────────────────────────────────────────────────

def compute_wind_yield(
    *,
    wind_speed_m_s: float,
    avg_temp_c: float = 15.0,
    slope_deg: float = 0.0,
    installed_capacity_mw: float = 1.0,
) -> Dict[str, Any]:
    """
    Compute wind energy yield using exact spec formulas:
    rho = 1.225 - (T_ambient - 15) * 0.003
    WPD = 0.5 * rho * (wind_speed ** 3)
    TI_pct = min(25, 10 + slope_deg * 1.0)
    Power curve (2MW unit turbine):
      if ws < 3 or ws > 25: 0
      elif 3 <= ws < 12: 2000 * ((ws³ - 27) / (1728 - 27))
      else: 2000
    Daily_Wind_Yield_kWh = Yield_kW * 24 * 0.40
    CF_wind = clip((ws - 3) / 9 * 0.45, 0.10, 0.55)
    AEP_wind_MWh_per_MW = CF_wind * 8760
    """
    if installed_capacity_mw <= 0:
        return {
            "daily_yield_kwh": 0.0,
            "annual_yield_mwh": 0.0,
            "capacity_factor_pct": 0.0,
            "wind_power_density_w_m2": 0.0,
            "turbulence_intensity_pct": 0.0,
            "air_density_kg_m3": 1.225,
            "aep_mwh_per_mw": 0.0,
        }

    rho = 1.225 - (avg_temp_c - 15.0) * 0.003
    wpd = 0.5 * rho * (wind_speed_m_s ** 3)
    ti_pct = min(25.0, 10.0 + slope_deg * 1.0)

    # 2MW unit turbine power curve
    if wind_speed_m_s < 3.0 or wind_speed_m_s > 25.0:
        unit_yield_kw = 0.0
    elif 3.0 <= wind_speed_m_s < 12.0:
        unit_yield_kw = 2000.0 * ((wind_speed_m_s ** 3 - 27.0) / (1728.0 - 27.0))
    else:
        unit_yield_kw = 2000.0

    daily_wind_yield_kwh = unit_yield_kw * 24.0 * 0.40

    # Capacity factor and AEP
    cf_wind = _clip((wind_speed_m_s - 3.0) / 9.0 * 0.45, 0.10, 0.55)
    if wind_speed_m_s < 3.0:
        cf_wind = 0.0

    aep_mwh_per_mw = cf_wind * 8760.0
    annual_yield_mwh = aep_mwh_per_mw * installed_capacity_mw

    capacity_factor_pct = cf_wind * 100.0

    return {
        "daily_yield_kwh": round(daily_wind_yield_kwh, 2),
        "annual_yield_mwh": round(annual_yield_mwh, 2),
        "capacity_factor_pct": round(capacity_factor_pct, 2),
        "wind_power_density_w_m2": round(wpd, 2),
        "turbulence_intensity_pct": round(ti_pct, 2),
        "air_density_kg_m3": round(rho, 4),
        "aep_mwh_per_mw": round(aep_mwh_per_mw, 2),
    }


# ── Hybrid Yield ────────────────────────────────────────────────────────

def compute_hybrid_yield(
    *,
    ghi_kwh_m2_day: float,
    wind_speed_m_s: float,
    avg_temp_c: float,
    slope_deg: float = 0.0,
    solar_capacity_mw: float = 0.5,
    wind_capacity_mw: float = 0.5,
) -> Dict[str, Any]:
    """Combine solar + wind yield proportionally to allocated capacity."""
    solar = compute_solar_yield(
        ghi_kwh_m2_day=ghi_kwh_m2_day,
        avg_temp_c=avg_temp_c,
        slope_deg=slope_deg,
        installed_capacity_mw=solar_capacity_mw,
    )
    wind = compute_wind_yield(
        wind_speed_m_s=wind_speed_m_s,
        avg_temp_c=avg_temp_c,
        slope_deg=slope_deg,
        installed_capacity_mw=wind_capacity_mw,
    )

    total_annual_mwh = solar["annual_yield_mwh"] + wind["annual_yield_mwh"]
    total_capacity_mw = solar_capacity_mw + wind_capacity_mw
    max_annual_mwh = total_capacity_mw * 8760.0
    combined_cf = (total_annual_mwh / max_annual_mwh * 100.0) if max_annual_mwh > 0 else 0.0

    return {
        "solar_yield": solar,
        "wind_yield": wind,
        "total_annual_yield_mwh": round(total_annual_mwh, 2),
        "total_capacity_mw": round(total_capacity_mw, 2),
        "combined_capacity_factor_pct": round(combined_cf, 2),
        "solar_fraction": round(solar_capacity_mw / total_capacity_mw, 3) if total_capacity_mw > 0 else 0.5,
        "wind_fraction": round(wind_capacity_mw / total_capacity_mw, 3) if total_capacity_mw > 0 else 0.5,
    }


def compute_energy_yield(
    *,
    ghi_kwh_m2_day: float,
    wind_speed_m_s: float,
    avg_temp_c: float,
    slope_deg: float = 0.0,
    energy_type: str = "hybrid",
    solar_capacity_mw: float = 1.0,
    wind_capacity_mw: float = 1.0,
) -> Dict[str, Any]:
    """
    Top-level energy yield computation.
    Dispatches to solar, wind, or hybrid based on energy_type.
    """
    if energy_type == "solar":
        solar = compute_solar_yield(
            ghi_kwh_m2_day=ghi_kwh_m2_day,
            avg_temp_c=avg_temp_c,
            slope_deg=slope_deg,
            installed_capacity_mw=solar_capacity_mw,
        )
        return {
            "energy_type": "solar",
            "annual_energy_yield_mwh": solar["annual_yield_mwh"],
            "capacity_factor_pct": solar["capacity_factor_pct"],
            "total_capacity_mw": solar_capacity_mw,
            "solar_yield": solar,
            "wind_yield": None,
        }
    elif energy_type == "wind":
        wind = compute_wind_yield(
            wind_speed_m_s=wind_speed_m_s,
            avg_temp_c=avg_temp_c,
            slope_deg=slope_deg,
            installed_capacity_mw=wind_capacity_mw,
        )
        return {
            "energy_type": "wind",
            "annual_energy_yield_mwh": wind["annual_yield_mwh"],
            "capacity_factor_pct": wind["capacity_factor_pct"],
            "total_capacity_mw": wind_capacity_mw,
            "solar_yield": None,
            "wind_yield": wind,
        }
    else:  # hybrid
        hybrid = compute_hybrid_yield(
            ghi_kwh_m2_day=ghi_kwh_m2_day,
            wind_speed_m_s=wind_speed_m_s,
            avg_temp_c=avg_temp_c,
            slope_deg=slope_deg,
            solar_capacity_mw=solar_capacity_mw,
            wind_capacity_mw=wind_capacity_mw,
        )
        return {
            "energy_type": "hybrid",
            "annual_energy_yield_mwh": hybrid["total_annual_yield_mwh"],
            "capacity_factor_pct": hybrid["combined_capacity_factor_pct"],
            "total_capacity_mw": hybrid["total_capacity_mw"],
            "solar_yield": hybrid["solar_yield"],
            "wind_yield": hybrid["wind_yield"],
            "solar_fraction": hybrid["solar_fraction"],
            "wind_fraction": hybrid["wind_fraction"],
        }
