"""ABM básico de Trabajadores y Siniestros."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.session import get_db
from app.models import Trabajador, Siniestro, User
from app.schemas.trabajador import (
    TrabajadorCreate, TrabajadorUpdate, TrabajadorOut,
    SiniestroCreate, SiniestroOut,
)
from app.api.deps import get_current_user


router = APIRouter(tags=["Trabajadores y Siniestros"])


# ---------- Trabajadores ----------

@router.get("/trabajadores", response_model=list[TrabajadorOut])
def listar_trabajadores(
    q: str | None = Query(None, description="Buscar por CUIL o nombre"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Trabajador)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Trabajador.cuil.like(like), Trabajador.nombre_completo.ilike(like)))
    return query.order_by(Trabajador.nombre_completo).limit(50).all()


@router.post("/trabajadores", response_model=TrabajadorOut, status_code=201)
def crear_trabajador(
    data: TrabajadorCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if db.query(Trabajador).filter(Trabajador.cuil == data.cuil).first():
        raise HTTPException(status_code=409, detail="CUIL ya registrado")
    t = Trabajador(**data.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.patch("/trabajadores/{trabajador_id}", response_model=TrabajadorOut)
def actualizar_trabajador(
    trabajador_id: int,
    data: TrabajadorUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    t = db.query(Trabajador).filter(Trabajador.id == trabajador_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


# ---------- Siniestros ----------

@router.get("/siniestros", response_model=list[SiniestroOut])
def listar_siniestros(
    q: str | None = Query(None, description="Buscar por número o CUIL"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Siniestro).join(Trabajador)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Siniestro.numero.like(like),
            Trabajador.cuil.like(like),
            Trabajador.nombre_completo.ilike(like),
        ))
    return query.order_by(Siniestro.creado_en.desc()).limit(50).all()


@router.post("/siniestros", response_model=SiniestroOut, status_code=201)
def crear_siniestro(
    data: SiniestroCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if db.query(Siniestro).filter(Siniestro.numero == data.numero).first():
        raise HTTPException(status_code=409, detail="Número de siniestro ya registrado")
    s = Siniestro(**data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/siniestros/{siniestro_id}", response_model=SiniestroOut)
def obtener_siniestro(
    siniestro_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    s = db.query(Siniestro).filter(Siniestro.id == siniestro_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Siniestro no encontrado")
    return s
