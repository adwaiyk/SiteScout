import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, database
from auth import get_current_user
from ingestion import fetch_nasa_power_data, fetch_osm_infrastructure
from geoalchemy2.shape import to_shape

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
    return {"message": f"Site {site.name} registered successfully"}

@router.get("/{project_id}/sites/{site_id}/data", status_code=status.HTTP_200_OK)
async def get_site_environmental_data(project_id: str, site_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
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

    # 3. Fetch from NASA and OSM simultaneously!
    nasa_data, osm_data = await asyncio.gather(
        fetch_nasa_power_data(latitude=latitude, longitude=longitude),
        fetch_osm_infrastructure(latitude=latitude, longitude=longitude)
    )
    
    return {
        "site_name": site.name,
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "environmental_baseline": nasa_data,
        "infrastructure_baseline": osm_data
    }