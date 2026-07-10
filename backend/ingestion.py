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

async def fetch_osm_infrastructure(latitude: float, longitude: float, radius_meters: int = 5000):
    url = "https://overpass-api.de/api/interpreter"
    
    # Overpass QL query: Find power lines, substations, and major roads within the radius
    query = f"""
    [out:json][timeout:25];
    (
      way["power"](around:{radius_meters},{latitude},{longitude});
      node["power"="substation"](around:{radius_meters},{latitude},{longitude});
      way["highway"~"motorway|trunk|primary"](around:{radius_meters},{latitude},{longitude});
    );
    out count;
    """
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data={"data": query}, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            
            elements = data.get("elements", [])
            if elements:
                counts = elements[0].get("tags", {})
                return {
                    "nearby_power_infrastructure_count": counts.get("nodes", 0) + counts.get("ways", 0),
                    "search_radius_km": radius_meters / 1000
                }
            return {"nearby_power_infrastructure_count": 0, "search_radius_km": radius_meters / 1000}
            
        except httpx.HTTPError as e:
            # We don't want the whole request to fail if OSM is temporarily down
            print(f"OSM fetch warning: {str(e)}")
            return {"nearby_power_infrastructure_count": None, "error": "OSM data unavailable"}