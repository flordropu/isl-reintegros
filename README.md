# Frontend — Reintegros ART

Frontend en React + Vite + Tailwind para el sistema de gestión de reintegros ART.

> **Estado**: Iteración 1 — base completa con Login, Dashboard y navegación. Páginas restantes (Listado, Nuevo Reintegro con PDF, Detalle, Usuarios, Auditoría, Parámetros) en próxima iteración.

## Stack

- **React 18** + **Vite 5**
- **Tailwind CSS 3** con paleta corporativa
- **React Router 6** para navegación
- **Axios** con interceptores para JWT
- **@tabler/icons-react** para íconos (5800+ disponibles, todos outline)

## Setup local

### Pre-requisitos

- **Node.js 18+** y **npm** (o yarn / pnpm)
- El **backend corriendo** en http://localhost:8000 (ver `backend/README.md`)

### Pasos

```bash
cd frontend
npm install
npm run dev
```

La app abre en http://localhost:5173

Vite ya está configurado para hacer proxy de `/api` y `/uploads` a `localhost:8000`, así que el frontend habla con el backend sin tocar CORS ni configurar nada.

### Build de producción

```bash
npm run build
```

Genera `dist/` con los archivos estáticos listos para servir desde cualquier CDN/Nginx.

## Estructura

```
frontend/src/
├── components/
│   ├── Layout.jsx            # Sidebar + topbar (auth-aware)
│   ├── ProtectedRoute.jsx    # Guard de rutas privadas
│   └── Placeholder.jsx       # Vista temporal para páginas no implementadas
├── context/
│   └── AuthContext.jsx       # Estado global de auth + helper `can(accion)`
├── pages/
│   ├── Login.jsx             # Login con atajos demo
│   └── Dashboard.jsx         # KPIs, alertas, productividad
├── services/
│   └── api.js                # Cliente axios + endpoints organizados
├── utils/
│   └── format.js             # Formateadores: moneda, fechas, SLA
├── App.jsx                   # Router principal
├── main.jsx                  # Entry point
└── index.css                 # Tailwind + estilos base
```

## Decisiones de diseño

### Paleta corporativa (Tailwind)

Definida en `tailwind.config.js`:

- **`brand`**: ramp azul corporativo (50 a 900). Usado para acciones primarias, nav activa, headers.
- **`sla`**: tres tonos para semaforización (`ok` verde, `warn` ámbar, `alert` rojo).

Todo el color "de estado" sale del sistema de Tailwind directo (rose, amber, emerald, slate, etc.) para mantener consistencia.

### Componentes utilitarios

En `index.css` definí clases componibles que evitan repetir Tailwind por todos lados:

- `.btn-primary`, `.btn-secondary`, `.btn-ghost` — botones
- `.input-field`, `.label-field` — formularios
- `.card` — contenedores con borde + sombra suave
- `.tag` — pills de estado

Permite que cuando se cambie la paleta corporativa real (cuando ISL provea sus colores), se ajuste en un solo lugar y se propague.

### Sistema de permisos

`AuthContext.can(accion)` espeja el backend (`app/core/constants.py::PERMISOS`). Se usa en el Sidebar para mostrar/ocultar items, y en cada página para condicionar botones.

```jsx
const { can } = useAuth();
if (can('reintegro:approve')) { /* mostrar botón */ }
```

### Cliente API

`services/api.js` está organizado por dominio (`authApi`, `reintegrosApi`, `usersApi`, etc.). Cada función devuelve directamente `response.data` para evitar acceder al `.data` por todos lados.

El interceptor de respuestas maneja 401 globalmente: limpia el token y redirige a /login.

## Lo que funciona ahora

- ✅ Login con validación contra el backend real
- ✅ Persistencia del token y usuario en localStorage
- ✅ Refresh automático del usuario al recargar la página (verifica el token con `/auth/me`)
- ✅ Logout
- ✅ Sidebar con navegación según permisos
- ✅ Dashboard real conectado a `/api/v1/reintegros/stats/dashboard`
- ✅ Atajos de demo en Login para probar los 4 perfiles
- ✅ Layout responsive (sidebar full en desktop, panel de branding solo en lg+)
- ✅ Formateadores de moneda ARS y fechas

## Próxima iteración

- [ ] **Listado de reintegros** con tabla, filtros (estado/tipo/SLA/búsqueda), paginación y semaforización
- [ ] **Nuevo reintegro** — wizard de 4 pasos con upload de PDF y pre-llenado automático
- [ ] **Detalle del reintegro** — workflow visual + documentos + acciones (aprobar/rechazar/observar)
- [ ] **ABM Usuarios** (admin)
- [ ] **Auditoría** — listado de logs con filtros
- [ ] **Parametrización** — editor de configuración dinámica
- [ ] Toasts/notificaciones para feedback de acciones
- [ ] Estados de carga/error consistentes
