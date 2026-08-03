from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    organization: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginResponse(Token):
    """Extended token response that includes user profile data for the frontend."""
    username: str
    email: str
    full_name: str

class UserProfile(BaseModel):
    """Schema for the /auth/me endpoint."""
    email: str
    full_name: str
    role: str
    organization: Optional[str] = None
    
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(ProjectCreate):
    id: UUID
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class SiteCreate(BaseModel):
    name: str
    region: Optional[str] = None
    latitude: float
    longitude: float
    land_area_sqkm: Optional[float] = None
    elevation_m: Optional[float] = None
    land_ownership: Optional[str] = None