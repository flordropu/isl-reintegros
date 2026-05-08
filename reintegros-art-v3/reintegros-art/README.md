# Sistema Integral de Gestión de Reintegros ART

Plataforma web para la gestión integral de reintegros ART, reemplazando el circuito operativo actual basado en planillas Excel y procesos manuales.

## Estado actual

| Componente | Estado |
|------------|:---:|
| **Backend (FastAPI)** | ✅ MVP funcional |
| Modelos y DB | ✅ |
| Autenticación + permisos por rol | ✅ |
| Workflow de 9 estados con SLA | ✅ |
| Carga + análisis de PDFs (texto + OCR) | ✅ |
| Audit logs | ✅ |
| Parametrización dinámica | ✅ |
| **Frontend (React)** | 🟡 Iteración 2 — listado + paleta ISL |
| Login + auth + persistencia | ✅ |
| Sidebar + permisos por rol | ✅ |
| Dashboard real conectado | ✅ |
| Listado de reintegros (filtros, búsqueda, SLA) | ✅ |
| Paleta corporativa ISL aplicada | ✅ |
| Búsqueda accent-insensitive | ✅ |
| Nuevo Reintegro (wizard con PDF) | ⏳ próxima iteración |
| Detalle del caso | ⏳ próxima iteración |
| ABM Usuarios / Auditoría / Parámetros | ⏳ próxima iteración |

## Estructura

```
reintegros-art/
├── backend/      # API REST en FastAPI (ver backend/README.md)
└── frontend/     # React + Vite + Tailwind (en construcción)
```

## Empezar a usar

**1) Backend** (requerido siempre — ver `backend/README.md` para detalles):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

**2) Frontend** (en otra terminal — ver `frontend/README.md`):

```bash
cd frontend
npm install
npm run dev
```

Frontend en http://localhost:5173 — ya conecta con el backend automáticamente.
Loguearse con `operador@isl.com.ar` / `oper1234` (o usar los atajos de demo en la pantalla de login).

## Documentación funcional

Los requerimientos completos están en el documento funcional original del proyecto. Algunos puntos clave que el backend ya cubre:

- ABM completo de usuarios con 5 perfiles (Admin, Supervisor, Operador, Auditor médico, Consulta)
- Permisos por módulo y por acción
- Reintegros con 4 tipos principales: Traslados, Medicación, Ortopedia, Prestaciones Médicas
- Workflow con 9 estados y validación de transiciones
- SLA configurable con semaforización (verde/amarillo/rojo)
- Trazabilidad completa via audit log
- Parametrización dinámica de valor/km, topes, motivos de rechazo, SLA, etc.
- Carga de documentos con extracción automática de datos (texto y OCR)
- Capa de IA preparada para auto-completado (apagada por defecto)

## Tecnologías

**Backend**: Python 3.10+, FastAPI, SQLAlchemy 2.0, SQLite (→ PostgreSQL en producción), JWT, pdfplumber, Tesseract OCR

**Frontend** (próximamente): React 18, Vite, Tailwind CSS, Axios, Tabler Icons
