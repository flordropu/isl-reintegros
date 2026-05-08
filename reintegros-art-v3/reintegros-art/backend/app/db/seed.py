"""
Seed inicial: crea usuario admin, parámetros base y datos demo.

Se ejecuta una sola vez al arrancar la app si la DB está vacía.
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine, Base
from app.models import (
    User, Trabajador, Siniestro, Reintegro, Parametro,
)
from app.core.security import hash_password
from app.core.constants import (
    UserRole, ReintegroTipo, ReintegroEstado, TipoCuenta,
)
from app.services.reintegro_service import generar_codigo_reintegro, calcular_vencimiento_sla


def crear_tablas():
    Base.metadata.create_all(bind=engine)


def seed():
    crear_tablas()
    db: Session = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return  # ya seedeado

        # ---- Usuarios ----
        admin = User(
            email="admin@isl.com.ar",
            nombre_completo="Administrador",
            hashed_password=hash_password("admin1234"),
            role=UserRole.ADMIN,
        )
        supervisor = User(
            email="supervisor@isl.com.ar",
            nombre_completo="María Reyes",
            hashed_password=hash_password("super1234"),
            role=UserRole.SUPERVISOR,
        )
        operador = User(
            email="operador@isl.com.ar",
            nombre_completo="Martín Reyes",
            hashed_password=hash_password("oper1234"),
            role=UserRole.OPERADOR,
        )
        auditor = User(
            email="auditor@isl.com.ar",
            nombre_completo="Dra. Lucía Pereyra",
            hashed_password=hash_password("audit1234"),
            role=UserRole.AUDITOR_MEDICO,
        )
        db.add_all([admin, supervisor, operador, auditor])
        db.commit()

        # ---- Parámetros base ----
        params = [
            Parametro(clave="valor_km_remis", valor=243.0, descripcion="Valor por km en remis", categoria="traslados"),
            Parametro(clave="valor_km_combustible", valor=120.0, descripcion="Valor por km en combustible", categoria="traslados"),
            Parametro(clave="tope_traslado_mensual", valor=85000.0, descripcion="Tope mensual de traslados", categoria="topes"),
            Parametro(clave="tope_medicacion_mensual", valor=50000.0, descripcion="Tope mensual de medicación", categoria="topes"),
            Parametro(clave="sla_default_dias", valor=5, descripcion="SLA por defecto en días", categoria="sla"),
            Parametro(clave="motivos_rechazo", valor=[
                "Documentación insuficiente",
                "Importe excede el tope",
                "Fecha fuera del período cubierto",
                "Comprobante ilegible",
                "No corresponde al tipo de prestación",
            ], descripcion="Catálogo de motivos de rechazo", categoria="catalogos"),
        ]
        db.add_all(params)
        db.commit()

        # ---- Trabajadores demo ----
        trabajadores = [
            Trabajador(
                cuil="20-31456789-3", nombre_completo="Pérez, Juan Carlos",
                dni="31456789", telefono="+54 11 5567-2389", telefono_verificado=True,
                alias_cbu="PEREZ.JUAN.MP", tipo_cuenta=TipoCuenta.BILLETERA_VIRTUAL, cbu_verificado=True,
            ),
            Trabajador(
                cuil="27-28934512-7", nombre_completo="García, María Elena",
                dni="28934512", telefono="+54 11 4421-9988", telefono_verificado=True,
                cbu="0170099120000031245678", tipo_cuenta=TipoCuenta.CUENTA_BANCARIA_SUELDO, cbu_verificado=True,
            ),
            Trabajador(
                cuil="20-35671234-1", nombre_completo="Rodríguez, Sebastián",
                dni="35671234", telefono="+54 11 6789-2345", telefono_verificado=False,
                alias_cbu="SEBA.ROD.PESOS", tipo_cuenta=TipoCuenta.BILLETERA_VIRTUAL,
            ),
            Trabajador(
                cuil="27-30214567-9", nombre_completo="López, Carolina",
                dni="30214567", telefono="+54 11 3456-7890", telefono_verificado=True,
                cbu="0070088120000045678901", tipo_cuenta=TipoCuenta.CUENTA_BANCARIA_SUELDO, cbu_verificado=True,
            ),
        ]
        db.add_all(trabajadores)
        db.commit()

        # ---- Siniestros demo ----
        siniestros = [
            Siniestro(numero="4421", trabajador_id=trabajadores[0].id, descripcion="Lumbalgia laboral"),
            Siniestro(numero="4398", trabajador_id=trabajadores[1].id, descripcion="Esguince de tobillo"),
            Siniestro(numero="4456", trabajador_id=trabajadores[2].id, descripcion="Cervicalgia"),
            Siniestro(numero="4471", trabajador_id=trabajadores[3].id, descripcion="Fractura de muñeca"),
        ]
        db.add_all(siniestros)
        db.commit()

        # ---- Reintegros demo ----
        ahora = datetime.now(timezone.utc)
        reintegros_data = [
            dict(
                siniestro_id=siniestros[0].id, tipo=ReintegroTipo.TRASLADO_REMIS,
                estado=ReintegroEstado.EN_VALIDACION,
                monto_solicitado=48200.0, monto_total_ticket=48200.0,
                fecha_vencimiento_sla=ahora - timedelta(days=2),
                datos_especificos={
                    "origen": "Av. Córdoba 1234, CABA",
                    "destino": "Hospital Italiano, Perón 4190",
                    "cantidad_viajes": 8, "ida_y_vuelta": True,
                    "distancia_km": 12.4, "valor_km": 243,
                    "fechas_turnos": ["2025-10-02", "2025-10-04", "2025-10-07", "2025-10-09"],
                },
                cbu_pago=None, alias_pago="PEREZ.JUAN.MP", tipo_cuenta_pago=TipoCuenta.BILLETERA_VIRTUAL,
                creado_por_id=operador.id, asignado_a_id=operador.id,
            ),
            dict(
                siniestro_id=siniestros[1].id, tipo=ReintegroTipo.MEDICACION,
                estado=ReintegroEstado.EN_AUDITORIA,
                monto_solicitado=15840.0, monto_total_ticket=15840.0,
                fecha_vencimiento_sla=ahora - timedelta(days=1),
                datos_especificos={
                    "medicamentos": [
                        {"droga": "Ibuprofeno 600mg", "presentacion": "comprimidos", "cantidad": 30, "valor_unitario": 280.0},
                        {"droga": "Diclofenac 75mg gel", "presentacion": "tubo 60g", "cantidad": 2, "valor_unitario": 3720.0},
                    ],
                },
                cbu_pago="0170099120000031245678", tipo_cuenta_pago=TipoCuenta.CUENTA_BANCARIA_SUELDO,
                creado_por_id=operador.id, asignado_a_id=auditor.id,
            ),
            dict(
                siniestro_id=siniestros[2].id, tipo=ReintegroTipo.PRESTACION_MEDICA,
                estado=ReintegroEstado.OBSERVADO,
                monto_solicitado=92500.0, monto_total_ticket=92500.0,
                fecha_vencimiento_sla=ahora + timedelta(hours=12),
                datos_especificos={"concepto": "Sesiones de kinesiología (10 sesiones)"},
                observaciones="Falta órden médica original",
                creado_por_id=operador.id, asignado_a_id=operador.id,
            ),
            dict(
                siniestro_id=siniestros[3].id, tipo=ReintegroTipo.ORTOPEDIA,
                estado=ReintegroEstado.PENDIENTE_DOCUMENTACION,
                monto_solicitado=24300.0,
                fecha_vencimiento_sla=ahora + timedelta(hours=36),
                datos_especificos={"tipo_ortesis": "Bota Walker"},
                creado_por_id=operador.id, asignado_a_id=operador.id,
            ),
            dict(
                siniestro_id=siniestros[0].id, tipo=ReintegroTipo.TRASLADO_REMIS,
                estado=ReintegroEstado.APROBADO, fecha_aprobacion=ahora - timedelta(days=4),
                monto_solicitado=31700.0, monto_aprobado=31700.0, monto_total_ticket=31700.0,
                fecha_vencimiento_sla=ahora + timedelta(days=4),
                datos_especificos={
                    "origen": "Av. Córdoba 1234, CABA", "destino": "Centro de rehabilitación FLENI",
                    "cantidad_viajes": 5, "ida_y_vuelta": True, "distancia_km": 8.6, "valor_km": 243,
                },
                creado_por_id=operador.id, asignado_a_id=supervisor.id,
            ),
            dict(
                siniestro_id=siniestros[1].id, tipo=ReintegroTipo.MEDICACION,
                estado=ReintegroEstado.LIQUIDADO, fecha_liquidacion=ahora - timedelta(days=1),
                monto_solicitado=8450.0, monto_aprobado=8450.0, monto_total_ticket=8450.0,
                fecha_vencimiento_sla=ahora + timedelta(days=5),
                datos_especificos={
                    "medicamentos": [{"droga": "Paracetamol 500mg", "presentacion": "comprimidos", "cantidad": 20, "valor_unitario": 422.5}],
                },
                creado_por_id=operador.id, asignado_a_id=auditor.id,
            ),
        ]

        for data in reintegros_data:
            data["codigo"] = generar_codigo_reintegro(db)
            r = Reintegro(**data)
            db.add(r)
            db.flush()  # para que el siguiente codigo sea correlativo
        db.commit()

        print("[seed] Datos demo creados exitosamente")
        print("[seed] Usuarios:")
        print("       admin@isl.com.ar / admin1234   (Admin)")
        print("       supervisor@isl.com.ar / super1234   (Supervisor)")
        print("       operador@isl.com.ar / oper1234   (Operador)")
        print("       auditor@isl.com.ar / audit1234   (Auditor)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
