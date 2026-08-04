"""
SiteScout — Centralized Application Settings.

Loads all configuration from environment variables via pydantic-settings.
Replaces hardcoded secrets and provides a single source of truth.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration loaded from .env or environment variables."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── JWT Authentication ────────────────────────────────────────────────
    SECRET_KEY: str = "super_secret_dev_key_change_in_prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── ML Model Paths ────────────────────────────────────────────────────
    ML_MODELS_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "models"
    )

    # ── External API Config ───────────────────────────────────────────────
    NASA_POWER_BASE_URL: str = "https://power.larc.nasa.gov/api/temporal/climatology/point"
    OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
    OVERPASS_MIRROR_URL: str = "https://overpass.kumi.systems/api/interpreter"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton of application settings."""
    return Settings()  # type: ignore[call-arg]
