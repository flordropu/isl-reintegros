"""Endpoint de consulta de audit logs."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.db.session import get_db
from app.models import AuditLog, User
from app.api.deps import get_current_user
from app.core.constants import tiene_permiso
from fastapi import HTTPException


router = APIRouter(prefix="/audit", tags=["Auditoría"])


@router.get("")
def listar_audit(
    reintegro_id: int | None = None,
    usuario_id: int | None = None,
    accion: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
):
    if not tiene_permiso(actual.role, "audit:read"):
        raise HTTPException(status_code=403, detail="Sin permiso")

    q = db.query(AuditLog).options(joinedload(AuditLog.usuario))
    if reintegro_id:
        q = q.filter(AuditLog.reintegro_id == reintegro_id)
    if usuario_id:
        q = q.filter(AuditLog.usuario_id == usuario_id)
    if accion:
        q = q.filter(AuditLog.accion.like(f"{accion}%"))

    total = q.count()
    rows = q.order_by(desc(AuditLog.creado_en)).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": r.id,
                "accion": r.accion,
                "descripcion": r.descripcion,
                "usuario": r.usuario.nombre_completo if r.usuario else None,
                "usuario_email": r.usuario.email if r.usuario else None,
                "reintegro_id": r.reintegro_id,
                "datos_previos": r.datos_previos,
                "datos_nuevos": r.datos_nuevos,
                "creado_en": r.creado_en,
            }
            for r in rows
        ],
    }
