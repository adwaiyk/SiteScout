from __future__ import annotations
import os
from typing import Any, Dict
import joblib
import pandas as pd
from app.config import get_settings
_settings = get_settings()
_SOLAR_MODEL_PATH = os.path.join(_settings.ML_MODELS_DIR, 'solar_model.joblib')
_WIND_MODEL_PATH = os.path.join(_settings.ML_MODELS_DIR, 'wind_model.joblib')
solar_model = joblib.load(_SOLAR_MODEL_PATH) if os.path.exists(_SOLAR_MODEL_PATH) else None
wind_model = joblib.load(_WIND_MODEL_PATH) if os.path.exists(_WIND_MODEL_PATH) else None

def predict_solar_potential(irradiance_kwh_m2_day: float, avg_temp_c: float, system_capacity_kw: float=1000.0) -> Dict[str, Any]:
    if solar_model is not None:
        input_data = pd.DataFrame([{'irradiance': irradiance_kwh_m2_day, 'temperature': avg_temp_c, 'capacity_kw': system_capacity_kw}])
        annual_mwh = float(solar_model.predict(input_data)[0])
        inference_source = 'XGBoost ML Model'
    else:
        base_pr = 0.75
        temp_penalty = (avg_temp_c - 25.0) * 0.004 if avg_temp_c > 25.0 else 0
        annual_mwh = irradiance_kwh_m2_day * 365 * system_capacity_kw * (base_pr - temp_penalty) / 1000
        inference_source = 'Physics Heuristic Engine'
    max_possible_mwh = system_capacity_kw * 8760 / 1000
    capacity_factor = annual_mwh / max_possible_mwh * 100 if max_possible_mwh > 0 else 0.0
    return {'assumed_capacity_kw': system_capacity_kw, 'annual_energy_output_mwh': round(annual_mwh, 2), 'capacity_factor_percent': round(capacity_factor, 2), 'inference_engine': inference_source, 'suitability': 'Excellent' if capacity_factor > 18 else 'Moderate' if capacity_factor > 14 else 'Low'}

def predict_wind_potential(wind_speed_m_s: float, system_capacity_kw: float=1000.0) -> Dict[str, Any]:
    if wind_model is not None:
        input_data = pd.DataFrame([{'wind_speed': wind_speed_m_s, 'capacity_kw': system_capacity_kw}])
        annual_mwh = float(wind_model.predict(input_data)[0])
        inference_source = 'XGBoost ML Model'
    else:
        if wind_speed_m_s < 3.0:
            annual_mwh = 0.0
        else:
            cf = min(0.5, max(0, 0.087 * wind_speed_m_s - 0.2))
            annual_mwh = system_capacity_kw * 8760 * cf / 1000
        inference_source = 'Physics Heuristic Engine'
    max_possible_mwh = system_capacity_kw * 8760 / 1000
    capacity_factor = annual_mwh / max_possible_mwh * 100 if max_possible_mwh > 0 else 0.0
    return {'assumed_capacity_kw': system_capacity_kw, 'annual_energy_output_mwh': round(annual_mwh, 2), 'capacity_factor_percent': round(capacity_factor, 2), 'inference_engine': inference_source, 'suitability': 'Excellent' if capacity_factor > 30 else 'Moderate' if capacity_factor > 20 else 'Low'}
