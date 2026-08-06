from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(ProjectCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: Optional[datetime] = None

class SiteCreate(BaseModel):
    name: str
    region: Optional[str] = None
    latitude: float
    longitude: float
    land_area_sqkm: Optional[float] = None
    elevation_m: Optional[float] = None
    land_ownership: Optional[str] = None
