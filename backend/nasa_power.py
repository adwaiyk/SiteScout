import httpx
import asyncio
from typing import Dict, Any

NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"

async def fetch_nasa_environmental_data(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetches multi-year climatology data (Solar Irradiance & Wind Speed) 
    from the NASA POWER API for specific geographic coordinates.
    """
    # Updated parameters:
    # ALLSKY_SFC_SW_DWN -> Surface Shortwave Solar Irradiance (kWh/m²/day)
    # WS50M             -> Wind Speed at 50-meter hub height (m/s)
    # T2M               -> Air Temperature at 2 meters (°C)
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,WS50M,T2M",
        "community": "RE",  # Renewable Energy
        "longitude": lon,
        "latitude": lat,
        "format": "JSON"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(NASA_POWER_BASE_URL, params=params)
        
        if response.status_code != 200:
            raise RuntimeError(f"NASA POWER API request failed with status code: {response.status_code}")
            
        data = response.json()
        properties = data.get("properties", {}).get("parameter", {})
        
        # Extract Annual Averages ('ANN')
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
            "raw_monthly_wind": properties.get("WS50M", {})
        }

if __name__ == "__main__":
    test_lat, test_lon = 19.7515, 75.7139
    print(f"Fetching real NASA POWER climate data for Lat: {test_lat}, Lon: {test_lon}...")
    
    result = asyncio.run(fetch_nasa_environmental_data(test_lat, test_lon))
    
    print("\n--- NASA POWER Data Ingested Successfully ---")
    print(f"Annual Solar Irradiance: {result['annual_solar_irradiance_kwh_m2_day']} kWh/m²/day")
    print(f"Annual Wind Speed (50m): {result['annual_wind_speed_50m_m_s']} m/s")
    print(f"Avg Temperature: {result['annual_avg_temp_c']} °C")