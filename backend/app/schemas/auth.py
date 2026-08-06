from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, EmailStr

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
    username: str
    email: str
    full_name: str

class UserProfile(BaseModel):
    email: str
    full_name: str
    role: str
    organization: Optional[str] = None
