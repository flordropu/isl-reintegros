"""
Modelos SQLAlchemy del dominio.

Entidades:
- User: usuarios del sistema (con roles)
- Trabajador: persona que recibe el reintegro
- Siniestro: caso al que se asocia el reintegro
- Reintegro: solicitud central del sistema
- Documento: archivos adjuntos a un reintegro
- AuditLog: trazabilidad de acciones
- Parametro: configuración dinámica (valor/km, topes, SLA, etc.)
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, JSON,
)
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.core.constants import (
    UserRole, ReintegroTipo, ReintegroEstado, TipoCuenta, TipoDocumento,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    nombre_completo = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.OPERADOR)
    activo = Column(Boolean, default=True, nullable=False)
    bloqueado = Column(Boolean, default=False, nullable=False)
    region = Column(String, nullable=True)

    creado_en = Column(DateTime, default=utcnow, nullable=False)
    actualizado_en = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    ultimo_login = Column(DateTime, nullable=True)

    # Relaciones
    reintegros_creados = relationship("Reintegro", foreign_keys="Reintegro.creado_por_id", back_populates="creado_por")
    reintegros_asignados = relationship("Reintegro", foreign_keys="Reintegro.asignado_a_id", back_populates="asignado_a")
    audit_logs = relationship("AuditLog", back_populates="usuario")


class Trabajador(Base):
    __tablename__ = "trabajadores"

    id = Column(Integer, primary_key=True, index=True)
    cuil = Column(String, unique=True, nullable=False, index=True)
    nombre_completo = Column(String, nullable=False)
    dni = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    telefono_verificado = Column(Boolean, default=False, nullable=False)
    cbu = Column(String, nullable=True)
    alias_cbu = Column(String, nullable=True)
    tipo_cuenta = Column(SQLEnum(TipoCuenta), nullable=True)
    cbu_verificado = Column(Boolean, default=False, nullable=False)

    creado_en = Column(DateTime, default=utcnow, nullable=False)
    actualizado_en = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    siniestros = relationship("Siniestro", back_populates="trabajador")


class Siniestro(Base):
    __tablename__ = "siniestros"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, unique=True, nullable=False, index=True)
    trabajador_id = Column(Integer, ForeignKey("trabajadores.id"), nullable=False)
    fecha_siniestro = Column(DateTime, nullable=True)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True, nullable=False)

    creado_en = Column(DateTime, default=utcnow, nullable=False)

    trabajador = relationship("Trabajador", back_populates="siniestros")
    reintegros = relationship("Reintegro", back_populates="siniestro")


class Reintegro(Base):
    __tablename__ = "reintegros"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False, index=True)  # ej: RT-2025-0421
    siniestro_id = Column(Integer, ForeignKey("siniestros.id"), nullable=False)
    tipo = Column(SQLEnum(ReintegroTipo), nullable=False)
    estado = Column(SQLEnum(ReintegroEstado), default=ReintegroEstado.INGRESADO, nullable=False, index=True)

    # Montos
    monto_solicitado = Column(Float, nullable=True)
    monto_aprobado = Column(Float, nullable=True)
    monto_total_ticket = Column(Float, nullable=True)

    # SLA
    fecha_vencimiento_sla = Column(DateTime, nullable=True, index=True)

    # Datos específicos por tipo (JSON flexible)
    # Para traslados: {origen, destino, cantidad_viajes, ida_y_vuelta, fechas_turnos, distancia_km, valor_km}
    # Para medicación: {medicamentos: [{droga, presentacion, cantidad, valor_unitario}]}
    # Para ortopedia: {tipo_ortesis, descripcion}
    # Para prestaciones: {concepto, descripcion}
    datos_especificos = Column(JSON, nullable=True, default=dict)

    # Observaciones / motivos
    observaciones = Column(Text, nullable=True)
    motivo_rechazo = Column(Text, nullable=True)

    # Asignación
    creado_por_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asignado_a_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Datos de pago capturados al momento (snapshot, por si cambian los del trabajador)
    cbu_pago = Column(String, nullable=True)
    alias_pago = Column(String, nullable=True)
    tipo_cuenta_pago = Column(SQLEnum(TipoCuenta), nullable=True)

    # Liquidación / pago
    fecha_aprobacion = Column(DateTime, nullable=True)
    fecha_liquidacion = Column(DateTime, nullable=True)
    fecha_pago = Column(DateTime, nullable=True)

    creado_en = Column(DateTime, default=utcnow, nullable=False, index=True)
    actualizado_en = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Relaciones
    siniestro = relationship("Siniestro", back_populates="reintegros")
    creado_por = relationship("User", foreign_keys=[creado_por_id], back_populates="reintegros_creados")
    asignado_a = relationship("User", foreign_keys=[asignado_a_id], back_populates="reintegros_asignados")
    documentos = relationship("Documento", back_populates="reintegro", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="reintegro")


class Documento(Base):
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True, index=True)
    reintegro_id = Column(Integer, ForeignKey("reintegros.id"), nullable=False)
    tipo = Column(SQLEnum(TipoDocumento), nullable=False)
    nombre_original = Column(String, nullable=False)
    nombre_archivo = Column(String, nullable=False)  # nombre en disco (UUID)
    ruta = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    tamanio_bytes = Column(Integer, nullable=True)

    # Resultado de procesamiento PDF/OCR
    texto_extraido = Column(Text, nullable=True)
    metodo_extraccion = Column(String, nullable=True)  # 'pdfplumber', 'ocr', 'none'
    datos_extraidos = Column(JSON, nullable=True)  # estructurados (montos, fechas, etc.)
    procesado = Column(Boolean, default=False, nullable=False)

    subido_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    creado_en = Column(DateTime, default=utcnow, nullable=False)

    reintegro = relationship("Reintegro", back_populates="documentos")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reintegro_id = Column(Integer, ForeignKey("reintegros.id"), nullable=True)
    accion = Column(String, nullable=False, index=True)  # ej: "reintegro.create", "estado.cambio"
    descripcion = Column(Text, nullable=True)
    datos_previos = Column(JSON, nullable=True)
    datos_nuevos = Column(JSON, nullable=True)
    ip_origen = Column(String, nullable=True)
    creado_en = Column(DateTime, default=utcnow, nullable=False, index=True)

    usuario = relationship("User", back_populates="audit_logs")
    reintegro = relationship("Reintegro", back_populates="audit_logs")


class Parametro(Base):
    """
    Configuración dinámica del sistema.
    Ejemplos de claves:
    - 'valor_km_remis' (float)
    - 'tope_traslado_mensual' (float)
    - 'sla_default_dias' (int)
    - 'motivos_rechazo' (json/list)
    """
    __tablename__ = "parametros"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String, unique=True, nullable=False, index=True)
    valor = Column(JSON, nullable=False)
    descripcion = Column(Text, nullable=True)
    categoria = Column(String, nullable=True, index=True)
    actualizado_en = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    actualizado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
