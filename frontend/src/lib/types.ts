/**
 * SiteScout TypeScript Types — Milestone 4
 * Typed interfaces for all pipeline response shapes.
 */

// ── Pipeline Response ──────────────────────────────────────────────────

export interface Coordinates {
  latitude: number;
  longitude: number;
}

export interface EnvironmentalData {
  latitude: number;
  longitude: number;
  annual_solar_irradiance_kwh_m2_day: number;
  annual_wind_speed_50m_m_s: number;
  annual_avg_temp_c: number;
  raw_monthly_solar?: Record<string, number>;
  raw_monthly_wind?: Record<string, number>;
}

export interface InfrastructureData {
  nearest_substation_km: number | null;
  nearest_power_line_km: number | null;
  nearest_major_road_km: number | null;
  substations_found_in_radius: number;
  power_lines_found_in_radius: number;
  roads_found_in_radius: number;
}

export interface ConflictData {
  is_unsuitable: boolean;
  hard_flags: string[];
  warnings: string[];
  total_conflicts_found: number;
}

export interface Prediction {
  assumed_capacity_kw: number;
  annual_energy_output_mwh: number;
  capacity_factor_percent: number;
  inference_engine: string;
  suitability: string;
}

export interface HardConstraint {
  constraint: string;
  threshold: string;
  actual_value: number | string | null;
  passed: boolean;
  severity: string;
  detail: string;
}

export interface FeasibilityResult {
  is_feasible: boolean;
  feasibility_score: number;
  recommended_energy_type: string;
  hard_constraints: HardConstraint[];
  hard_constraint_summary: {
    total: number;
    passed: number;
    failed: number;
    failure_reasons: string[];
  };
  soft_scores: {
    infrastructure_proximity_score: number;
    accessibility_score: number;
    overall_soft_score: number;
  };
}

export interface ComponentScore {
  combined_score: number;
  [key: string]: number;
}

export interface SuitabilityResult {
  overall_score: number;
  classification: string;
  weights_used: Record<string, number>;
  component_scores: {
    resource: ComponentScore;
    geographic: ComponentScore;
    infrastructure: ComponentScore;
    environmental: ComponentScore;
    economic: ComponentScore;
  };
}

export interface SolarYield {
  daily_yield_kwh_per_mw: number;
  annual_yield_mwh: number;
  capacity_factor_pct: number;
  performance_ratio_pct: number;
  t_cell_c: number;
  temp_loss_fraction: number;
  shading_loss_pct: number;
}

export interface WindYield {
  daily_yield_kwh: number;
  annual_yield_mwh: number;
  capacity_factor_pct: number;
  wind_power_density_w_m2: number;
  turbulence_intensity_pct: number;
  air_density_kg_m3: number;
  aep_mwh_per_mw: number;
}

export interface EnergyYieldResult {
  energy_type: string;
  annual_energy_yield_mwh: number;
  capacity_factor_pct: number;
  total_capacity_mw: number;
  solar_yield: SolarYield | null;
  wind_yield: WindYield | null;
  solar_fraction?: number;
  wind_fraction?: number;
}

export interface YearlyCashFlow {
  year: number;
  solar_mwh: number;
  wind_mwh: number;
  total_mwh: number;
  revenue_usd: number;
  opex_usd: number;
  net_cash_flow_usd: number;
  cumulative_cash_flow_usd: number;
}

export interface FinancialResult {
  deployment: string;
  technical_feasibility: boolean;
  total_capacity_mw: number;
  solar_capacity_mw: number;
  wind_capacity_mw: number;
  annual_energy_yield_mwh: number;
  annual_revenue_usd: number;
  estimated_project_cost_usd: number;
  annual_opex_usd: number;
  payback_period_years: number | null;
  payback_status: string;
  roi_pct: number;
  npv_usd: number;
  lcoe_usd_per_mwh: number;
  irr_pct: number;
  fit_usd_per_mwh: number;
  discount_rate_pct: number;
  project_lifetime_years: number;
  yearly_cash_flows: YearlyCashFlow[];
}

export interface DeploymentPlan {
  recommended_technology: string;
  recommended_capacity_mw: number;
  expansion_status: string;
  optimization_remarks: string;
}

export interface MicrositingResult {
  total_land_area_sqkm: number;
  total_land_area_ha: number;
  energy_type: string;
  solar: {
    allocated_land_ha: number;
    max_capacity_mw: number;
    panel_count: number;
    footprint_sqm: number;
  } | null;
  wind: {
    allocated_land_ha: number;
    max_capacity_mw: number;
    turbine_count: number;
  } | null;
  total_capacity_mw: number;
  solar_capacity_mw: number;
  wind_capacity_mw: number;
  expansion_status: string;
  expansion_detail: string;
  deployment_plan: DeploymentPlan;
}

export interface Recommendation {
  verdict: string;
  confidence: string;
  summary: string;
  recommended_technology: string;
  recommended_capacity_mw: number;
  expansion_potential: string;
  suitability_score: number;
  suitability_class: string;
  is_feasible: boolean;
}

export interface AINarrative {
  narrative: string | null;
  available: boolean;
  model?: string;
  error?: string | null;
}

export interface FullAnalysisResponse {
  status: string;
  coordinates: Coordinates;
  environmental_data: EnvironmentalData;
  infrastructure_data: InfrastructureData;
  land_use_conflicts: ConflictData;
  predictions: {
    solar: Prediction;
    wind: Prediction;
  };
  feasibility: FeasibilityResult;
  suitability: SuitabilityResult;
  micrositing: MicrositingResult;
  energy_yield: EnergyYieldResult;
  financial: FinancialResult;
  recommendation: Recommendation;
  ai_narrative: AINarrative | null;
}

// ── Yield Calculator ───────────────────────────────────────────────────

export interface YieldCalculatorResponse {
  energy_yield: EnergyYieldResult;
  financial: FinancialResult;
  micrositing: MicrositingResult;
}
