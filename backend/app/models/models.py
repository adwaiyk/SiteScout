"""
SiteScout — SQLAlchemy ORM Models.

Defines all database tables: User, Project, Site, ScanLog.
Uses PostGIS geometry types for geographic coordinate storage.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)  # planner | gis_analyst | project_manager | admin
    organization = Column(String(255))
    phone = Column(String(20))
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    is_active = Column(Boolean, default=True)


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    owner = relationship("User")
    sites = relationship("Site", back_populates="project", cascade="all, delete-orphan")


class Site(Base):
    __tablename__ = "sites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    region = Column(String(100))
    # PostGIS Point storage (SRID 4326 = standard WGS-84 GPS Lat/Lon)
    coordinates = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    land_area_sqkm = Column(Numeric)
    elevation_m = Column(Numeric)
    land_ownership = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    project = relationship("Project", back_populates="sites")
    logs = relationship("ScanLog", back_populates="site", cascade="all, delete-orphan")


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(
        UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False
    )
    solar_yield_mwh = Column(Numeric, nullable=True)
    wind_yield_mwh = Column(Numeric, nullable=True)
    is_unsuitable = Column(Boolean, default=False)
    full_analysis_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    site = relationship("Site", back_populates="logs")
