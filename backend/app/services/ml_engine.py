from __future__ import annotations
import logging
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from app.config import get_settings
from app.schemas.scoring import FactorBreakdown, ParetoSolution, ScoredSiteResponse, SHAPFeatureContribution, SiteFeatureVector, SiteScoringWeights
logger = logging.getLogger(__name__)
_settings = get_settings()

def _normalize_min_max(values: np.ndarray, invert: bool=False) -> np.ndarray:
    v_min, v_max = (values.min(), values.max())
    if v_max - v_min < 1e-09:
        return np.full_like(values, 0.5, dtype=np.float64)
    normalized = (values - v_min) / (v_max - v_min)
    if invert:
        normalized = 1.0 - normalized
    return normalized

def _classify_score(score: float) -> str:
    if score >= 0.85:
        return 'Excellent'
    elif score >= 0.7:
        return 'Highly Suitable'
    elif score >= 0.5:
        return 'Moderately Suitable'
    elif score >= 0.3:
        return 'Low Suitability'
    else:
        return 'Unsuitable'

def compute_weighted_scores(sites: List[SiteFeatureVector], weights: SiteScoringWeights) -> List[ScoredSiteResponse]:
    n = len(sites)
    if n == 0:
        return []
    renewable_raw = np.array([(s.solar_capacity_factor_pct + s.wind_capacity_factor_pct) / 2.0 + s.solar_irradiance_kwh_m2_day * 5.0 + s.wind_speed_50m_m_s * 3.0 for s in sites])
    geographic_raw = np.array([s.land_area_sqkm * 10.0 + max(0, 100.0 - abs(s.elevation_m - 500.0) * 0.1) for s in sites])
    infra_raw = np.array([s.nearest_substation_km + s.nearest_power_line_km + s.nearest_road_km for s in sites])
    env_raw = np.array([s.conflict_count * 25.0 + (100.0 if s.is_unsuitable else 0.0) for s in sites])
    socio_raw = np.array([s.infrastructure_count * 5.0 for s in sites])
    econ_raw = np.array([s.estimated_annual_mwh * 0.1 + max(0, 50.0 - abs(s.avg_temp_c - 25.0) * 2.0) for s in sites])
    renewable_norm = _normalize_min_max(renewable_raw, invert=False)
    geographic_norm = _normalize_min_max(geographic_raw, invert=False)
    infra_norm = _normalize_min_max(infra_raw, invert=True)
    env_norm = _normalize_min_max(env_raw, invert=True)
    socio_norm = _normalize_min_max(socio_raw, invert=False)
    econ_norm = _normalize_min_max(econ_raw, invert=False)
    weight_vec = np.array([weights.renewable_resource, weights.geographic_suitability, weights.infrastructure_accessibility, weights.environmental_impact, weights.socio_economic_viability, weights.economic_feasibility])
    factor_names = ['Renewable Resource Availability', 'Geographic Suitability', 'Infrastructure Accessibility', 'Environmental Impact', 'Socio-Economic Viability', 'Economic Feasibility']
    results: List[ScoredSiteResponse] = []
    for i, site in enumerate(sites):
        norm_values = np.array([renewable_norm[i], geographic_norm[i], infra_norm[i], env_norm[i], socio_norm[i], econ_norm[i]])
        raw_values = np.array([renewable_raw[i], geographic_raw[i], infra_raw[i], env_raw[i], socio_raw[i], econ_raw[i]])
        weighted_contributions = norm_values * weight_vec
        total_score = float(weighted_contributions.sum())
        breakdown = [FactorBreakdown(factor_name=factor_names[j], raw_value=round(float(raw_values[j]), 4), normalized_value=round(float(norm_values[j]), 4), weight=round(float(weight_vec[j]), 4), weighted_contribution=round(float(weighted_contributions[j]), 4)) for j in range(6)]
        results.append(ScoredSiteResponse(site_id=site.site_id, site_name=site.site_name, total_score=round(total_score, 4), classification=_classify_score(total_score), factor_breakdown=breakdown))
    results.sort(key=lambda r: r.total_score, reverse=True)
    return results

