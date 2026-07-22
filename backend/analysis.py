from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio

from nasa_power import fetch_nasa_environmental_data
from infrastructure_engine import fetch_osm_infrastructure
from conflict_detector import detect_land_use_conflicts
from prediction_engine import predict_solar_potential, predict_wind_potential 

router = APIRouter(prefix="/api/analysis", tags=["Site Analysis"])

class SiteAnalysisRequest(BaseModel):
    latitude: float
    longitude: float
    system_capacity_kw: float = 1000.0 # Allow frontend to specify plant size, default 1MW

@router.post("/scan-site")
async def scan_new_site(request: SiteAnalysisRequest):
    try:
        nasa_task = fetch_nasa_environmental_data(request.latitude, request.longitude)
        osm_task = fetch_osm_infrastructure(request.latitude, request.longitude, radius_m=10000)
        conflict_task = detect_land_use_conflicts(request.latitude, request.longitude)
        
        nasa_data, osm_data, conflict_data = await asyncio.gather(nasa_task, osm_task, conflict_task)
        solar_prediction = predict_solar_potential(
            irradiance_kwh_m2_day=nasa_data["annual_solar_irradiance_kwh_m2_day"],
            avg_temp_c=nasa_data["annual_avg_temp_c"],
            system_capacity_kw=request.system_capacity_kw
        )
        
        wind_prediction = predict_wind_potential(
            wind_speed_m_s=nasa_data["annual_wind_speed_50m_m_s"],
            system_capacity_kw=request.system_capacity_kw
        )
        
        # 3. Return the massive aggregated payload
        return {
            "status": "success",
            "coordinates": {
                "latitude": request.latitude,
                "longitude": request.longitude
            },
            "climate_intelligence": nasa_data,
            "infrastructure_intelligence": osm_data,
            "land_use_conflicts": conflict_data,
            "predictions": {
                "solar": solar_prediction,
                "wind": wind_prediction
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis Engine Error: {str(e)}")