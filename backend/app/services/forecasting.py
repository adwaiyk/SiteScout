"""
SiteScout — Uncertainty-Aware Energy Forecasting Engine.

Produces P10/P50/P90 confidence bands (not misleading single-point estimates)
for monthly seasonality and 25-year lifespan projections with degradation.

P10 = Conservative (90% chance of exceeding this value)
P50 = Expected (median, 50/50)
P90 = Optimistic (only 10% chance of exceeding this value)

Architecture:
  Uses site environmental data (solar irradiance, wind speed) from
  ScanLog.full_analysis_json to compute realistic generation profiles
  with India-specific monthly seasonality patterns.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Tuple

from app.schemas.forecasting import (
    AnnualForecast,
    CumulativeProduction,
    ForecastResponse,
    MonthlyForecast,
)

logger = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Monthly Seasonality Profiles (India-specific)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Solar seasonality multipliers — relative to annual average.
# India: High in Mar-May (pre-monsoon), dip in Jul-Aug (monsoon cloud cover),
# recovery in Oct-Dec (post-monsoon clear skies).
SOLAR_SEASONALITY = [
    0.88,  # Jan — winter, shorter days, moderate irradiance
    0.95,  # Feb — improving, pre-spring
    1.08,  # Mar — excellent, clear pre-monsoon skies
    1.15,  # Apr — peak pre-monsoon irradiance
    1.12,  # May — very high, hot and clear
    0.92,  # Jun — monsoon onset, increasing cloud cover
    0.78,  # Jul — peak monsoon, heavy cloud cover
    0.80,  # Aug — continued monsoon
    0.90,  # Sep — monsoon retreat begins
    1.02,  # Oct — post-monsoon, clearing skies
    1.00,  # Nov — good clear conditions
    0.90,  # Dec — winter, shorter days
]

# Wind seasonality multipliers — India monsoon-driven wind patterns.
# Strong southwest monsoon winds Jun-Sep, calmer Oct-Feb.
WIND_SEASONALITY = [
    0.70,  # Jan — low wind season
    0.72,  # Feb — still calm
    0.80,  # Mar — beginning to pick up
    0.85,  # Apr — pre-monsoon acceleration
    0.95,  # May — building toward monsoon
    1.25,  # Jun — monsoon onset, strong SW winds
    1.35,  # Jul — peak monsoon winds
    1.30,  # Aug — sustained monsoon
    1.15,  # Sep — monsoon winds easing
    0.90,  # Oct — post-monsoon transition
    0.75,  # Nov — calming
    0.68,  # Dec — low wind season
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Quantile Spread Factors
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# P10/P90 spread around P50 reflects interannual weather variability.
# Based on typical solar/wind resource assessment uncertainty ranges:
#   Solar: ~±12-15% interannual variability
#   Wind:  ~±15-20% interannual variability
P10_MULTIPLIER_SOLAR = 0.85   # Conservative: 15% below expected
P90_MULTIPLIER_SOLAR = 1.12   # Optimistic: 12% above expected
P10_MULTIPLIER_WIND = 0.80    # Conservative: 20% below expected
P90_MULTIPLIER_WIND = 1.15    # Optimistic: 15% above expected

# Degradation rates (per year, cumulative)
SOLAR_DEGRADATION_RATE = 0.005   # 0.5% per year — industry standard for crystalline PV
WIND_DEGRADATION_RATE = 0.002    # 0.2% per year — mechanical wear, blade erosion

# Default project lifespan
DEFAULT_LIFESPAN_YEARS = 25

# Hours per month (approximate, for capacity factor calculations)
DAYS_PER_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
HOURS_PER_YEAR = 8760


def compute_energy_forecast(
    site_name: str,
    capacity_mw: float,
    system_loss_pct: float,
    solar_irradiance_kwh_m2_day: float,
    wind_speed_50m_m_s: float,
    solar_capacity_factor_pct: float,
    wind_capacity_factor_pct: float,
    avg_temp_c: float,
    lifespan_years: int = DEFAULT_LIFESPAN_YEARS,
) -> Dict[str, Any]:
    """
    Compute uncertainty-aware energy forecasts with P10/P50/P90 bands.

    Parameters
    ----------
    site_name : str
        Human-readable site name.
    capacity_mw : float
        Installed capacity in MW.
    system_loss_pct : float
        Total system losses as a percentage.
    solar_irradiance_kwh_m2_day : float
        Annual average solar irradiance (kWh/m²/day).
    wind_speed_50m_m_s : float
        Annual average wind speed at 50m height (m/s).
    solar_capacity_factor_pct : float
        Solar capacity factor from prediction engine (%).
    wind_capacity_factor_pct : float
        Wind capacity factor from prediction engine (%).
    avg_temp_c : float
        Annual average temperature (°C).
    lifespan_years : int
        Project lifespan for degradation modelling.

    Returns
    -------
    dict
        Contains monthly_forecasts, annual_forecasts, cumulative totals,
        energy_type, first_year_p50_mwh, and capacity_factor_pct.
    """
    system_loss_factor = 1.0 - (system_loss_pct / 100.0)

    # ── Determine energy type and base P50 annual generation ─────────────
    solar_mwh_annual = _compute_solar_annual_mwh(
        capacity_mw, solar_irradiance_kwh_m2_day, avg_temp_c, system_loss_factor
    )
    wind_mwh_annual = _compute_wind_annual_mwh(
        capacity_mw, wind_speed_50m_m_s, system_loss_factor
    )

    # Classify energy type based on which source dominates
    if solar_mwh_annual > 0 and wind_mwh_annual > 0:
        energy_type = "hybrid"
    elif solar_mwh_annual > 0:
        energy_type = "solar"
    else:
        energy_type = "wind"

    total_p50_annual = solar_mwh_annual + wind_mwh_annual

    # ── Compute blended P10/P90 multipliers ──────────────────────────────
    if total_p50_annual > 0:
        solar_fraction = solar_mwh_annual / total_p50_annual
        wind_fraction = wind_mwh_annual / total_p50_annual
    else:
        solar_fraction = 0.5
        wind_fraction = 0.5

    p10_mult = solar_fraction * P10_MULTIPLIER_SOLAR + wind_fraction * P10_MULTIPLIER_WIND
    p90_mult = solar_fraction * P90_MULTIPLIER_SOLAR + wind_fraction * P90_MULTIPLIER_WIND

    # Blended degradation rate
    degradation_rate = (
        solar_fraction * SOLAR_DEGRADATION_RATE + wind_fraction * WIND_DEGRADATION_RATE
    )

    # Blended seasonality
    blended_seasonality = [
        solar_fraction * SOLAR_SEASONALITY[m] + wind_fraction * WIND_SEASONALITY[m]
        for m in range(12)
    ]

    # ── Monthly forecasts (Year 1, no degradation) ───────────────────────
    monthly_forecasts: List[MonthlyForecast] = []
    for m in range(12):
        days = DAYS_PER_MONTH[m]
        month_fraction = days / 365.0
        month_p50 = total_p50_annual * month_fraction * blended_seasonality[m]
        month_p10 = month_p50 * p10_mult
        month_p90 = month_p50 * p90_mult

        monthly_forecasts.append(
            MonthlyForecast(
                month_index=m + 1,
                month_name=MONTH_NAMES[m],
                p10_mwh=round(month_p10, 2),
                p50_mwh=round(month_p50, 2),
                p90_mwh=round(month_p90, 2),
            )
        )

    # ── Annual forecasts with degradation ────────────────────────────────
    annual_forecasts: List[AnnualForecast] = []
    cumulative_p10 = 0.0
    cumulative_p50 = 0.0
    cumulative_p90 = 0.0

    for year in range(1, lifespan_years + 1):
        # Degradation: compound decay from year 2 onward
        deg_factor = (1.0 - degradation_rate) ** (year - 1)

        year_p50 = total_p50_annual * deg_factor
        year_p10 = year_p50 * p10_mult
        year_p90 = year_p50 * p90_mult

        cumulative_p10 += year_p10
        cumulative_p50 += year_p50
        cumulative_p90 += year_p90

        annual_forecasts.append(
            AnnualForecast(
                year=year,
                degradation_factor=round(deg_factor, 6),
                p10_mwh=round(year_p10, 2),
                p50_mwh=round(year_p50, 2),
                p90_mwh=round(year_p90, 2),
            )
        )

    # ── Capacity factor (effective, including losses) ────────────────────
    max_possible_mwh = capacity_mw * HOURS_PER_YEAR
    effective_cf = (
        (total_p50_annual / max_possible_mwh) * 100.0
        if max_possible_mwh > 0
        else 0.0
    )

    cumulative = CumulativeProduction(
        lifespan_years=lifespan_years,
        p10_total_mwh=round(cumulative_p10, 2),
        p50_total_mwh=round(cumulative_p50, 2),
        p90_total_mwh=round(cumulative_p90, 2),
    )

    return {
        "energy_type": energy_type,
        "monthly_forecasts": monthly_forecasts,
        "annual_forecasts": annual_forecasts,
        "cumulative": cumulative,
        "first_year_p50_mwh": round(total_p50_annual, 2),
        "capacity_factor_pct": round(effective_cf, 2),
    }


def _compute_solar_annual_mwh(
    capacity_mw: float,
    irradiance_kwh_m2_day: float,
    avg_temp_c: float,
    system_loss_factor: float,
) -> float:
    """
    Estimate annual solar PV generation in MWh.

    Uses a simplified performance ratio model:
      Annual MWh = Capacity(kW) × PSH × 365 × PR × SystemLoss / 1000

    Where:
      PSH (Peak Sun Hours) ≈ irradiance_kwh_m2_day (for fixed-tilt systems)
      PR (Performance Ratio) adjusted for temperature derating
    """
    if irradiance_kwh_m2_day <= 0:
        return 0.0

    capacity_kw = capacity_mw * 1000.0

    # Base performance ratio (typical for well-maintained fixed-tilt PV)
    base_pr = 0.80

    # Temperature derating: PV output drops ~0.4% per °C above 25°C (STC)
    temp_coefficient = -0.004
    temp_derate = max(0.0, (avg_temp_c - 25.0) * temp_coefficient)
    effective_pr = max(0.50, base_pr + temp_derate)  # Floor at 50%

    # Annual generation
    annual_mwh = (
        capacity_kw * irradiance_kwh_m2_day * 365.0 * effective_pr * system_loss_factor
    ) / 1000.0

    return max(0.0, annual_mwh)


def _compute_wind_annual_mwh(
    capacity_mw: float,
    wind_speed_m_s: float,
    system_loss_factor: float,
) -> float:
    """
    Estimate annual wind generation in MWh.

    Uses a capacity factor approach derived from wind speed:
      - Below 3 m/s (cut-in): no generation
      - 3–12 m/s: approximately linear CF ramp
      - Above 12 m/s: CF plateaus around 45-50%

    CF ≈ clamp(0.087 × windspeed - 0.2, 0, 0.50)
    Annual MWh = Capacity(MW) × 8760 × CF × SystemLoss
    """
    if wind_speed_m_s < 3.0:
        return 0.0

    # Capacity factor from wind speed (simplified power curve)
    cf = min(0.50, max(0.0, 0.087 * wind_speed_m_s - 0.20))

    annual_mwh = capacity_mw * HOURS_PER_YEAR * cf * system_loss_factor

    return max(0.0, annual_mwh)
