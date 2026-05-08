# Sistema Integral de Gestión de Reintegros ART — Backend

API REST en FastAPI para la gestión integral de reintegros ART.

> **Estado del proyecto**: MVP funcional del backend. El frontend (React) se construye en una próxima iteración.

## Stack

- **Python 3.10+** con FastAPI
- **SQLAlchemy 2.0** + SQLite (preparado para migrar a PostgreSQL)
- **JWT** para autenticación (python-jose)
- **bcrypt** para hashing de contraseñas (passlib)
- **pdfplumber** + **Tesseract OCR** para extracción de datos de PDFs
- Capa de IA preparada (apagada) para auto-completado con la API de Anthropic

## Estructura del proyecto

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py              # Dependencies (auth, permisos)
│   │   └── v1/
│   │       ├── auth.py          # Login, /me
│   │       ├── users.py         # ABM usuarios
│   │       ├── trabajadores.py  # Trabajadores y siniestros
│   │       ├── reintegros.py    # Núcleo: CRUD, estados, upload PDF
│   │       ├── audit.py         # Consulta de audit logs
│   │       ├── parametros.py    # Parametrización dinámica
│   │       └── router.py        # Agregador
│   ├── core/
│   │   ├── config.py            # Settings con Pydantic
│   │   ├── security.py          # JWT + hashing
│   │   └── constants.py         # Roles, estados, permisos, transiciones
│   ├── db/
│   │   ├── session.py           # Engine, SessionLocal, Base
│   │   └── seed.py              # Datos demo iniciales
│   ├── models/
│   │   └── models.py            # User, Trabajador, Siniestro, Reintegro, Documento, AuditLog, Parametro
│   ├── schemas/
│   │   ├── user.py
│   │   ├── trabajador.py
│   │   └── reintegro.py
│   ├── services/
│   │   ├── reintegro_service.py # Lógica de negocio: códigos, SLA, transiciones, dashboard
│   │   ├── pdf_extractor.py     # Extracción de texto + OCR + parsing heurístico
│   │   └── ai_extractor.py      # Capa IA (apagada por defecto)
│   └── main.py                  # Entry point FastAPI
├── uploads/                     # Documentos subidos (creado en runtime)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Setup local

### 1) Pre-requisitos del sistema

**Python 3.10+** y, opcionalmente para OCR de PDFs escaneados:

- **Tesseract OCR** con paquete de español
- **Poppler** (lo usa pdf2image para rasterizar PDFs)

#### Ubuntu / Debian
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-spa poppler-utils
```

#### macOS (Homebrew)
```bash
brew install tesseract tesseract-lang poppler
```

#### Windows
- Tesseract: instalador desde https://github.com/UB-Mannheim/tesseract/wiki (marcá Spanish)
- Poppler: bajá el zip de https://github.com/oschwartz10612/poppler-windows/releases y agregalo al PATH

> Si no instalás Tesseract/Poppler la app igual funciona: solo se desactiva el fallback OCR, y se usa pdfplumber (que cubre la mayoría de los PDFs con texto). El OCR es solo para PDFs escaneados/imagen.

### 2) Instalar dependencias Python

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 3) Configurar variables de entorno

```bash
cp .env.example .env
```

Editá `.env` y, **muy importante**, cambiá el `SECRET_KEY` por un string largo y aleatorio para producción.

### 4) Levantar el server

```bash
uvicorn app.main:app --reload --port 8000
```

La primera vez se crea la DB SQLite y se cargan datos demo automáticamente.

- API: http://localhost:8000
- Docs interactivas (Swagger): http://localhost:8000/docs
- Docs alternativas (ReDoc): http://localhost:8000/redoc

## Usuarios de prueba

| Email | Password | Rol |
|-------|----------|-----|
| `admin@isl.com.ar` | `admin1234` | Admin |
| `supervisor@isl.com.ar` | `super1234` | Supervisor |
| `operador@isl.com.ar` | `oper1234` | Operador |
| `auditor@isl.com.ar` | `audit1234` | Auditor médico |

> En `/docs`, hacé click en **Authorize** (arriba a la derecha), poné el email como `username` y la password. Ahí ya quedás autenticado para probar todos los endpoints.

## Cómo probar la API rápido

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"operador@isl.com.ar","password":"oper1234"}'
```

Devuelve un `access_token`. Usalo en los siguientes requests como header:
```
Authorization: Bearer <token>
```

### Dashboard
```bash
curl http://localhost:8000/api/v1/reintegros/stats/dashboard \
  -H "Authorization: Bearer <token>"
```

### Listado de reintegros
```bash
curl "http://localhost:8000/api/v1/reintegros?page_size=10&sla=vencido" \
  -H "Authorization: Bearer <token>"
```

### Análisis de PDF (preview, antes de crear el reintegro)
```bash
curl -X POST http://localhost:8000/api/v1/reintegros/analizar-pdf \
  -H "Authorization: Bearer <token>" \
  -F "file=@/ruta/a/comprobante.pdf"
```

Devuelve el texto extraído + datos estructurados detectados (tipo de reintegro, montos, CUIL, CBU, fechas) que el frontend va a usar para auto-completar el formulario.

### Cambiar estado de un reintegro
```bash
curl -X POST http://localhost:8000/api/v1/reintegros/1/estado \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"nuevo_estado":"aprobado","monto_aprobado":48200}'
```

