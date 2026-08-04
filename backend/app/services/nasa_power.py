"""
SiteScout — NASA POWER Environmental Data Service.

Fetches multi-year climatology data (Solar Irradiance, Wind Speed, Temperature)
from the NASA POWER API for specific geographic coordinates.
"""

from __future__ import annotations

from typing import Any, Dict

import httpx

from app.config import get_settings

_settings = get_settings()


async def fetch_nasa_environmental_data(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch annual climatology averages from the NASA POWER API.

    Parameters
    ----------
    lat : float
        Latitude in decimal degrees (-90 to 90).
    lon : float
        Longitude in decimal degrees (-180 to 180).

    Returns
    -------
    dict
        Contains annual solar irradiance (kWh/m²/day), wind speed at 50 m (m/s),
        average temperature (°C), and raw monthly breakdowns.
    """
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,WS50M,T2M",
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "format": "JSON",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(_settings.NASA_POWER_BASE_URL, params=params)

        if response.status_code != 200:
            raise RuntimeError(
                f"NASA POWER API request failed with status code: {response.status_code}"
            )

        data = response.json()
        properties = data.get("properties", {}).get("parameter", {})

        annual_solar = properties.get("ALLSKY_SFC_SW_DWN", {}).get("ANN", 0.0)
        annual_wind = properties.get("WS50M", {}).get("ANN", 0.0)
        annual_temp = properties.get("T2M", {}).get("ANN", 0.0)

        return {
            "latitude": lat,
            "longitude": lon,
            "annual_solar_irradiance_kwh_m2_day": annual_solar,
            "annual_wind_speed_50m_m_s": annual_wind,
            "annual_avg_temp_c": annual_temp,
            "raw_monthly_solar": properties.get("ALLSKY_SFC_SW_DWN", {}),
            "raw_monthly_wind": properties.get("WS50M", {}),
        }


async def fetch_nasa_power_data(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Lightweight wrapper returning only annual averages (legacy compatibility).
    Used by the older projects.py analyze endpoint.
    """
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,WS50M",
        "community": "RE",
        "longitude": longitude,
        "latitude": latitude,
        "format": "JSON",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(_settings.NASA_POWER_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        return {
            "annual_solar_irradiance_kwh_m2_day": data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]["ANN"],
            "annual_wind_speed_50m_m_s": data["properties"]["parameter"]["WS50M"]["ANN"],
        }
