"""
Endpoints del módulo de Reintegros.

Operaciones:
- Listar con filtros (estado, tipo, búsqueda, paginación)
- Crear (asociado a siniestro)
- Detalle
- Actualizar
- Cambiar estado (con validación de transiciones)
- Upload de documentos (PDF/imagen) con extracción automática
- Análisis de PDF antes de crear (preview)
"""
import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc
from datetime import datetime, timezone

from app.db.session import get_db
from app.models import Reintegro, Siniestro, Documento, User
from app.schemas.reintegro import (
    ReintegroCreate, ReintegroUpdate, ReintegroOut, ReintegroDetalleOut,
    CambioEstadoRequest, DocumentoOut, ExtraccionPDFOut, DashboardStats,
)
from app.core.constants import ReintegroEstado, ReintegroTipo, TipoDocumento, tiene_permiso
from app.core.config import settings
from app.api.deps import get_current_user
from app.services.reintegro_service import (
    generar_codigo_reintegro, calcular_vencimiento_sla,
    cambiar_estado, registrar_audit, obtener_estadisticas_dashboard,
)
from app.services.pdf_extractor import extraer_pdf
from app.services.ai_extractor import extraer_con_ia


router = APIRouter(prefix="/reintegros", tags=["Reintegros"])


def _check_permission(user: User, accion: str):
    if not tiene_permiso(user.role, accion):
        raise HTTPException(status_code=403, detail=f"Sin permiso: {accion}")


def _validar_upload(file: UploadFile) -> None:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida. Permitidas: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )


def _guardar_archivo(file: UploadFile) -> tuple[str, str, int]:
    """Guarda archivo en UPLOAD_DIR. Retorna (nombre_disco, ruta_completa, tamanio)."""
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "").suffix.lower()
    nombre_disco = f"{uuid.uuid4().hex}{ext}"
    ruta = os.path.join(settings.UPLOAD_DIR, nombre_disco)
    with open(ruta, "wb") as buf:
        shutil.copyfileobj(file.file, buf)
    tamanio = os.path.getsize(ruta)
    if tamanio > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        os.remove(ruta)
        raise HTTPException(status_code=413, detail="Archivo demasiado grande")
    return nombre_disco, ruta, tamanio


# ---------- Listado / búsqueda ----------

