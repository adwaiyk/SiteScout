from __future__ import annotations
from typing import List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ForecastRequest(BaseModel):
    site_id: UUID = Field(description='UUID of the site to forecast')
    capacity_mw: float = Field(default=1.0, gt=0.0, le=500.0, description='Installed capacity in MW')
    system_loss_pct: float = Field(default=14.0, ge=0.0, le=50.0, description='Total system losses as a percentage (soiling, wiring, inverter, transformer, curtailment). Industry standard ~14% for solar PV.')

class MonthlyForecast(BaseModel):
    month_index: int = Field(ge=1, le=12, description='1 = January, 12 = December')
    month_name: str = Field(description="Full month name (e.g., 'January')")
    p10_mwh: float = Field(description='P10 (conservative) generation in MWh')
    p50_mwh: float = Field(description='P50 (expected) generation in MWh')
    p90_mwh: float = Field(description='P90 (optimistic) generation in MWh')

class AnnualForecast(BaseModel):
    year: int = Field(ge=1, le=30, description='Project year (1 = first year)')
    degradation_factor: float = Field(description='Cumulative degradation multiplier (e.g., 0.995 for year 2 solar)')
    p10_mwh: float = Field(description='P10 annual generation after degradation (MWh)')
    p50_mwh: float = Field(description='P50 annual generation after degradation (MWh)')
    p90_mwh: float = Field(description='P90 annual generation after degradation (MWh)')

class CumulativeProduction(BaseModel):
    lifespan_years: int = Field(description='Project lifespan in years')
    p10_total_mwh: float = Field(description='P10 cumulative production (MWh)')
    p50_total_mwh: float = Field(description='P50 cumulative production (MWh)')
    p90_total_mwh: float = Field(description='P90 cumulative production (MWh)')

class ForecastResponse(BaseModel):
    project_id: UUID
    site_id: UUID
    site_name: str
    capacity_mw: float
    system_loss_pct: float
    energy_type: str = Field(description="Primary energy type: 'solar', 'wind', or 'hybrid'")
    monthly_forecasts: List[MonthlyForecast] = Field(description='12-month seasonality array with P10/P50/P90 bands')
    annual_forecasts: List[AnnualForecast] = Field(description='25-year lifespan projections with degradation applied')
    cumulative: CumulativeProduction = Field(description='Total cumulative production over the project lifespan')
    first_year_p50_mwh: float = Field(description='Year-1 expected (P50) generation in MWh for quick reference')
    capacity_factor_pct: float = Field(description='Effective P50 capacity factor including system losses (%)')

class GridCapacityRequest(BaseModel):
    site_id: UUID = Field(description='UUID of the site to assess')

class GridCapacityResponse(BaseModel):
    project_id: UUID
    site_id: UUID
    site_name: str
    substation_distance_km: Optional[float] = Field(default=None, description='Distance to nearest substation in km')
    estimated_voltage_kv: float = Field(description='Estimated substation voltage class in kV (heuristic: <10 km → 33 kV, <25 km → 66 kV, else 132 kV)')
    line_distance_km: Optional[float] = Field(default=None, description='Distance to nearest power line in km')
    estimated_line_rating_a: float = Field(description='Estimated current-carrying capacity of the line in Amperes')
    existing_generation_nearby_mw: float = Field(description='Estimated existing generation capacity nearby in MW (proxy from power infrastructure density)')
    thermal_limit_mw: float = Field(description='Maximum thermal transmission capacity in MW: √3 × Voltage(kV) × Line Rating(A) × Power Factor / 1000')
    estimated_spare_capacity_mw: float = Field(description='Estimated remaining hosting capacity in MW')
    hosting_status: Literal['Constrained', 'Moderate', 'High Capacity'] = Field(description='Hosting capacity classification: Constrained (<10 MW), Moderate (10–50 MW), High Capacity (>50 MW)')
    max_recommended_interconnect_mw: float = Field(description='Maximum recommended new interconnection size in MW (conservative: min(spare×0.8, thermal×0.5))')
    assessment_notes: str = Field(description='Human-readable summary of the grid capacity assessment')