## Endpoints principales

| Método | Path | Descripción |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Login (devuelve JWT) |
| GET | `/api/v1/auth/me` | Datos del usuario actual |
| GET, POST, PATCH, DELETE | `/api/v1/users` | ABM usuarios (admin) |
| GET, POST, PATCH | `/api/v1/trabajadores` | Trabajadores |
| GET, POST | `/api/v1/siniestros` | Siniestros |
| GET | `/api/v1/reintegros` | Listado con filtros (estado, tipo, SLA, búsqueda, paginación) |
| POST | `/api/v1/reintegros` | Crear reintegro |
| GET | `/api/v1/reintegros/{id}` | Detalle (incluye documentos y siniestro) |
| PATCH | `/api/v1/reintegros/{id}` | Actualizar |
| POST | `/api/v1/reintegros/{id}/estado` | Cambiar estado del workflow |
| POST | `/api/v1/reintegros/{id}/documentos` | Subir documento (con extracción automática) |
| POST | `/api/v1/reintegros/analizar-pdf` | **Preview**: analizar PDF antes de crear |
| GET | `/api/v1/reintegros/stats/dashboard` | KPIs del dashboard |
| GET | `/api/v1/audit` | Logs de auditoría |
| GET, PUT | `/api/v1/parametros` | Configuración dinámica |

La documentación completa con todos los schemas y campos está en `/docs`.

## Workflow de estados

```
ingresado → pendiente_documentacion → en_validacion → en_auditoria → aprobado → liquidado → pagado
                                            ↓               ↓
                                       observado ←──────────┤
                                                            ↓
                                                       rechazado
```

Las transiciones permitidas están definidas en `app/core/constants.py::TRANSICIONES_PERMITIDAS`. Si intentás un cambio de estado no permitido, la API devuelve 400 con el mensaje correspondiente.

## Permisos por rol

| Acción | Admin | Supervisor | Operador | Auditor | Consulta |
|--------|:---:|:---:|:---:|:---:|:---:|
| `users:*` | ✓ | leer | — | — | — |
| `reintegro:create` | ✓ | ✓ | ✓ | — | — |
| `reintegro:read` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `reintegro:update` | ✓ | ✓ | ✓ | — | — |
| `reintegro:approve / reject` | ✓ | ✓ | — | ✓ | — |
| `reintegro:audit` | ✓ | — | — | ✓ | — |
| `audit:read` | ✓ | ✓ | — | ✓ | — |
| `params:write` | ✓ | ✓ | — | — | — |
| `dashboard:read` | ✓ | ✓ | ✓ | ✓ | ✓ |

Definidos en `app/core/constants.py::PERMISOS`.

## Lectura de PDFs

El servicio `pdf_extractor.py` usa una estrategia de dos pasos:

1. **pdfplumber**: extrae texto directo del PDF. Funciona perfecto para PDFs digitales (ej: la plantilla de reintegros ISL).
2. **OCR (Tesseract)**: solo si el texto extraído es muy corto (< 50 chars), asume que es un PDF escaneado y aplica OCR en español.

Después aplica heurísticas regex para detectar:
- Montos (`$X.XXX,XX`)
- CUIL (formato XX-XXXXXXXX-X)
- CBU (22 dígitos) y Alias
- Teléfono argentino
- Fechas (DD/MM/YYYY)
- Tipo de reintegro por keywords (remis, medicación, ortopedia, prestación, etc.)

**Probado con tu plantilla ISL real** — detecta correctamente `traslado_remis` y los campos identificables.

## Capa de IA (opcional, apagada por defecto)

`app/services/ai_extractor.py` está preparado para integrarse con la API de Anthropic y mejorar drásticamente la extracción de datos de tickets/recetas reales. Para activarlo:

1. En `.env`:
   ```
   AI_EXTRACTION_ENABLED=true
   ANTHROPIC_API_KEY=sk-ant-...
   ```
2. `pip install anthropic`
3. Implementar el contenido de `_extraer_con_ia()` siguiendo el esquema sugerido en el docstring.

Cuando esté activo, el endpoint `/analizar-pdf` mergea automáticamente los datos extraídos por IA con los de la regex.

## Migrar a PostgreSQL

Cuando salgas de SQLite (recomendado para producción):

1. `pip install psycopg2-binary`
2. En `.env`:
   ```
   DATABASE_URL=postgresql://user:pass@localhost/reintegros
   ```
3. Considerar agregar Alembic para migraciones (`pip install alembic` + `alembic init`).

Por ahora la app crea las tablas automáticamente al arrancar (`Base.metadata.create_all`) — está bien para desarrollo, pero en producción conviene Alembic.

## Próximos pasos del proyecto

- [ ] **Frontend en React + Vite + Tailwind** (siguiente iteración)
- [ ] Formularios específicos por tipo de reintegro (Medicación con lista de drogas, Ortopedia, Prestaciones)
- [ ] Activar IA para auto-completado real
- [ ] Calculadora de km con integración Google Maps API
- [ ] Tests automatizados (pytest)
- [ ] Migraciones con Alembic
- [ ] Deploy (Docker + reverse proxy)
- [ ] Logs estructurados (logging) y métricas
- [ ] Notificaciones por email/Slack para SLA vencidos
