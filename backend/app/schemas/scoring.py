from __future__ import annotations
from typing import Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator

class SiteScoringWeights(BaseModel):
    renewable_resource: float = Field(default=0.3, ge=0.0, le=1.0, description='Weight for Renewable Resource Availability (solar/wind potential)')
    geographic_suitability: float = Field(default=0.2, ge=0.0, le=1.0, description='Weight for Geographic Suitability (terrain, slope, elevation)')
    infrastructure_accessibility: float = Field(default=0.15, ge=0.0, le=1.0, description='Weight for Infrastructure Accessibility (grid, roads)')
    environmental_impact: float = Field(default=0.15, ge=0.0, le=1.0, description='Weight for Environmental Impact (conflicts, protected areas)')
    socio_economic_viability: float = Field(default=0.15, ge=0.0, le=1.0, description='Weight for Socio-Economic Viability (demand, land cost, acceptance)')
    economic_feasibility: float = Field(default=0.05, ge=0.0, le=1.0, description='Weight for Economic/Cost Feasibility')

    @model_validator(mode='after')
    def validate_weights_sum_to_one(self) -> 'SiteScoringWeights':
        total = self.renewable_resource + self.geographic_suitability + self.infrastructure_accessibility + self.environmental_impact + self.socio_economic_viability + self.economic_feasibility
        if abs(total - 1.0) > 0.01:
            raise ValueError(f'Weights must sum to 1.0 (got {total:.4f}). Adjust your weights so they add up correctly.')
        return self

class SiteFeatureVector(BaseModel):
    site_id: UUID
    site_name: str
    solar_irradiance_kwh_m2_day: float = Field(default=0.0, description='Annual avg solar irradiance (kWh/m²/day)')
    wind_speed_50m_m_s: float = Field(default=0.0, description='Annual avg wind speed at 50 m (m/s)')
    solar_capacity_factor_pct: float = Field(default=0.0, description='Solar capacity factor (%)')
    wind_capacity_factor_pct: float = Field(default=0.0, description='Wind capacity factor (%)')
    elevation_m: float = Field(default=0.0, description='Elevation in meters')
    land_area_sqkm: float = Field(default=0.0, description='Available land area (km²)')
    nearest_substation_km: float = Field(default=50.0, description='Distance to nearest substation (km)')
    nearest_power_line_km: float = Field(default=50.0, description='Distance to nearest power line (km)')
    nearest_road_km: float = Field(default=50.0, description='Distance to nearest major road (km)')
    conflict_count: int = Field(default=0, description='Number of land-use conflicts detected')
    is_unsuitable: bool = Field(default=False, description='Whether hard-flag conflicts exist')
    infrastructure_count: int = Field(default=0, description='Count of nearby infrastructure features')
    estimated_annual_mwh: float = Field(default=0.0, description='Combined estimated annual energy output (MWh)')
    avg_temp_c: float = Field(default=25.0, description='Annual average temperature (°C)')

class FactorBreakdown(BaseModel):
    factor_name: str
    raw_value: float
    normalized_value: float = Field(description='Normalized to 0–1 range')
    weight: float
    weighted_contribution: float = Field(description='normalized_value × weight')

class ScoredSiteResponse(BaseModel):
    site_id: UUID
    site_name: str
    total_score: float = Field(description='Weighted sum score (0–1)')
    classification: str = Field(description='Excellent | Highly Suitable | Moderately Suitable | Low Suitability | Unsuitable')
    factor_breakdown: List[FactorBreakdown]

class ScoreSitesResponse(BaseModel):
    project_id: UUID
    weights_used: SiteScoringWeights
    total_sites_scored: int
    scored_sites: List[ScoredSiteResponse]

class OptimizationRequest(BaseModel):
    population_size: int = Field(default=100, ge=20, le=500, description='NSGA-II population size (higher = more thorough, slower)')
    n_generations: int = Field(default=200, ge=50, le=1000, description='Number of NSGA-II generations to evolve')

class ParetoSolution(BaseModel):
    site_id: UUID
    site_name: str
    energy_output_mwh: float = Field(description='Annual energy output (MWh) — maximized')
    environmental_impact_score: float = Field(description='Environmental impact score (0–1) — minimized')
    infrastructure_cost_proxy: float = Field(description='Infrastructure distance proxy (km) — minimized')
    is_dominated: bool = Field(default=False, description='Whether this solution is dominated by another')

class ParetoFrontierResponse(BaseModel):
    project_id: UUID
    algorithm: str = 'NSGA-II'
    population_size: int
    generations_evolved: int
    total_sites_evaluated: int
    pareto_front_size: int
    pareto_solutions: List[ParetoSolution]
    dominated_solutions: List[ParetoSolution]

class ExplainSiteRequest(BaseModel):
    site_id: UUID

class SHAPFeatureContribution(BaseModel):
    feature_name: str
    feature_value: float = Field(description='The raw feature value for this site')
    shap_value: float = Field(description='SHAP contribution (positive = pushes score UP, negative = pushes DOWN)')
    abs_importance: float = Field(description='|shap_value| for ranking importance')

class SHAPExplanationResponse(BaseModel):
    project_id: UUID
    site_id: UUID
    site_name: str
    model_type: str = Field(description='The ML model used (e.g., XGBoost, LightGBM)')
    base_value: float = Field(description='Expected prediction when no features are known (model baseline)')
    predicted_value: float = Field(description="The model's actual prediction for this site")
    feature_contributions: List[SHAPFeatureContribution]
    top_positive_drivers: List[str] = Field(description='Features that most increased the score')
    top_negative_drivers: List[str] = Field(description='Features that most decreased the score')
