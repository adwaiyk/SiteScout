from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Numeric, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import uuid
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False) # planner, gis_analyst, project_manager, admin
    organization = Column(String(255))
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    system_type = Column(String, default="Solar")
    
    owner = relationship("User")
    sites = relationship("Site", back_populates="project", cascade="all, delete-orphan")

class Site(Base):
    __tablename__ = "sites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    region = Column(String(100))
    # PostGIS Point storage (SRID 4326 is standard GPS Long/Lat)
    coordinates = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    land_area_sqkm = Column(Numeric)
    elevation_m = Column(Numeric)
    land_ownership = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="sites")
    logs = relationship("ScanLog", back_populates="site", cascade="all, delete-orphan")

class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"))
    solar_yield_mwh = Column(Numeric, nullable=True)
    wind_yield_mwh = Column(Numeric, nullable=True)
    is_unsuitable = Column(Boolean, default=False)
    full_analysis_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    site = relationship("Site", back_populates="logs")