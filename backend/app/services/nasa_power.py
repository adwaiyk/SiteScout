from __future__ import annotations
from typing import Any, Dict
import httpx
from app.config import get_settings
_settings = get_settings()

import logging

logger = logging.getLogger(__name__)

async def fetch_nasa_environmental_data(lat: float, lon: float) -> Dict[str, Any]:
    params = {'parameters': 'ALLSKY_SFC_SW_DWN,WS50M,T2M', 'community': 'RE', 'longitude': lon, 'latitude': lat, 'format': 'JSON'}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(_settings.NASA_POWER_BASE_URL, params=params)
            if response.status_code != 200:
                logger.warning(f'NASA POWER API request failed with status code: {response.status_code}')
                return _fallback_nasa_response(lat, lon)
            data = response.json()
            properties = data.get('properties', {}).get('parameter', {})
            annual_solar = properties.get('ALLSKY_SFC_SW_DWN', {}).get('ANN', 0.0)
            annual_wind = properties.get('WS50M', {}).get('ANN', 0.0)
            annual_temp = properties.get('T2M', {}).get('ANN', 0.0)
            return {'latitude': lat, 'longitude': lon, 'annual_solar_irradiance_kwh_m2_day': annual_solar, 'annual_wind_speed_50m_m_s': annual_wind, 'annual_avg_temp_c': annual_temp, 'raw_monthly_solar': properties.get('ALLSKY_SFC_SW_DWN', {}), 'raw_monthly_wind': properties.get('WS50M', {})}
    except Exception as e:
        logger.warning(f'NASA POWER API timeout/error: {e}')
        return _fallback_nasa_response(lat, lon)

async def fetch_nasa_power_data(latitude: float, longitude: float) -> Dict[str, Any]:
    params = {'parameters': 'ALLSKY_SFC_SW_DWN,WS50M', 'community': 'RE', 'longitude': longitude, 'latitude': latitude, 'format': 'JSON'}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(_settings.NASA_POWER_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return {'annual_solar_irradiance_kwh_m2_day': data['properties']['parameter']['ALLSKY_SFC_SW_DWN']['ANN'], 'annual_wind_speed_50m_m_s': data['properties']['parameter']['WS50M']['ANN']}
    except Exception as e:
        logger.warning(f'NASA POWER legacy API error: {e}')
        return {'annual_solar_irradiance_kwh_m2_day': 5.0, 'annual_wind_speed_50m_m_s': 6.0}

def _fallback_nasa_response(lat: float, lon: float) -> Dict[str, Any]:
    # Generic fallback baseline for robustness
    return {
        'latitude': lat, 
        'longitude': lon, 
        'annual_solar_irradiance_kwh_m2_day': 5.0, 
        'annual_wind_speed_50m_m_s': 6.0, 
        'annual_avg_temp_c': 25.0, 
        'raw_monthly_solar': {}, 
        'raw_monthly_wind': {}
    }
