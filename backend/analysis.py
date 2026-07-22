from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio

# Import the engines we just built
from nasa_power import fetch_nasa_environmental_data
from infrastructure_engine import fetch_osm_infrastructure

router = APIRouter(prefix="/api/analysis", tags=["Site Analysis"])

# Define what the frontend needs to send us
class SiteAnalysisRequest(BaseModel):
    latitude: float
    longitude: float

@router.post("/scan-site")
async def scan_new_site(request: SiteAnalysisRequest):
    """
    Takes live coordinates from the frontend and concurrently fetches 
    climate and infrastructure data for that specific location.
    """
    try:
        # We use asyncio.gather to fetch from NASA and OSM at the exact same time!
        # This cuts the loading time in half for your users.
        nasa_task = fetch_nasa_environmental_data(request.latitude, request.longitude)
        osm_task = fetch_osm_infrastructure(request.latitude, request.longitude, radius_m=10000)
        
        # Wait for both APIs to finish
        nasa_data, osm_data = await asyncio.gather(nasa_task, osm_task)
        
        # Combine the results into one massive intelligence payload
        return {
            "status": "success",
            "coordinates": {
                "latitude": request.latitude,
                "longitude": request.longitude
            },
            "climate_intelligence": nasa_data,
            "infrastructure_intelligence": osm_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis Engine Error: {str(e)}")