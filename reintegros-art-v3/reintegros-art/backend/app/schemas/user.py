"""Schemas de User y autenticación."""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.core.constants import UserRole


class UserBase(BaseModel):
    email: EmailStr
    nombre_completo: str
    role: UserRole = UserRole.OPERADOR
    region: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    nombre_completo: str | None = None
    role: UserRole | None = None
    region: str | None = None
    activo: bool | None = None
    bloqueado: bool | None = None
    password: str | None = Field(default=None, min_length=8)


class UserOut(UserBase):
    id: int
    activo: bool
    bloqueado: bool
    creado_en: datetime
    ultimo_login: datetime | None = None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
