import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, database
from auth import get_current_user
from geoalchemy2.shape import to_shape

# Import Intelligence Engines
from ingestion import fetch_nasa_power_data, fetch_osm_infrastructure
from conflict_detector import detect_land_use_conflicts
from prediction_engine import predict_solar_potential, predict_wind_potential

router = APIRouter(prefix="/projects", tags=["Project & Site Management"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    new_project = models.Project(
        owner_id=current_user.id,
        name=project.name,
        description=project.description
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return {"message": "Project created successfully", "project_id": new_project.id}

@router.get("/", response_model=list[schemas.ProjectResponse])
def get_user_projects(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Fetch all projects owned by the currently logged-in user
    projects = db.query(models.Project).filter(models.Project.owner_id == current_user.id).all()
    return projects

@router.post("/{project_id}/sites", status_code=status.HTTP_201_CREATED)
def register_site(project_id: str, site: schemas.SiteCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Verify project belongs to user
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    # Convert lat/lon to PostGIS WKT Point (Format: POINT(longitude latitude))
    point_wkt = f"POINT({site.longitude} {site.latitude})"
    
    new_site = models.Site(
        project_id=project.id,
        name=site.name,
        region=site.region,
        coordinates=point_wkt,
        land_area_sqkm=site.land_area_sqkm,
        elevation_m=site.elevation_m,
        land_ownership=site.land_ownership
    )
    db.add(new_site)
    db.commit()
    return {"message": f"Site {site.name} registered successfully", "site_id": new_site.id}

@router.post("/{project_id}/sites/{site_id}/analyze", status_code=status.HTTP_200_OK)
async def analyze_and_save_site(
    project_id: str, 
    site_id: str, 
    system_capacity_kw: float = 1000.0,
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # 1. Verify ownership
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
        
    site = db.query(models.Site).filter(models.Site.id == site_id, models.Site.project_id == project.id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # 2. Extract coordinates
    point = to_shape(site.coordinates)
    longitude, latitude = point.x, point.y

    # 3. Fetch from all intelligence APIs simultaneously!
    nasa_data, osm_data, conflict_data = await asyncio.gather(
        fetch_nasa_power_data(latitude=latitude, longitude=longitude),
        fetch_osm_infrastructure(latitude=latitude, longitude=longitude),
        detect_land_use_conflicts(lat=latitude, lon=longitude)
    )
    
    # 4. Generate Machine Learning Predictions
    solar_prediction = predict_solar_potential(
        irradiance_kwh_m2_day=nasa_data.get("annual_solar_irradiance_kwh_m2_day", 0),
        avg_temp_c=nasa_data.get("annual_avg_temp_c", 25),
        system_capacity_kw=system_capacity_kw
    )
    
    wind_prediction = predict_wind_potential(
        wind_speed_m_s=nasa_data.get("annual_wind_speed_50m_m_s", 0),
        system_capacity_kw=system_capacity_kw
    )
    
    # 5. Compile Master JSON
    full_analysis = {
        "site_name": site.name,
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "environmental_baseline": nasa_data,
        "infrastructure_baseline": osm_data,
        "land_use_conflicts": conflict_data,
        "predictions": {
            "solar": solar_prediction,
            "wind": wind_prediction
        }
    }
    
    # 6. Save Scan Log to Database
    scan_log = models.ScanLog(
        site_id=site.id,
        solar_yield_mwh=solar_prediction.get("annual_energy_output_mwh"),
        wind_yield_mwh=wind_prediction.get("annual_energy_output_mwh"),
        is_unsuitable=conflict_data.get("is_unsuitable", False),
        full_analysis_json=full_analysis
    )
    
    db.add(scan_log)
    db.commit()

    return full_analysis