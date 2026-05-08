import { useEffect, useState, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  IconSearch, IconFilter, IconDownload, IconPlus, IconChevronRight,
  IconLoader2, IconX, IconChevronDown, IconRefresh,
} from '@tabler/icons-react';
import { reintegrosApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { formatMoney } from '../utils/format';
import { EstadoBadge, SlaIndicator, TipoBadge } from '../components/Badges';
import Pagination from '../components/Pagination';

const TIPOS = [
  { value: '', label: 'Todos los tipos' },
  { value: 'traslado_remis', label: 'Traslado — Remis' },
  { value: 'traslado_transporte_publico', label: 'Traslado — Público' },
  { value: 'medicacion', label: 'Medicación' },
  { value: 'ortopedia', label: 'Ortopedia' },
  { value: 'prestacion_medica', label: 'Prestación médica' },
  { value: 'alojamiento', label: 'Alojamiento' },
];

const ESTADOS = [
  { value: '', label: 'Todos los estados' },
  { value: 'ingresado', label: 'Ingresado' },
  { value: 'pendiente_documentacion', label: 'Pendiente doc.' },
  { value: 'en_validacion', label: 'En validación' },
  { value: 'en_auditoria', label: 'En auditoría' },
  { value: 'observado', label: 'Observado' },
  { value: 'aprobado', label: 'Aprobado' },
  { value: 'rechazado', label: 'Rechazado' },
  { value: 'liquidado', label: 'Liquidado' },
  { value: 'pagado', label: 'Pagado' },
];

// Tabs rápidos: cada uno define un preset de filtros
const TABS = [
  { id: 'todos',     label: 'Todos',      filter: {} },
  { id: 'mios',      label: 'Mis casos',  filter: { mios: true } },
  { id: 'vencidos',  label: 'Vencidos',   filter: { sla: 'vencido' }, danger: true },
  { id: 'pendientes',label: 'Pendientes', filter: { estado_grupo: 'pendientes' } },
  { id: 'aprobados', label: 'Aprobados',  filter: { estado: 'aprobado' } },
];

const ESTADOS_PENDIENTES = [
  'ingresado', 'pendiente_documentacion', 'en_validacion', 'en_auditoria', 'observado',
];

export default function ReintegrosListado() {
  const { can } = useAuth();
  const navigate = useNavigate();

  // Tab activo
  const [tab, setTab] = useState('todos');
  // Filtros explícitos
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [tipo, setTipo] = useState('');
  const [estado, setEstado] = useState('');
  const [sla, setSla] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Paginación
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Datos
  const [data, setData] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  // Contadores para tabs (los calcula el dashboard endpoint)
  const [counts, setCounts] = useState({ todos: 0, mios: 0, vencidos: 0, pendientes: 0, aprobados: 0 });

  // Construir params según tab + filtros
  const params = useMemo(() => {
    const p = { page, page_size: pageSize };
    const tabFilter = TABS.find((t) => t.id === tab)?.filter || {};

    // Tab "pendientes" no es un filtro directo del backend; lo resolvemos sin filtrar
    // y mostramos solo estados pendientes vía búsqueda alternativa: pedimos sin filtro
    // y dejamos que el usuario filtre manualmente. Para no hacer multi-call, usamos
    // estado individual cuando corresponde:
    if (tabFilter.estado) p.estado = tabFilter.estado;
    if (tabFilter.sla) p.sla = tabFilter.sla;
    if (tabFilter.mios) p.mios = true;

    // Filtros explícitos (sobrescriben el tab si están seteados)
    if (tipo) p.tipo = tipo;
    if (estado) p.estado = estado;
    if (sla) p.sla = sla;
    if (search) p.q = search;

    return p;
  }, [tab, page, tipo, estado, sla, search]);

  // Reset de página cuando cambian filtros
  useEffect(() => {
    setPage(1);
  }, [tab, tipo, estado, sla, search]);

  // Fetch
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    reintegrosApi.list(params)
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e) => { if (!cancelled) setError(e.response?.data?.detail || e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [params, refreshKey]);

  // Cargar contadores para tabs (via dashboard stats)
  useEffect(() => {
    reintegrosApi.dashboard().then((d) => {
      const pendientes = ESTADOS_PENDIENTES.reduce((acc, e) => acc + (d.por_estado?.[e] || 0), 0);
      setCounts({
        todos: d.casos_ingresados || 0,
        mios: 0, // requeriría endpoint dedicado; lo dejamos en blanco
        vencidos: d.vencidos_sla || 0,
        pendientes,
        aprobados: d.por_estado?.aprobado || 0,
      });
    }).catch(() => { /* silent */ });
  }, [refreshKey]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setSearch(searchInput);
  };

  const clearSearch = () => {
    setSearch('');
    setSearchInput('');
  };

  const clearFilters = () => {
    setTipo('');
    setEstado('');
    setSla('');
    setSearch('');
    setSearchInput('');
  };

  const hasActiveFilters = tipo || estado || sla || search;

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-xl font-semibold">Listado de reintegros</h1>
        {can('reintegro:create') && (
          <Link to="/reintegros/nuevo" className="btn-primary">
            <IconPlus size={16} /> Nuevo reintegro
          </Link>
        )}
      </div>
      <p className="text-sm text-slate-500 mb-5">
        {data.total > 0
          ? `${data.total} caso${data.total === 1 ? '' : 's'} · ordenados por fecha de ingreso`
          : 'Gestión integral de reintegros'}
      </p>

      {/* Search + filter button + export */}
      <div className="flex gap-2 mb-3">
        <form onSubmit={handleSearchSubmit} className="flex-1 relative">
          <IconSearch size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Buscar por código, CUIL, número de siniestro o nombre..."
            className="w-full pl-9 pr-9 py-2 rounded-md border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-isl-200 focus:border-isl-400"
          />
          {searchInput && (
            <button
              type="button"
              onClick={clearSearch}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-100"
            >
              <IconX size={14} />
            </button>
          )}
        </form>
        <button
          onClick={() => setShowFilters((v) => !v)}
          className={`btn-secondary ${showFilters || hasActiveFilters ? 'bg-isl-50 border-isl-200 text-isl-800' : ''}`}
        >
          <IconFilter size={15} />
          Filtros
          {hasActiveFilters && (
            <span className="bg-isl-700 text-white text-[10px] rounded-full px-1.5 py-0.5 font-medium">
              {[tipo, estado, sla, search].filter(Boolean).length}
            </span>
          )}
        </button>
        <button
          onClick={() => setRefreshKey((k) => k + 1)}
          className="btn-secondary"
          title="Refrescar"
        >
          <IconRefresh size={15} />
        </button>
        <button className="btn-secondary" disabled title="Próximamente">
          <IconDownload size={15} /> Exportar
        </button>
      </div>

      {/* Filtros desplegables */}
      {showFilters && (
        <div className="card p-4 mb-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="label-field">Tipo de reintegro</label>
              <Select value={tipo} onChange={setTipo} options={TIPOS} />
            </div>
            <div>
              <label className="label-field">Estado</label>
              <Select value={estado} onChange={setEstado} options={ESTADOS} />
            </div>
            <div>
              <label className="label-field">SLA</label>
              <Select value={sla} onChange={setSla} options={[
                { value: '', label: 'Cualquiera' },
                { value: 'vencido', label: 'Vencidos' },
                { value: 'proximo', label: 'Próximos a vencer' },
                { value: 'en_termino', label: 'En término' },
              ]} />
            </div>
          </div>
          {hasActiveFilters && (
            <div className="mt-3 pt-3 border-t border-slate-100 flex justify-end">
              <button
                onClick={clearFilters}
                className="text-xs text-slate-500 hover:text-slate-700 inline-flex items-center gap-1"
              >
                <IconX size={13} /> Limpiar todos los filtros
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-3 border-b border-slate-200 -mx-1 px-1 overflow-x-auto">
        {TABS.map((t) => {
          const isActive = tab === t.id;
          const count = counts[t.id];
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-3 py-2 text-xs font-medium whitespace-nowrap border-b-2 transition-colors ${
                isActive
                  ? t.danger
                    ? 'border-rose-500 text-rose-700'
                    : 'border-isl-700 text-isl-800'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {t.label}
              {count !== undefined && count > 0 && (
                <span className={`ml-1.5 ${
                  isActive ? (t.danger ? 'text-rose-600' : 'text-isl-600') : 'text-slate-400'
                }`}>
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tabla */}
      <div className="card overflow-hidden">
        {/* Header de columnas */}
        <div className="hidden md:grid grid-cols-[40px_1.4fr_1fr_120px_120px_110px_36px] gap-3 px-4 py-2.5 text-[11px] font-medium text-slate-500 uppercase tracking-wider border-b border-slate-100 bg-slate-50/50">
          <div></div>
          <div>Trabajador / Siniestro</div>
          <div>Tipo</div>
          <div>Estado</div>
          <div>Monto</div>
          <div>SLA</div>
          <div></div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-16 text-slate-400 text-sm">
            <IconLoader2 className="animate-spin mr-2" size={16} /> Cargando reintegros...
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="py-12 text-center text-sm text-rose-600">{error}</div>
        )}

        {/* Empty state */}
        {!loading && !error && data.items.length === 0 && (
          <div className="py-16 text-center">
            <div className="text-sm text-slate-500">No se encontraron reintegros con estos criterios.</div>
            {hasActiveFilters && (
              <button onClick={clearFilters} className="text-xs text-isl-700 hover:underline mt-2">
                Limpiar filtros
              </button>
            )}
          </div>
        )}

        {/* Filas */}
        {!loading && !error && data.items.map((r) => (
          <button
            key={r.id}
            onClick={() => navigate(`/reintegros/${r.id}`)}
            className="w-full text-left grid grid-cols-1 md:grid-cols-[40px_1.4fr_1fr_120px_120px_110px_36px] gap-2 md:gap-3 px-4 py-3 border-b border-slate-100 hover:bg-slate-50 transition-colors"
          >
            {/* Móvil: header compacto */}
            <div className="md:hidden flex items-center justify-between mb-1">
              <span className="text-xs font-mono text-slate-500">{r.codigo}</span>
              <SlaIndicator reintegro={r} withText />
            </div>

            <div className="hidden md:flex items-center">
              <SlaIndicator reintegro={r} />
            </div>

            <div className="min-w-0">
              <div className="text-sm font-medium text-slate-900 truncate">
                {r.trabajador_nombre || '—'}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5 truncate">
                <span className="font-mono">{r.codigo}</span>
                {r.trabajador_cuil && <> · CUIL {r.trabajador_cuil}</>}
                {r.siniestro_numero && <> · Sin. #{r.siniestro_numero}</>}
              </div>
            </div>

            <div className="flex items-center">
              <TipoBadge tipo={r.tipo} />
            </div>

            <div className="flex items-center">
              <EstadoBadge estado={r.estado} />
            </div>

            <div className="flex items-center text-sm font-medium text-slate-900">
              {formatMoney(r.monto_aprobado || r.monto_solicitado)}
            </div>

            <div className="hidden md:flex items-center">
              <SlaIndicator reintegro={r} withText />
            </div>

            <div className="hidden md:flex items-center justify-end text-slate-400">
              <IconChevronRight size={16} />
            </div>
          </button>
        ))}
      </div>

      {/* Paginación */}
      {!loading && !error && data.total > pageSize && (
        <Pagination
          page={page}
          pageSize={pageSize}
          total={data.total}
          onChange={setPage}
        />
      )}
    </div>
  );
}

/**
 * Select compacto y consistente con la paleta.
 */
function Select({ value, onChange, options }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="input-field appearance-none pr-8 cursor-pointer"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      <IconChevronDown
        size={14}
        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
      />
    </div>
  );
}
