from __future__ import annotations
import logging
from typing import Any, Dict, List
from app.schemas.forecasting import AnnualForecast, CumulativeProduction, MonthlyForecast
logger = logging.getLogger(__name__)
MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
SOLAR_SEASONALITY = [0.88, 0.95, 1.08, 1.15, 1.12, 0.92, 0.78, 0.8, 0.9, 1.02, 1.0, 0.9]
WIND_SEASONALITY = [0.7, 0.72, 0.8, 0.85, 0.95, 1.25, 1.35, 1.3, 1.15, 0.9, 0.75, 0.68]
P10_MULTIPLIER_SOLAR = 0.85
P90_MULTIPLIER_SOLAR = 1.12
P10_MULTIPLIER_WIND = 0.8
P90_MULTIPLIER_WIND = 1.15
SOLAR_DEGRADATION_RATE = 0.005
WIND_DEGRADATION_RATE = 0.002
DEFAULT_LIFESPAN_YEARS = 25
DAYS_PER_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
HOURS_PER_YEAR = 8760

def compute_energy_forecast(site_name: str, capacity_mw: float, system_loss_pct: float, solar_irradiance_kwh_m2_day: float, wind_speed_50m_m_s: float, solar_capacity_factor_pct: float, wind_capacity_factor_pct: float, avg_temp_c: float, lifespan_years: int=DEFAULT_LIFESPAN_YEARS) -> Dict[str, Any]:
    system_loss_factor = 1.0 - system_loss_pct / 100.0
    solar_mwh_annual = _compute_solar_annual_mwh(capacity_mw, solar_irradiance_kwh_m2_day, avg_temp_c, system_loss_factor)
    wind_mwh_annual = _compute_wind_annual_mwh(capacity_mw, wind_speed_50m_m_s, system_loss_factor)
    if solar_mwh_annual > 0 and wind_mwh_annual > 0:
        energy_type = 'hybrid'
    elif solar_mwh_annual > 0:
        energy_type = 'solar'
    else:
        energy_type = 'wind'
    total_p50_annual = solar_mwh_annual + wind_mwh_annual
    if total_p50_annual > 0:
        solar_fraction = solar_mwh_annual / total_p50_annual
        wind_fraction = wind_mwh_annual / total_p50_annual
    else:
        solar_fraction = 0.5
        wind_fraction = 0.5
    p10_mult = solar_fraction * P10_MULTIPLIER_SOLAR + wind_fraction * P10_MULTIPLIER_WIND
    p90_mult = solar_fraction * P90_MULTIPLIER_SOLAR + wind_fraction * P90_MULTIPLIER_WIND
    degradation_rate = solar_fraction * SOLAR_DEGRADATION_RATE + wind_fraction * WIND_DEGRADATION_RATE
    blended_seasonality = [solar_fraction * SOLAR_SEASONALITY[m] + wind_fraction * WIND_SEASONALITY[m] for m in range(12)]
    monthly_forecasts: List[MonthlyForecast] = []
    for m in range(12):
        days = DAYS_PER_MONTH[m]
        month_fraction = days / 365.0
        month_p50 = total_p50_annual * month_fraction * blended_seasonality[m]
        month_p10 = month_p50 * p10_mult
        month_p90 = month_p50 * p90_mult
        monthly_forecasts.append(MonthlyForecast(month_index=m + 1, month_name=MONTH_NAMES[m], p10_mwh=round(month_p10, 2), p50_mwh=round(month_p50, 2), p90_mwh=round(month_p90, 2)))
    annual_forecasts: List[AnnualForecast] = []
    cumulative_p10 = 0.0
    cumulative_p50 = 0.0
    cumulative_p90 = 0.0
    for year in range(1, lifespan_years + 1):
        deg_factor = (1.0 - degradation_rate) ** (year - 1)
        year_p50 = total_p50_annual * deg_factor
        year_p10 = year_p50 * p10_mult
        year_p90 = year_p50 * p90_mult
        cumulative_p10 += year_p10
        cumulative_p50 += year_p50
        cumulative_p90 += year_p90
        annual_forecasts.append(AnnualForecast(year=year, degradation_factor=round(deg_factor, 6), p10_mwh=round(year_p10, 2), p50_mwh=round(year_p50, 2), p90_mwh=round(year_p90, 2)))
    max_possible_mwh = capacity_mw * HOURS_PER_YEAR
    effective_cf = total_p50_annual / max_possible_mwh * 100.0 if max_possible_mwh > 0 else 0.0
    cumulative = CumulativeProduction(lifespan_years=lifespan_years, p10_total_mwh=round(cumulative_p10, 2), p50_total_mwh=round(cumulative_p50, 2), p90_total_mwh=round(cumulative_p90, 2))
    return {'energy_type': energy_type, 'monthly_forecasts': monthly_forecasts, 'annual_forecasts': annual_forecasts, 'cumulative': cumulative, 'first_year_p50_mwh': round(total_p50_annual, 2), 'capacity_factor_pct': round(effective_cf, 2)}

def _compute_solar_annual_mwh(capacity_mw: float, irradiance_kwh_m2_day: float, avg_temp_c: float, system_loss_factor: float) -> float:
    if irradiance_kwh_m2_day <= 0:
        return 0.0
    capacity_kw = capacity_mw * 1000.0
    base_pr = 0.8
    temp_coefficient = -0.004
    temp_derate = max(0.0, (avg_temp_c - 25.0) * temp_coefficient)
    effective_pr = max(0.5, base_pr + temp_derate)
    annual_mwh = capacity_kw * irradiance_kwh_m2_day * 365.0 * effective_pr * system_loss_factor / 1000.0
    return max(0.0, annual_mwh)

def _compute_wind_annual_mwh(capacity_mw: float, wind_speed_m_s: float, system_loss_factor: float) -> float:
    if wind_speed_m_s < 3.0:
        return 0.0
    cf = min(0.5, max(0.0, 0.087 * wind_speed_m_s - 0.2))
    annual_mwh = capacity_mw * HOURS_PER_YEAR * cf * system_loss_factor
    return max(0.0, annual_mwh)
