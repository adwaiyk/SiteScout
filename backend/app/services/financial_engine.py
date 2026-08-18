"""
Financial Analysis Engine — SiteScout Milestone 4
CAPEX/OPEX, 25-year degradation, NPV, LCOE, IRR, payback — fully independent of ML.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Cost Constants ──────────────────────────────────────────────────────
SOLAR_CAPEX_PER_MW = 1_100_000   # USD
WIND_CAPEX_PER_MW = 1_400_000    # USD
SOLAR_OPEX_PER_MW = 15_000       # USD/year
WIND_OPEX_PER_MW = 32_000        # USD/year

SOLAR_DEGRADATION_RATE = 0.005   # 0.5%/yr
WIND_DEGRADATION_RATE = 0.008    # 0.8%/yr
DISCOUNT_RATE = 0.075            # 7.5%
DEFAULT_FIT_USD_MWH = 65.0       # $/MWh
PROJECT_LIFETIME_YEARS = 25


def compute_financial_analysis(
    *,
    solar_capacity_mw: float = 0.0,
    wind_capacity_mw: float = 0.0,
    base_solar_mwh: float = 0.0,
    base_wind_mwh: float = 0.0,
    fit_usd_per_mwh: float = DEFAULT_FIT_USD_MWH,
    discount_rate: float = DISCOUNT_RATE,
    lifetime_years: int = PROJECT_LIFETIME_YEARS,
) -> Dict[str, Any]:
    """
    Full 25-year financial model.

    CAPEX = (Solar_MW * 1,100,000) + (Wind_MW * 1,400,000)
    OPEX  = (Solar_MW * 15,000) + (Wind_MW * 32,000)

    Solar_MWh(t) = Base_Solar * (0.995)^(t-1)
    Wind_MWh(t)  = Base_Wind  * (0.992)^(t-1)
    Revenue(t) = (Solar_MWh(t) + Wind_MWh(t)) * FiT
    Net_CF(t) = Revenue(t) - OPEX
    NPV = -CAPEX + sum(Net_CF(t) / (1+r)^t)
    LCOE = [CAPEX + sum(OPEX/(1+r)^t)] / sum(Total_MWh(t)/(1+r)^t)
    """
    total_capex = solar_capacity_mw * SOLAR_CAPEX_PER_MW + wind_capacity_mw * WIND_CAPEX_PER_MW
    annual_opex = solar_capacity_mw * SOLAR_OPEX_PER_MW + wind_capacity_mw * WIND_OPEX_PER_MW
    total_capacity_mw = solar_capacity_mw + wind_capacity_mw

    # Determine deployment type
    if solar_capacity_mw > 0 and wind_capacity_mw > 0:
        deployment = "Hybrid"
    elif solar_capacity_mw > 0:
        deployment = "Solar"
    elif wind_capacity_mw > 0:
        deployment = "Wind"
    else:
        deployment = "None"

    # Edge case: no capacity
    if total_capacity_mw <= 0 or (base_solar_mwh <= 0 and base_wind_mwh <= 0):
        return _zero_result(deployment, total_capex)

    # ── Year-by-year cash flow model ────────────────────────────────────
    yearly_data: List[Dict[str, Any]] = []
    cumulative_cash_flow = -total_capex
    npv_net_cf_sum = 0.0
    npv_opex_sum = 0.0
    npv_mwh_sum = 0.0
    payback_year: Optional[int] = None
    prev_cumulative = cumulative_cash_flow

    for t in range(1, lifetime_years + 1):
        solar_mwh_t = base_solar_mwh * (1.0 - SOLAR_DEGRADATION_RATE) ** (t - 1)
        wind_mwh_t = base_wind_mwh * (1.0 - WIND_DEGRADATION_RATE) ** (t - 1)
        total_mwh_t = solar_mwh_t + wind_mwh_t

        revenue_t = total_mwh_t * fit_usd_per_mwh
        net_cf_t = revenue_t - annual_opex
        cumulative_cash_flow += net_cf_t

        discount_factor = (1.0 + discount_rate) ** t
        npv_net_cf_sum += net_cf_t / discount_factor
        npv_opex_sum += annual_opex / discount_factor
        npv_mwh_sum += total_mwh_t / discount_factor

        # Payback detection
        if payback_year is None and cumulative_cash_flow >= 0 and prev_cumulative < 0:
            # Interpolate for fractional payback year
            if net_cf_t > 0:
                fraction = abs(prev_cumulative) / net_cf_t
                payback_year = t - 1
                payback_fraction = fraction
            else:
                payback_year = t
                payback_fraction = 0.0

        prev_cumulative = cumulative_cash_flow

        yearly_data.append({
            "year": t,
            "solar_mwh": round(solar_mwh_t, 2),
            "wind_mwh": round(wind_mwh_t, 2),
            "total_mwh": round(total_mwh_t, 2),
            "revenue_usd": round(revenue_t, 2),
            "opex_usd": round(annual_opex, 2),
            "net_cash_flow_usd": round(net_cf_t, 2),
            "cumulative_cash_flow_usd": round(cumulative_cash_flow, 2),
        })

    # ── Summary Metrics ─────────────────────────────────────────────────
    npv = -total_capex + npv_net_cf_sum

    # LCOE = [CAPEX + sum(OPEX/(1+r)^t)] / sum(MWh/(1+r)^t)
    lcoe = (total_capex + npv_opex_sum) / npv_mwh_sum if npv_mwh_sum > 0 else 0.0

    # Payback period
    if payback_year is not None:
        payback_period = payback_year + payback_fraction
    elif cumulative_cash_flow >= 0:
        payback_period = float(lifetime_years)
    else:
        payback_period = None  # Not recoverable

    # IRR approximation: ((Net_CF[1] + Net_CF[25]) / 2 / CAPEX) * 100 + 2.5
    if total_capex > 0 and len(yearly_data) >= 2:
        net_cf_1 = yearly_data[0]["net_cash_flow_usd"]
        net_cf_last = yearly_data[-1]["net_cash_flow_usd"]
        irr_pct = ((net_cf_1 + net_cf_last) / 2.0 / total_capex) * 100.0 + 2.5
        irr_pct = max(0.0, irr_pct)
    else:
        irr_pct = 0.0

    # Year-1 metrics
    year1 = yearly_data[0] if yearly_data else {}
    annual_energy_yield_mwh = year1.get("total_mwh", 0.0)
    annual_revenue = year1.get("revenue_usd", 0.0)

    # ROI
    roi_pct = (npv / total_capex * 100.0) if total_capex > 0 else 0.0

    result = {
        "deployment": deployment,
        "technical_feasibility": True,  # Set by pipeline, not financial engine
        "total_capacity_mw": round(total_capacity_mw, 2),
        "solar_capacity_mw": round(solar_capacity_mw, 2),
        "wind_capacity_mw": round(wind_capacity_mw, 2),
        "annual_energy_yield_mwh": round(annual_energy_yield_mwh, 2),
        "annual_revenue_usd": round(annual_revenue, 2),
        "estimated_project_cost_usd": round(total_capex, 2),
        "annual_opex_usd": round(annual_opex, 2),
        "payback_period_years": round(payback_period, 2) if payback_period is not None else None,
        "payback_status": "Recoverable" if payback_period is not None else "Not recoverable within project horizon",
        "roi_pct": round(roi_pct, 2),
        "npv_usd": round(npv, 2),
        "lcoe_usd_per_mwh": round(lcoe, 2),
        "irr_pct": round(irr_pct, 2),
        "fit_usd_per_mwh": fit_usd_per_mwh,
        "discount_rate_pct": round(discount_rate * 100, 2),
        "project_lifetime_years": lifetime_years,
        "yearly_cash_flows": yearly_data,
    }

    logger.info(
        "Financial analysis: %s | CAPEX=$%s | NPV=$%s | LCOE=$%.2f/MWh | Payback=%.1f yrs | IRR=%.1f%%",
        deployment,
        f"{total_capex:,.0f}",
        f"{npv:,.0f}",
        lcoe,
        payback_period if payback_period is not None else -1,
        irr_pct,
    )

    return result


def _zero_result(deployment: str, total_capex: float) -> Dict[str, Any]:
    """Return a zeroed-out result for edge cases."""
    return {
        "deployment": deployment,
        "technical_feasibility": False,
        "total_capacity_mw": 0.0,
        "solar_capacity_mw": 0.0,
        "wind_capacity_mw": 0.0,
        "annual_energy_yield_mwh": 0.0,
        "annual_revenue_usd": 0.0,
        "estimated_project_cost_usd": round(total_capex, 2),
        "annual_opex_usd": 0.0,
        "payback_period_years": None,
        "payback_status": "Not recoverable — zero energy yield",
        "roi_pct": 0.0,
        "npv_usd": round(-total_capex, 2),
        "lcoe_usd_per_mwh": 0.0,
        "irr_pct": 0.0,
        "fit_usd_per_mwh": DEFAULT_FIT_USD_MWH,
        "discount_rate_pct": round(DISCOUNT_RATE * 100, 2),
        "project_lifetime_years": PROJECT_LIFETIME_YEARS,
        "yearly_cash_flows": [],
    }
