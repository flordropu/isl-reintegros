"""
Servicio de Reintegros: lógica de negocio.

Responsabilidades:
- Generar códigos únicos (RT-YYYY-NNNN)
- Calcular fechas de vencimiento de SLA
- Validar transiciones de estado
- Registrar entradas en el audit log
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models import Reintegro, AuditLog, User
from app.core.constants import (
    ReintegroEstado, TRANSICIONES_PERMITIDAS,
)
from app.core.config import settings


def generar_codigo_reintegro(db: Session) -> str:
    """Genera código único RT-YYYY-NNNN (correlativo por año)."""
    anio = datetime.now(timezone.utc).year
    prefijo = f"RT-{anio}-"
    ultimo = (
        db.query(Reintegro)
        .filter(Reintegro.codigo.like(f"{prefijo}%"))
        .order_by(Reintegro.id.desc())
        .first()
    )
    if ultimo and ultimo.codigo.startswith(prefijo):
        try:
            n = int(ultimo.codigo.replace(prefijo, ""))
        except ValueError:
            n = 0
    else:
        n = 0
    return f"{prefijo}{n + 1:04d}"


def calcular_vencimiento_sla(dias: int | None = None) -> datetime:
    """Calcula fecha de vencimiento de SLA (días corridos por simplicidad en MVP)."""
    d = dias if dias is not None else settings.SLA_DEFAULT_DAYS
    return datetime.now(timezone.utc) + timedelta(days=d)


def validar_transicion(actual: ReintegroEstado, nuevo: ReintegroEstado) -> bool:
    """Verifica si la transición de estado es válida según el workflow."""
    permitidos = TRANSICIONES_PERMITIDAS.get(actual, [])
    return nuevo in permitidos


def estado_sla(reintegro: Reintegro) -> str:
    """
    Devuelve el estado del SLA para semaforización:
    'verde' = en término
    'amarillo' = próximo a vencer (< SLA_WARNING_HOURS)
    'rojo' = vencido
    'na' = no aplica (estados terminales)
    """
    if reintegro.estado in (ReintegroEstado.PAGADO, ReintegroEstado.RECHAZADO, ReintegroEstado.LIQUIDADO):
        return "na"
    if not reintegro.fecha_vencimiento_sla:
        return "verde"

    ahora = datetime.now(timezone.utc)
    vence = reintegro.fecha_vencimiento_sla
    if vence.tzinfo is None:
        vence = vence.replace(tzinfo=timezone.utc)

    if ahora > vence:
        return "rojo"
    if ahora + timedelta(hours=settings.SLA_WARNING_HOURS) > vence:
        return "amarillo"
    return "verde"


def registrar_audit(
    db: Session,
    *,
    usuario_id: int | None,
    accion: str,
    descripcion: str | None = None,
    reintegro_id: int | None = None,
    datos_previos: dict | None = None,
    datos_nuevos: dict | None = None,
    ip: str | None = None,
    commit: bool = True,
) -> AuditLog:
    """Crea un registro en el audit log."""
    log = AuditLog(
        usuario_id=usuario_id,
        accion=accion,
        descripcion=descripcion,
        reintegro_id=reintegro_id,
        datos_previos=datos_previos,
        datos_nuevos=datos_nuevos,
        ip_origen=ip,
    )
    db.add(log)
    if commit:
        db.commit()
    return log


def cambiar_estado(
    db: Session,
    reintegro: Reintegro,
    nuevo: ReintegroEstado,
    usuario: User,
    *,
    observaciones: str | None = None,
    motivo_rechazo: str | None = None,
    monto_aprobado: float | None = None,
) -> Reintegro:
    """Cambia el estado de un reintegro validando la transición y dejando audit log."""
    if not validar_transicion(reintegro.estado, nuevo):
        raise ValueError(
            f"Transición no permitida: {reintegro.estado.value} → {nuevo.value}"
        )

    estado_previo = reintegro.estado
    reintegro.estado = nuevo

    if observaciones:
        reintegro.observaciones = observaciones
    if motivo_rechazo and nuevo == ReintegroEstado.RECHAZADO:
        reintegro.motivo_rechazo = motivo_rechazo
    if monto_aprobado is not None and nuevo == ReintegroEstado.APROBADO:
        reintegro.monto_aprobado = monto_aprobado

    ahora = datetime.now(timezone.utc)
    if nuevo == ReintegroEstado.APROBADO:
        reintegro.fecha_aprobacion = ahora
    elif nuevo == ReintegroEstado.LIQUIDADO:
        reintegro.fecha_liquidacion = ahora
    elif nuevo == ReintegroEstado.PAGADO:
        reintegro.fecha_pago = ahora

    db.flush()

    registrar_audit(
        db,
        usuario_id=usuario.id,
        reintegro_id=reintegro.id,
        accion="reintegro.estado.cambio",
        descripcion=f"Estado cambiado: {estado_previo.value} → {nuevo.value}",
        datos_previos={"estado": estado_previo.value},
        datos_nuevos={"estado": nuevo.value},
        commit=False,
    )

    db.commit()
    db.refresh(reintegro)
    return reintegro


def obtener_estadisticas_dashboard(db: Session) -> dict:
    """Calcula los KPIs del dashboard."""
    total = db.query(func.count(Reintegro.id)).scalar() or 0

    # Por estado
    por_estado_rows = db.query(Reintegro.estado, func.count(Reintegro.id)).group_by(Reintegro.estado).all()
    por_estado = {e.value: c for e, c in por_estado_rows}

    # Por tipo
    por_tipo_rows = db.query(Reintegro.tipo, func.count(Reintegro.id)).group_by(Reintegro.tipo).all()
    por_tipo = {t.value: c for t, c in por_tipo_rows}

    # Pendientes (no terminales)
    estados_pendientes = [
        ReintegroEstado.INGRESADO, ReintegroEstado.PENDIENTE_DOCUMENTACION,
        ReintegroEstado.EN_VALIDACION, ReintegroEstado.EN_AUDITORIA, ReintegroEstado.OBSERVADO,
    ]
    pendientes = db.query(func.count(Reintegro.id)).filter(Reintegro.estado.in_(estados_pendientes)).scalar() or 0

    # Vencidos SLA
    ahora = datetime.now(timezone.utc)
    vencidos = (
        db.query(func.count(Reintegro.id))
        .filter(
            and_(
                Reintegro.estado.in_(estados_pendientes),
                Reintegro.fecha_vencimiento_sla < ahora,
            )
        )
        .scalar() or 0
    )

    # Próximos a vencer (en las siguientes SLA_WARNING_HOURS)
    limite = ahora + timedelta(hours=settings.SLA_WARNING_HOURS)
    proximos = (
        db.query(func.count(Reintegro.id))
        .filter(
            and_(
                Reintegro.estado.in_(estados_pendientes),
                Reintegro.fecha_vencimiento_sla >= ahora,
                Reintegro.fecha_vencimiento_sla <= limite,
            )
        )
        .scalar() or 0
    )

    aprobados = por_estado.get(ReintegroEstado.APROBADO.value, 0)
    rechazados = por_estado.get(ReintegroEstado.RECHAZADO.value, 0)

    monto_liquidado = (
        db.query(func.coalesce(func.sum(Reintegro.monto_aprobado), 0))
        .filter(Reintegro.estado == ReintegroEstado.LIQUIDADO)
        .scalar() or 0
    )
    monto_pagado = (
        db.query(func.coalesce(func.sum(Reintegro.monto_aprobado), 0))
        .filter(Reintegro.estado == ReintegroEstado.PAGADO)
        .scalar() or 0
    )

    # Productividad por operador (top 10)
    op_rows = (
        db.query(User.id, User.nombre_completo, func.count(Reintegro.id).label("cant"))
        .join(Reintegro, Reintegro.creado_por_id == User.id)
        .group_by(User.id, User.nombre_completo)
        .order_by(func.count(Reintegro.id).desc())
        .limit(10)
        .all()
    )
    por_operador = [
        {"id": r.id, "nombre": r.nombre_completo, "cantidad": r.cant}
        for r in op_rows
    ]

    return {
        "casos_ingresados": total,
        "pendientes": pendientes,
        "vencidos_sla": vencidos,
        "proximos_vencer": proximos,
        "aprobados": aprobados,
        "rechazados": rechazados,
        "monto_total_liquidado": float(monto_liquidado),
        "monto_total_pagado": float(monto_pagado),
        "por_tipo": por_tipo,
        "por_estado": por_estado,
        "por_operador": por_operador,
    }
