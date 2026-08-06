from __future__ import annotations
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.models.models import Project, ScanLog, Site, User
from app.schemas.projects import ProjectCreate, ProjectResponse, SiteCreate
from app.services.conflict_detector import detect_land_use_conflicts
from app.services.nasa_power import fetch_nasa_power_data
from app.services.infrastructure_engine import fetch_osm_infrastructure
from app.services.prediction_engine import predict_solar_potential, predict_wind_potential
router = APIRouter(prefix='/projects', tags=['Project & Site Management'])

@router.post('/', status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)) -> dict:
    new_project = Project(owner_id=current_user.id, name=project.name, description=project.description)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return {'message': 'Project created successfully', 'project_id': new_project.id}

@router.get('/', response_model=list[ProjectResponse])
def get_user_projects(db: Session=Depends(get_db), current_user: User=Depends(get_current_user)) -> list:
    projects = db.query(Project).filter(Project.owner_id == current_user.id).all()
    return projects

@router.post('/{project_id}/sites', status_code=status.HTTP_201_CREATED)
def register_site(project_id: str, site: SiteCreate, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)) -> dict:
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found or unauthorized')
    point_wkt = f'POINT({site.longitude} {site.latitude})'
    new_site = Site(project_id=project.id, name=site.name, region=site.region, coordinates=point_wkt, land_area_sqkm=site.land_area_sqkm, elevation_m=site.elevation_m, land_ownership=site.land_ownership)
    db.add(new_site)
    db.commit()
    return {'message': f'Site {site.name} registered successfully', 'site_id': new_site.id}

@router.post('/{project_id}/sites/{site_id}/analyze', status_code=status.HTTP_200_OK)
async def analyze_and_save_site(project_id: str, site_id: str, system_capacity_kw: float=1000.0, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)) -> dict:
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found or unauthorized')
    site = db.query(Site).filter(Site.id == site_id, Site.project_id == project.id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Site not found')
    point = to_shape(site.coordinates)
    longitude, latitude = (point.x, point.y)
    nasa_data, osm_data, conflict_data = await asyncio.gather(fetch_nasa_power_data(latitude=latitude, longitude=longitude), fetch_osm_infrastructure(lat=latitude, lon=longitude), detect_land_use_conflicts(lat=latitude, lon=longitude))
    solar_prediction = predict_solar_potential(irradiance_kwh_m2_day=nasa_data.get('annual_solar_irradiance_kwh_m2_day', 0), avg_temp_c=nasa_data.get('annual_avg_temp_c', 25), system_capacity_kw=system_capacity_kw)
    wind_prediction = predict_wind_potential(wind_speed_m_s=nasa_data.get('annual_wind_speed_50m_m_s', 0), system_capacity_kw=system_capacity_kw)
    full_analysis = {'site_name': site.name, 'coordinates': {'latitude': latitude, 'longitude': longitude}, 'environmental_baseline': nasa_data, 'infrastructure_baseline': osm_data, 'land_use_conflicts': conflict_data, 'predictions': {'solar': solar_prediction, 'wind': wind_prediction}}
    scan_log = ScanLog(site_id=site.id, solar_yield_mwh=solar_prediction.get('annual_energy_output_mwh'), wind_yield_mwh=wind_prediction.get('annual_energy_output_mwh'), is_unsuitable=conflict_data.get('is_unsuitable', False), full_analysis_json=full_analysis)
    db.add(scan_log)
    db.commit()
    return full_analysis
