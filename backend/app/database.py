from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import get_settings
_settings = get_settings()
engine = create_engine(_settings.DATABASE_URL, pool_pre_ping=True, pool_recycle=300, connect_args={'sslmode': 'require'})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
