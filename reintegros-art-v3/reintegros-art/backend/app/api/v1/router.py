"""Agregador de routers v1."""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.trabajadores import router as trabajadores_router
from app.api.v1.reintegros import router as reintegros_router
from app.api.v1.audit import router as audit_router
from app.api.v1.parametros import router as parametros_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(trabajadores_router)
api_router.include_router(reintegros_router)
api_router.include_router(audit_router)
api_router.include_router(parametros_router)
