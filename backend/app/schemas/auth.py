"""
SiteScout — Authentication Pydantic Schemas.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for POST /auth/register."""

    email: EmailStr
    password: str
    full_name: str
    role: str
    organization: Optional[str] = None


class Token(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str


class LoginResponse(Token):
    """Extended token response that includes user profile data for the frontend."""

    username: str
    email: str
    full_name: str


class UserProfile(BaseModel):
    """Schema for the GET /auth/me endpoint."""

    email: str
    full_name: str
    role: str
    organization: Optional[str] = None
