"""
SiteScout — Authentication API Routes.

Endpoints:
  POST /auth/register  — Create a new user account
  POST /auth/login     — Authenticate and receive JWT
  GET  /auth/me        — Retrieve current user's profile
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.config import get_settings
from app.models.models import User
from app.schemas.auth import LoginResponse, UserCreate, UserProfile

router = APIRouter(prefix="/auth", tags=["Authentication"])

_settings = get_settings()
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password Utilities ────────────────────────────────────────────────────

def _verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def _get_password_hash(password: str) -> str:
    return _pwd_context.hash(password)


def _create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _settings.SECRET_KEY, algorithm=_settings.ALGORITHM)


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/register", response_model=LoginResponse)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
) -> dict:
    """Register a new user and return a JWT token."""
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    raw_password = (
        user.password.get_secret_value()
        if hasattr(user.password, "get_secret_value")
        else user.password
    )
    hashed_password = _get_password_hash(raw_password)

    new_user = User(
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name,
        role=user.role,
        organization=user.organization if user.organization else "Independent",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = _create_access_token(
        data={"sub": new_user.email, "role": new_user.role}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": new_user.full_name,
        "email": new_user.email,
        "full_name": new_user.full_name,
    }


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    """Authenticate with email + password and receive a JWT token."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not _verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = _create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.full_name,
        "email": user.email,
        "full_name": user.full_name,
    }


@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)) -> dict:
    """Return the current authenticated user's profile."""
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "organization": current_user.organization,
    }
