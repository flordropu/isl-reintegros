"""Configuración dinámica del sistema (parámetros)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any

from app.db.session import get_db
from app.models import Parametro, User
from app.api.deps import get_current_user
from app.core.constants import tiene_permiso
from app.services.reintegro_service import registrar_audit


router = APIRouter(prefix="/parametros", tags=["Parámetros"])


class ParametroIn(BaseModel):
    clave: str
    valor: Any
    descripcion: str | None = None
    categoria: str | None = None


class ParametroOut(BaseModel):
    clave: str
    valor: Any
    descripcion: str | None
    categoria: str | None


@router.get("", response_model=list[ParametroOut])
def listar_parametros(
    categoria: str | None = None,
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
):
    if not tiene_permiso(actual.role, "params:read"):
        raise HTTPException(status_code=403, detail="Sin permiso")
    q = db.query(Parametro)
    if categoria:
        q = q.filter(Parametro.categoria == categoria)
    return q.order_by(Parametro.categoria, Parametro.clave).all()


@router.put("/{clave}", response_model=ParametroOut)
def upsert_parametro(
    clave: str,
    data: ParametroIn,
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
):
    if not tiene_permiso(actual.role, "params:write"):
        raise HTTPException(status_code=403, detail="Sin permiso")
    if data.clave != clave:
        raise HTTPException(status_code=400, detail="Clave de URL no coincide con cuerpo")

    p = db.query(Parametro).filter(Parametro.clave == clave).first()
    if p:
        previo = p.valor
        p.valor = data.valor
        p.descripcion = data.descripcion or p.descripcion
        p.categoria = data.categoria or p.categoria
        p.actualizado_por_id = actual.id
        accion_desc = f"Modificación parámetro {clave}"
        previos = {"valor": previo}
    else:
        p = Parametro(**data.model_dump(), actualizado_por_id=actual.id)
        db.add(p)
        accion_desc = f"Alta parámetro {clave}"
        previos = None

    db.commit()
    db.refresh(p)
    registrar_audit(
        db, usuario_id=actual.id, accion="parametro.update",
        descripcion=accion_desc,
        datos_previos=previos, datos_nuevos={"valor": data.valor},
    )
    return p
