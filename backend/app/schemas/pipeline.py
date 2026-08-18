"""
Pipeline Schemas — SiteScout Milestone 4
Request/response models for the unified analysis pipeline, narrative, Q&A, and yield calculator.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FullAnalysisRequest(BaseModel):
    latitude: float = Field(ge=-90.0, le=90.0, description="Site latitude")
    longitude: float = Field(ge=-180.0, le=180.0, description="Site longitude")
    system_capacity_kw: float = Field(default=1000.0, gt=0, description="System capacity in kW")
    land_area_sqkm: float = Field(default=5.0, ge=0.0, description="Available land area in km²")
    elevation_m: float = Field(default=0.0, description="Site elevation in meters")
    slope_deg: float = Field(default=0.0, ge=0.0, le=90.0, description="Terrain slope in degrees")
    energy_type: str = Field(default="hybrid", description="solar | wind | hybrid")
    fit_usd_per_mwh: float = Field(default=65.0, gt=0, description="Feed-in tariff in USD/MWh")
    ndvi: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="NDVI vegetation index (optional)")
    land_cover: Optional[str] = Field(default=None, description="Land cover type (optional)")


class NarrativeRequest(BaseModel):
    """Request for AI-generated investment narrative."""
    pass  # Uses stored analysis data from the site's ScanLog


class QARequest(BaseModel):
    """Request for AI Q&A about a site's analysis."""
    question: str = Field(min_length=5, max_length=500, description="Natural-language question about the site")


class QAResponse(BaseModel):
    answer: Optional[str] = None
    available: bool = False
    model: Optional[str] = None
    error: Optional[str] = None


class NarrativeResponse(BaseModel):
    narrative: Optional[str] = None
    available: bool = False
    model: Optional[str] = None
    error: Optional[str] = None


class YieldCalculatorRequest(BaseModel):
    """Interactive yield calculator — adjust capacity, tariff, tech mix."""
    ghi_kwh_m2_day: float = Field(gt=0, description="Solar irradiance")
    wind_speed_m_s: float = Field(ge=0, description="Wind speed at 50m")
    avg_temp_c: float = Field(default=25.0, description="Average temperature °C")
    slope_deg: float = Field(default=0.0, ge=0.0, description="Slope in degrees")
    solar_capacity_mw: float = Field(default=1.0, ge=0.0, description="Solar capacity in MW")
    wind_capacity_mw: float = Field(default=1.0, ge=0.0, description="Wind capacity in MW")
    energy_type: str = Field(default="hybrid", description="solar | wind | hybrid")
    fit_usd_per_mwh: float = Field(default=65.0, gt=0, description="Tariff rate $/MWh")
    land_area_sqkm: float = Field(default=5.0, ge=0.0, description="Land area km²")