def run_pareto_optimization(sites: List[SiteFeatureVector], population_size: int=100, n_generations: int=200) -> Tuple[List[ParetoSolution], List[ParetoSolution]]:
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.core.problem import ElementwiseProblem
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.mutation.pm import PM
    from pymoo.operators.sampling.rnd import IntegerRandomSampling
    from pymoo.operators.repair.rounding import RoundingRepair
    from pymoo.optimize import minimize
    from pymoo.termination import get_termination
    n_sites = len(sites)
    if n_sites < 2:
        if n_sites == 1:
            s = sites[0]
            sol = ParetoSolution(site_id=s.site_id, site_name=s.site_name, energy_output_mwh=s.estimated_annual_mwh, environmental_impact_score=min(1.0, s.conflict_count * 0.25 + (0.5 if s.is_unsuitable else 0.0)), infrastructure_cost_proxy=(s.nearest_substation_km + s.nearest_power_line_km + s.nearest_road_km) / 3.0, is_dominated=False)
            return ([sol], [])
        return ([], [])
    energy_outputs = np.array([s.estimated_annual_mwh for s in sites])
    env_impacts = np.array([min(1.0, s.conflict_count * 0.25 + (0.5 if s.is_unsuitable else 0.0)) for s in sites])
    infra_costs = np.array([(s.nearest_substation_km + s.nearest_power_line_km + s.nearest_road_km) / 3.0 for s in sites])

    class SiteOptimizationProblem(ElementwiseProblem):

        def __init__(self) -> None:
            super().__init__(n_var=1, n_obj=3, n_ieq_constr=0, xl=np.array([0]), xu=np.array([n_sites - 1]), vtype=int)

        def _evaluate(self, x: np.ndarray, out: Dict[str, Any], *args: Any, **kwargs: Any) -> None:
            idx = int(x[0])
            idx = max(0, min(idx, n_sites - 1))
            out['F'] = np.array([-energy_outputs[idx], env_impacts[idx], infra_costs[idx]])
    problem = SiteOptimizationProblem()
    algorithm = NSGA2(pop_size=min(population_size, n_sites * 10), sampling=IntegerRandomSampling(), crossover=SBX(prob=0.9, eta=15, repair=RoundingRepair()), mutation=PM(prob=1.0 / 1, eta=20, repair=RoundingRepair()), eliminate_duplicates=True)
    termination = get_termination('n_gen', n_generations)
    logger.info('Running NSGA-II: pop_size=%d, generations=%d, sites=%d', population_size, n_generations, n_sites)
    result = minimize(problem, algorithm, termination, seed=42, verbose=False)
    pareto_indices: set[int] = set()
    pareto_solutions: List[ParetoSolution] = []
    if result.F is not None and result.X is not None and (len(result.F) > 0):
        for i in range(len(result.X)):
            idx = int(result.X[i][0])
            idx = max(0, min(idx, n_sites - 1))
            if idx not in pareto_indices:
                pareto_indices.add(idx)
                s = sites[idx]
                pareto_solutions.append(ParetoSolution(site_id=s.site_id, site_name=s.site_name, energy_output_mwh=round(float(-result.F[i][0]), 2), environmental_impact_score=round(float(result.F[i][1]), 4), infrastructure_cost_proxy=round(float(result.F[i][2]), 2), is_dominated=False))
    dominated_solutions: List[ParetoSolution] = []
    for i, s in enumerate(sites):
        if i not in pareto_indices:
            dominated_solutions.append(ParetoSolution(site_id=s.site_id, site_name=s.site_name, energy_output_mwh=round(float(energy_outputs[i]), 2), environmental_impact_score=round(float(env_impacts[i]), 4), infrastructure_cost_proxy=round(float(infra_costs[i]), 2), is_dominated=True))
    logger.info('NSGA-II complete: %d Pareto-optimal, %d dominated', len(pareto_solutions), len(dominated_solutions))
    return (pareto_solutions, dominated_solutions)
