"""
SiteScout — Shared API Dependencies.

Provides reusable FastAPI Depends() callables for database sessions
and user authentication across all route modules.
"""

from __future__ import annotations

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models.models import User

_settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy database session, ensuring cleanup on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode and validate the JWT bearer token, then return the
    corresponding User ORM instance.

    Raises HTTP 401 on invalid/expired tokens or missing users.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            _settings.SECRET_KEY,
            algorithms=[_settings.ALGORITHM],
        )
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user
