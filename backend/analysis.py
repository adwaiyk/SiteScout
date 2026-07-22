from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio

from nasa_power import fetch_nasa_environmental_data
from infrastructure_engine import fetch_osm_infrastructure
from conflict_detector import detect_land_use_conflicts 

router = APIRouter(prefix="/api/analysis", tags=["Site Analysis"])

class SiteAnalysisRequest(BaseModel):
    latitude: float
    longitude: float

@router.post("/scan-site")
async def scan_new_site(request: SiteAnalysisRequest):
    try:
        nasa_task = fetch_nasa_environmental_data(request.latitude, request.longitude)
        osm_task = fetch_osm_infrastructure(request.latitude, request.longitude, radius_m=10000)
        conflict_task = detect_land_use_conflicts(request.latitude, request.longitude)
        
        nasa_data, osm_data, conflict_data = await asyncio.gather(nasa_task, osm_task, conflict_task)
        
        return {
            "status": "success",
            "coordinates": {
                "latitude": request.latitude,
                "longitude": request.longitude
            },
            "climate_intelligence": nasa_data,
            "infrastructure_intelligence": osm_data,
            "land_use_conflicts": conflict_data # Added to our final payload
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis Engine Error: {str(e)}")