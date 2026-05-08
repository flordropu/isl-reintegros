"""Schemas de Reintegro y Documento."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.core.constants import ReintegroTipo, ReintegroEstado, TipoCuenta, TipoDocumento
from app.schemas.trabajador import SiniestroOut


class ReintegroBase(BaseModel):
    siniestro_id: int
    tipo: ReintegroTipo
    monto_solicitado: float | None = None
    monto_total_ticket: float | None = None
    datos_especificos: dict[str, Any] = Field(default_factory=dict)
    observaciones: str | None = None
    cbu_pago: str | None = None
    alias_pago: str | None = None
    tipo_cuenta_pago: TipoCuenta | None = None


class ReintegroCreate(ReintegroBase):
    pass


class ReintegroUpdate(BaseModel):
    tipo: ReintegroTipo | None = None
    monto_solicitado: float | None = None
    monto_aprobado: float | None = None
    monto_total_ticket: float | None = None
    datos_especificos: dict[str, Any] | None = None
    observaciones: str | None = None
    motivo_rechazo: str | None = None
    cbu_pago: str | None = None
    alias_pago: str | None = None
    tipo_cuenta_pago: TipoCuenta | None = None
    asignado_a_id: int | None = None


class CambioEstadoRequest(BaseModel):
    nuevo_estado: ReintegroEstado
    observaciones: str | None = None
    motivo_rechazo: str | None = None
    monto_aprobado: float | None = None


class DocumentoOut(BaseModel):
    id: int
    tipo: TipoDocumento
    nombre_original: str
    nombre_archivo: str
    mime_type: str | None
    tamanio_bytes: int | None
    procesado: bool
    metodo_extraccion: str | None
    datos_extraidos: dict[str, Any] | None
    creado_en: datetime

    class Config:
        from_attributes = True


class ReintegroOut(BaseModel):
    id: int
    codigo: str
    siniestro_id: int
    tipo: ReintegroTipo
    estado: ReintegroEstado
    monto_solicitado: float | None
    monto_aprobado: float | None
    monto_total_ticket: float | None
    fecha_vencimiento_sla: datetime | None
    datos_especificos: dict[str, Any] | None
    observaciones: str | None
    motivo_rechazo: str | None
    creado_por_id: int
    asignado_a_id: int | None
    cbu_pago: str | None
    alias_pago: str | None
    tipo_cuenta_pago: TipoCuenta | None
    fecha_aprobacion: datetime | None
    fecha_liquidacion: datetime | None
    fecha_pago: datetime | None
    creado_en: datetime
    actualizado_en: datetime

    class Config:
        from_attributes = True


class ReintegroDetalleOut(ReintegroOut):
    siniestro: SiniestroOut | None = None
    documentos: list[DocumentoOut] = []


class ExtraccionPDFOut(BaseModel):
    """Resultado de procesar un PDF cargado."""
    metodo: str
    texto_extraido: str
    paginas: int
    datos_estructurados: dict[str, Any]


class DashboardStats(BaseModel):
    casos_ingresados: int
    pendientes: int
    vencidos_sla: int
    proximos_vencer: int
    aprobados: int
    rechazados: int
    monto_total_liquidado: float
    monto_total_pagado: float
    por_tipo: dict[str, int]
    por_estado: dict[str, int]
    por_operador: list[dict[str, Any]]
