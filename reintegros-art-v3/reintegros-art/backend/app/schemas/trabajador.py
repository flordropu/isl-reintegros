"""Schemas de Trabajador y Siniestro."""
from datetime import datetime
from pydantic import BaseModel
from app.core.constants import TipoCuenta


class TrabajadorBase(BaseModel):
    cuil: str
    nombre_completo: str
    dni: str | None = None
    telefono: str | None = None
    telefono_verificado: bool = False
    cbu: str | None = None
    alias_cbu: str | None = None
    tipo_cuenta: TipoCuenta | None = None
    cbu_verificado: bool = False


class TrabajadorCreate(TrabajadorBase):
    pass


class TrabajadorUpdate(BaseModel):
    nombre_completo: str | None = None
    dni: str | None = None
    telefono: str | None = None
    telefono_verificado: bool | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    tipo_cuenta: TipoCuenta | None = None
    cbu_verificado: bool | None = None


class TrabajadorOut(TrabajadorBase):
    id: int
    creado_en: datetime

    class Config:
        from_attributes = True


class SiniestroBase(BaseModel):
    numero: str
    trabajador_id: int
    fecha_siniestro: datetime | None = None
    descripcion: str | None = None


class SiniestroCreate(SiniestroBase):
    pass


class SiniestroOut(SiniestroBase):
    id: int
    activo: bool
    creado_en: datetime
    trabajador: TrabajadorOut | None = None

    class Config:
        from_attributes = True