@router.get("", response_model=dict)
def listar_reintegros(
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
    estado: ReintegroEstado | None = None,
    tipo: ReintegroTipo | None = None,
    sla: str | None = Query(None, description="Filtrar por SLA: vencido, proximo, en_termino"),
    mios: bool = False,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    _check_permission(actual, "reintegro:read")

    query = db.query(Reintegro).options(
        joinedload(Reintegro.siniestro).joinedload(Siniestro.trabajador),
    )

    if estado:
        query = query.filter(Reintegro.estado == estado)
    if tipo:
        query = query.filter(Reintegro.tipo == tipo)
    if mios:
        query = query.filter(or_(
            Reintegro.creado_por_id == actual.id,
            Reintegro.asignado_a_id == actual.id,
        ))
    if q:
        # Búsqueda accent-insensitive: usamos la función SQLite `unaccent`
        # registrada en app/db/session.py para comparar sin tildes en ambos
        # lados (columna y query).
        import unicodedata
        def strip_accents(s: str) -> str:
            return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
        q_norm = strip_accents(q).lower()
        like_norm = f"%{q_norm}%"
        like_orig = f"%{q}%"
        from app.models import Trabajador as Trab
        from sqlalchemy import func as sa_func
        query = query.join(Reintegro.siniestro).join(Siniestro.trabajador).filter(or_(
            Reintegro.codigo.ilike(like_orig),
            Siniestro.numero.ilike(like_orig),
            Trab.cuil.ilike(like_orig),
            sa_func.lower(sa_func.unaccent(Trab.nombre_completo)).like(like_norm),
        ))

    if sla:
        ahora = datetime.now(timezone.utc)
        if sla == "vencido":
            query = query.filter(Reintegro.fecha_vencimiento_sla < ahora)
        elif sla == "proximo":
            from datetime import timedelta
            limite = ahora + timedelta(hours=settings.SLA_WARNING_HOURS)
            query = query.filter(and_(
                Reintegro.fecha_vencimiento_sla >= ahora,
                Reintegro.fecha_vencimiento_sla <= limite,
            ))
        elif sla == "en_termino":
            query = query.filter(Reintegro.fecha_vencimiento_sla >= ahora)

    total = query.count()
    items = (
        query.order_by(desc(Reintegro.creado_en))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # serializar agregando datos de trabajador para la lista
    resultados = []
    for r in items:
        d = ReintegroOut.model_validate(r).model_dump()
        d["trabajador_nombre"] = r.siniestro.trabajador.nombre_completo if r.siniestro and r.siniestro.trabajador else None
        d["trabajador_cuil"] = r.siniestro.trabajador.cuil if r.siniestro and r.siniestro.trabajador else None
        d["siniestro_numero"] = r.siniestro.numero if r.siniestro else None
        resultados.append(d)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": resultados,
    }


# ---------- Crear ----------

@router.post("", response_model=ReintegroDetalleOut, status_code=201)
def crear_reintegro(
    data: ReintegroCreate,
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
):
    _check_permission(actual, "reintegro:create")

    siniestro = db.query(Siniestro).filter(Siniestro.id == data.siniestro_id).first()
    if not siniestro:
        raise HTTPException(status_code=404, detail="Siniestro no encontrado")

    r = Reintegro(
        codigo=generar_codigo_reintegro(db),
        siniestro_id=data.siniestro_id,
        tipo=data.tipo,
        estado=ReintegroEstado.INGRESADO,
        monto_solicitado=data.monto_solicitado,
        monto_total_ticket=data.monto_total_ticket,
        datos_especificos=data.datos_especificos or {},
        observaciones=data.observaciones,
        cbu_pago=data.cbu_pago,
        alias_pago=data.alias_pago,
        tipo_cuenta_pago=data.tipo_cuenta_pago,
        creado_por_id=actual.id,
        asignado_a_id=actual.id,
        fecha_vencimiento_sla=calcular_vencimiento_sla(),
    )
    db.add(r)
    db.commit()
    db.refresh(r)

    registrar_audit(
        db, usuario_id=actual.id, reintegro_id=r.id,
        accion="reintegro.create",
        descripcion=f"Alta de reintegro {r.codigo} ({r.tipo.value})",
    )
    return r


# ---------- Detalle / update / estado ----------

@router.get("/{reintegro_id}", response_model=ReintegroDetalleOut)
def obtener_reintegro(
    reintegro_id: int,
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
):
    _check_permission(actual, "reintegro:read")
    r = (
        db.query(Reintegro)
        .options(
            joinedload(Reintegro.siniestro).joinedload(Siniestro.trabajador),
            joinedload(Reintegro.documentos),
        )
        .filter(Reintegro.id == reintegro_id)
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="Reintegro no encontrado")
    return r


@router.patch("/{reintegro_id}", response_model=ReintegroDetalleOut)
def actualizar_reintegro(
    reintegro_id: int,
    data: ReintegroUpdate,
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
):
    _check_permission(actual, "reintegro:update")
    r = db.query(Reintegro).filter(Reintegro.id == reintegro_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reintegro no encontrado")

    cambios = data.model_dump(exclude_unset=True)
    previos = {k: getattr(r, k) for k in cambios.keys() if hasattr(r, k)}

    for k, v in cambios.items():
        setattr(r, k, v)

    db.commit()
    db.refresh(r)

    registrar_audit(
        db, usuario_id=actual.id, reintegro_id=r.id,
        accion="reintegro.update", descripcion=f"Modificación reintegro {r.codigo}",
        datos_previos={k: (v.value if hasattr(v, "value") else v) for k, v in previos.items()},
        datos_nuevos={k: (v.value if hasattr(v, "value") else v) for k, v in cambios.items()},
    )
    return r


@router.post("/{reintegro_id}/estado", response_model=ReintegroDetalleOut)
def cambiar_estado_endpoint(
    reintegro_id: int,
    data: CambioEstadoRequest,
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
):
    # Validación de permisos según destino
    accion_requerida = {
        ReintegroEstado.APROBADO: "reintegro:approve",
        ReintegroEstado.RECHAZADO: "reintegro:reject",
        ReintegroEstado.OBSERVADO: "reintegro:observe",
    }.get(data.nuevo_estado, "reintegro:update")
    _check_permission(actual, accion_requerida)

    r = db.query(Reintegro).filter(Reintegro.id == reintegro_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reintegro no encontrado")

    try:
        r = cambiar_estado(
            db, r, data.nuevo_estado, actual,
            observaciones=data.observaciones,
            motivo_rechazo=data.motivo_rechazo,
            monto_aprobado=data.monto_aprobado,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return r


# ---------- Documentos ----------

@router.post("/{reintegro_id}/documentos", response_model=DocumentoOut, status_code=201)
def subir_documento(
    reintegro_id: int,
    file: UploadFile = File(...),
    tipo: TipoDocumento = Form(TipoDocumento.OTRO),
    procesar: bool = Form(True, description="Si True, intenta extraer texto/datos del PDF"),
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
):
    _check_permission(actual, "reintegro:update")

    r = db.query(Reintegro).filter(Reintegro.id == reintegro_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reintegro no encontrado")

    _validar_upload(file)
    nombre_disco, ruta, tamanio = _guardar_archivo(file)

    texto, metodo, datos_extra = "", None, None
    if procesar and ruta.lower().endswith(".pdf"):
        try:
            res = extraer_pdf(ruta)
            texto = res["texto_extraido"]
            metodo = res["metodo"]
            datos_extra = res["datos_estructurados"]
        except Exception:
            metodo = "error"

    doc = Documento(
        reintegro_id=r.id,
        tipo=tipo,
        nombre_original=file.filename or nombre_disco,
        nombre_archivo=nombre_disco,
        ruta=ruta,
        mime_type=file.content_type,
        tamanio_bytes=tamanio,
        texto_extraido=texto[:50000] if texto else None,  # tope para no inflar la DB
        metodo_extraccion=metodo,
        datos_extraidos=datos_extra,
        procesado=bool(metodo and metodo not in (None, "error")),
        subido_por_id=actual.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    registrar_audit(
        db, usuario_id=actual.id, reintegro_id=r.id,
        accion="documento.upload",
        descripcion=f"Adjuntó {doc.nombre_original} ({tipo.value})",
    )
    return doc


@router.post("/analizar-pdf", response_model=ExtraccionPDFOut)
def analizar_pdf_preview(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
):
    """
    Endpoint para analizar un PDF *antes* de crear el reintegro.
    Permite que el frontend pre-rellene el formulario con los datos detectados.
    """
    _check_permission(actual, "reintegro:create")
    _validar_upload(file)
    nombre_disco, ruta, _ = _guardar_archivo(file)

    try:
        res = extraer_pdf(ruta)
        # Capa IA opcional (deshabilitada por defecto)
        ia_data = extraer_con_ia(res["texto_extraido"])
        if ia_data:
            res["datos_estructurados"] = {**res["datos_estructurados"], **ia_data}
    finally:
        # archivo de preview lo borramos para no llenar el disco
        try:
            os.remove(ruta)
        except OSError:
            pass

    return ExtraccionPDFOut(
        metodo=res["metodo"],
        texto_extraido=res["texto_extraido"][:5000],
        paginas=res["paginas"],
        datos_estructurados=res["datos_estructurados"],
    )


# ---------- Dashboard ----------

@router.get("/stats/dashboard", response_model=DashboardStats)
def stats_dashboard(
    db: Session = Depends(get_db),
    actual: User = Depends(get_current_user),
):
    _check_permission(actual, "dashboard:read")
    return obtener_estadisticas_dashboard(db)
