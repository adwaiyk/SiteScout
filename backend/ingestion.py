import httpx
from fastapi import HTTPException

async def fetch_nasa_power_data(latitude: float, longitude: float):
    url = "https://power.larc.nasa.gov/api/temporal/climatology/point"
    
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,WS50M",
        "community": "RE",
        "longitude": longitude,
        "latitude": latitude,
        "format": "JSON"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            # Extract just the useful annual averages to keep the response clean
            return {
                "annual_solar_irradiance_kwh_m2_day": data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]["ANN"],
                "annual_wind_speed_50m_m_s": data["properties"]["parameter"]["WS50M"]["ANN"]
            }
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to fetch data from NASA POWER: {str(e)}")