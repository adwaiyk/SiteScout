from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, database
from auth import get_current_user

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