SHAP_FEATURE_COLUMNS = ['solar_irradiance_kwh_m2_day', 'wind_speed_50m_m_s', 'solar_capacity_factor_pct', 'wind_capacity_factor_pct', 'elevation_m', 'land_area_sqkm', 'nearest_substation_km', 'nearest_power_line_km', 'nearest_road_km', 'conflict_count', 'infrastructure_count', 'avg_temp_c']
SHAP_FEATURE_DISPLAY_NAMES = {'solar_irradiance_kwh_m2_day': 'Solar Irradiance (kWh/m²/day)', 'wind_speed_50m_m_s': 'Wind Speed at 50m (m/s)', 'solar_capacity_factor_pct': 'Solar Capacity Factor (%)', 'wind_capacity_factor_pct': 'Wind Capacity Factor (%)', 'elevation_m': 'Elevation (m)', 'land_area_sqkm': 'Land Area (km²)', 'nearest_substation_km': 'Distance to Substation (km)', 'nearest_power_line_km': 'Distance to Power Line (km)', 'nearest_road_km': 'Distance to Major Road (km)', 'conflict_count': 'Land-Use Conflicts', 'infrastructure_count': 'Nearby Infrastructure Count', 'avg_temp_c': 'Average Temperature (°C)'}

class SHAPExplainer:

    def __init__(self) -> None:
        self._model = None
        self._model_type = 'Unknown'
        self._explainer = None
        self._load_or_create_model()

    def _load_or_create_model(self) -> None:
        logger.info('SHAP: Training fresh LightGBM suitability model on synthetic data...')
        self._train_synthetic_model()

    def _train_synthetic_model(self) -> None:
        from lightgbm import LGBMRegressor
        np.random.seed(42)
        n_samples = 2000
        data = pd.DataFrame({'solar_irradiance_kwh_m2_day': np.random.uniform(2.0, 7.5, n_samples), 'wind_speed_50m_m_s': np.random.uniform(1.0, 15.0, n_samples), 'solar_capacity_factor_pct': np.random.uniform(8.0, 28.0, n_samples), 'wind_capacity_factor_pct': np.random.uniform(0.0, 50.0, n_samples), 'elevation_m': np.random.uniform(0, 3000, n_samples), 'land_area_sqkm': np.random.uniform(0.1, 50.0, n_samples), 'nearest_substation_km': np.random.uniform(0.5, 50.0, n_samples), 'nearest_power_line_km': np.random.uniform(0.5, 50.0, n_samples), 'nearest_road_km': np.random.uniform(0.1, 30.0, n_samples), 'conflict_count': np.random.randint(0, 8, n_samples), 'infrastructure_count': np.random.randint(0, 30, n_samples), 'avg_temp_c': np.random.uniform(5.0, 45.0, n_samples)})
        target = 0.3 * (data['solar_irradiance_kwh_m2_day'] / 7.5 * 0.4 + data['wind_speed_50m_m_s'] / 15.0 * 0.3 + data['solar_capacity_factor_pct'] / 28.0 * 0.15 + data['wind_capacity_factor_pct'] / 50.0 * 0.15) + 0.2 * (data['land_area_sqkm'] / 50.0 * 0.6 + np.clip(1.0 - np.abs(data['elevation_m'] - 500) / 3000, 0, 1) * 0.4) + 0.15 * np.clip(1.0 - (data['nearest_substation_km'] + data['nearest_power_line_km'] + data['nearest_road_km']) / 130.0, 0, 1) + 0.15 * np.clip(1.0 - data['conflict_count'] / 8.0, 0, 1) + 0.15 * np.clip(data['infrastructure_count'] / 30.0, 0, 1) + 0.05 * np.clip(1.0 - np.abs(data['avg_temp_c'] - 25.0) / 20.0, 0, 1)
        target += np.random.normal(0, 0.02, n_samples)
        target = np.clip(target, 0, 1)
        X = data[SHAP_FEATURE_COLUMNS]
        y = target
        model = LGBMRegressor(n_estimators=200, learning_rate=0.05, max_depth=6, num_leaves=31, random_state=42, verbose=-1)
        model.fit(pd.DataFrame(X), y)
        self._synthetic_background = X
        self._model = model
        self._model_type = 'LightGBM (Synthetic Suitability Model)'
        logger.info('SHAP: LightGBM synthetic model trained successfully.')

    def explain_site(self, target_site: SiteFeatureVector, all_sites: List[SiteFeatureVector]) -> Dict[str, Any]:
        import shap
        target_df = self._feature_vector_to_df(target_site)
        if len(all_sites) <= 3 and hasattr(self, '_synthetic_background'):
            logger.info('SHAP: Not enough project sites (%d), using synthetic background.', len(all_sites))
            background_df = self._synthetic_background
        else:
            background_df = pd.concat([self._feature_vector_to_df(s) for s in all_sites], ignore_index=True)
        assert self._model is not None, 'Model was not initialized'
        if self._explainer is None or True:
            self._explainer = shap.TreeExplainer(self._model, data=pd.DataFrame(background_df), feature_perturbation='interventional')
        assert self._explainer is not None, 'Explainer was not initialized'
        shap_values = self._explainer.shap_values(target_df)
        if isinstance(shap_values, np.ndarray):
            if shap_values.ndim == 2:
                shap_array = shap_values[0]
            else:
                shap_array = shap_values
        else:
            shap_array = np.array(shap_values).flatten()
        base_value = float(self._explainer.expected_value)
        predictions = np.array(self._model.predict(target_df))
        predicted_value = float(predictions[0])
        contributions: List[SHAPFeatureContribution] = []
        for j, col in enumerate(SHAP_FEATURE_COLUMNS):
            sv = float(shap_array[j])
            contributions.append(SHAPFeatureContribution(feature_name=SHAP_FEATURE_DISPLAY_NAMES.get(col, col), feature_value=round(float(target_df[col].iloc[0]), 4), shap_value=round(sv, 6), abs_importance=round(abs(sv), 6)))
        contributions.sort(key=lambda c: c.abs_importance, reverse=True)
        top_positive = [c.feature_name for c in contributions if c.shap_value > 0][:5]
        top_negative = [c.feature_name for c in contributions if c.shap_value < 0][:5]
        return {'model_type': self._model_type, 'base_value': round(base_value, 6), 'predicted_value': round(predicted_value, 6), 'feature_contributions': contributions, 'top_positive_drivers': top_positive, 'top_negative_drivers': top_negative}

    @staticmethod
    def _feature_vector_to_df(site: SiteFeatureVector) -> pd.DataFrame:
        return pd.DataFrame([{'solar_irradiance_kwh_m2_day': site.solar_irradiance_kwh_m2_day, 'wind_speed_50m_m_s': site.wind_speed_50m_m_s, 'solar_capacity_factor_pct': site.solar_capacity_factor_pct, 'wind_capacity_factor_pct': site.wind_capacity_factor_pct, 'elevation_m': site.elevation_m, 'land_area_sqkm': site.land_area_sqkm, 'nearest_substation_km': site.nearest_substation_km, 'nearest_power_line_km': site.nearest_power_line_km, 'nearest_road_km': site.nearest_road_km, 'conflict_count': float(site.conflict_count), 'infrastructure_count': float(site.infrastructure_count), 'avg_temp_c': site.avg_temp_c}])
_shap_explainer: SHAPExplainer | None = None

def get_shap_explainer() -> SHAPExplainer:
    global _shap_explainer
    if _shap_explainer is None:
        _shap_explainer = SHAPExplainer()
    return _shap_explainer
