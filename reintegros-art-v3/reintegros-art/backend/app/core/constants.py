"""
Constantes del dominio: enums centralizados para roles, estados, tipos, etc.
"""
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    OPERADOR = "operador"
    AUDITOR_MEDICO = "auditor_medico"
    CONSULTA = "consulta"


class ReintegroTipo(str, Enum):
    TRASLADO_REMIS = "traslado_remis"
    TRASLADO_TRANSPORTE_PUBLICO = "traslado_transporte_publico"
    MEDICACION = "medicacion"
    ORTOPEDIA = "ortopedia"
    PRESTACION_MEDICA = "prestacion_medica"
    ALOJAMIENTO = "alojamiento"


class ReintegroEstado(str, Enum):
    INGRESADO = "ingresado"
    PENDIENTE_DOCUMENTACION = "pendiente_documentacion"
    EN_VALIDACION = "en_validacion"
    EN_AUDITORIA = "en_auditoria"
    OBSERVADO = "observado"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    LIQUIDADO = "liquidado"
    PAGADO = "pagado"


class TipoCuenta(str, Enum):
    CUENTA_BANCARIA_SUELDO = "cuenta_bancaria_sueldo"
    BILLETERA_VIRTUAL = "billetera_virtual"


class TipoDocumento(str, Enum):
    RECETA = "receta"
    TICKET = "ticket"
    FACTURA = "factura"
    ORDEN_MEDICA = "orden_medica"
    CBU = "cbu"
    DNI = "dni"
    CERTIFICADO = "certificado"
    COMPROBANTE = "comprobante"
    OTRO = "otro"


# Transiciones válidas del workflow
TRANSICIONES_PERMITIDAS = {
    ReintegroEstado.INGRESADO: [
        ReintegroEstado.PENDIENTE_DOCUMENTACION,
        ReintegroEstado.EN_VALIDACION,
        ReintegroEstado.RECHAZADO,
    ],
    ReintegroEstado.PENDIENTE_DOCUMENTACION: [
        ReintegroEstado.EN_VALIDACION,
        ReintegroEstado.RECHAZADO,
    ],
    ReintegroEstado.EN_VALIDACION: [
        ReintegroEstado.EN_AUDITORIA,
        ReintegroEstado.OBSERVADO,
        ReintegroEstado.APROBADO,
        ReintegroEstado.RECHAZADO,
    ],
    ReintegroEstado.EN_AUDITORIA: [
        ReintegroEstado.APROBADO,
        ReintegroEstado.OBSERVADO,
        ReintegroEstado.RECHAZADO,
    ],
    ReintegroEstado.OBSERVADO: [
        ReintegroEstado.EN_VALIDACION,
        ReintegroEstado.RECHAZADO,
    ],
    ReintegroEstado.APROBADO: [
        ReintegroEstado.LIQUIDADO,
    ],
    ReintegroEstado.LIQUIDADO: [
        ReintegroEstado.PAGADO,
    ],
    ReintegroEstado.RECHAZADO: [],
    ReintegroEstado.PAGADO: [],
}


# Permisos por rol y acción
PERMISOS = {
    UserRole.ADMIN: {"*"},
    UserRole.SUPERVISOR: {
        "users:read",
        "reintegro:read", "reintegro:create", "reintegro:update",
        "reintegro:approve", "reintegro:reject",
        "audit:read", "params:read", "params:write", "dashboard:read",
    },
    UserRole.OPERADOR: {
        "reintegro:read", "reintegro:create", "reintegro:update",
        "documento:upload", "dashboard:read",
    },
    UserRole.AUDITOR_MEDICO: {
        "reintegro:read", "reintegro:audit",
        "reintegro:approve", "reintegro:reject", "reintegro:observe",
        "audit:read", "dashboard:read",
    },
    UserRole.CONSULTA: {
        "reintegro:read", "dashboard:read",
    },
}


def tiene_permiso(role: UserRole, accion: str) -> bool:
    """Verifica si un rol tiene permiso para una acción."""
    permisos_rol = PERMISOS.get(role, set())
    return "*" in permisos_rol or accion in permisos_rol
