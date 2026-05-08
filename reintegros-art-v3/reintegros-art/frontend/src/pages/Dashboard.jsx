import { useEffect, useState } from 'react';
import {
  IconCar, IconPill, IconStethoscope, IconWheelchair,
  IconAlertTriangle, IconClock, IconFileSearch, IconLoader2,
  IconTrendingUp, IconTrendingDown,
} from '@tabler/icons-react';
import { reintegrosApi } from '../services/api';
import { formatMoney, ROLE_LABELS } from '../utils/format';

const TIPO_VIS = {
  traslado_remis: { label: 'Traslados', icon: IconCar, color: 'bg-isl-400' },
  traslado_transporte_publico: { label: 'Transporte público', icon: IconCar, color: 'bg-isl-200' },
  medicacion: { label: 'Medicación', icon: IconPill, color: 'bg-emerald-500' },
  prestacion_medica: { label: 'Prestaciones', icon: IconStethoscope, color: 'bg-purple-500' },
  ortopedia: { label: 'Ortopedia', icon: IconWheelchair, color: 'bg-orange-500' },
  alojamiento: { label: 'Alojamiento', icon: IconCar, color: 'bg-pink-500' },
};

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    reintegrosApi.dashboard()
      .then(setStats)
      .catch((e) => setError(e.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center text-slate-400">
        <IconLoader2 className="animate-spin mr-2" /> Cargando dashboard...
      </div>
    );
  }
  if (error) {
    return <div className="p-8 text-rose-600 text-sm">{error}</div>;
  }

  // Calcular totales por tipo, ordenados desc
  const tipos = Object.entries(stats.por_tipo || {})
    .sort((a, b) => b[1] - a[1]);
  const maxTipo = Math.max(1, ...tipos.map(([, v]) => v));

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      {/* Header */}
      <div className="flex items-baseline justify-between mb-1">
        <h1 className="text-xl font-semibold">Dashboard operativo</h1>
        <div className="text-xs text-slate-500">
          {new Intl.DateTimeFormat('es-AR', { month: 'long', year: 'numeric' }).format(new Date())}
        </div>
      </div>
      <p className="text-sm text-slate-500 mb-6">
        Visión consolidada de la operación de reintegros
      </p>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-1.5 mb-5">
        <span className="tag bg-isl-50 text-isl-800">Este mes</span>
        <span className="tag bg-slate-100 text-slate-700">Todos los operadores</span>
        <span className="tag bg-slate-100 text-slate-700">Todos los tipos</span>
        <button className="text-xs text-isl-700 hover:underline px-1">+ Agregar filtro</button>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <MetricCard
          label="Casos ingresados"
          value={stats.casos_ingresados}
          delta="+12% vs mes anterior"
          deltaUp
        />
        <MetricCard
          label="Pendientes"
          value={stats.pendientes}
          delta="Activos en el workflow"
        />
        <MetricCard
          label="Vencidos SLA"
          value={stats.vencidos_sla}
          delta={stats.vencidos_sla > 0 ? 'Requiere atención' : 'En término'}
          alert={stats.vencidos_sla > 0}
        />
        <MetricCard
          label="Monto liquidado"
          value={formatMoney(stats.monto_total_liquidado)}
          delta="+18% vs mes anterior"
          deltaUp
          isText
        />
      </div>

      {/* Two-col: por tipo + alertas */}
      <div className="grid lg:grid-cols-3 gap-3 mb-6">
        <div className="card lg:col-span-2 p-5">
          <SectionTitle>Por tipo de reintegro</SectionTitle>
          {tipos.length === 0 ? (
            <div className="text-sm text-slate-400 mt-3">Sin datos aún</div>
          ) : (
            <div className="space-y-3 mt-4">
              {tipos.map(([tipo, count]) => {
                const meta = TIPO_VIS[tipo] || { label: tipo, icon: IconCar, color: 'bg-slate-400' };
                const Icon = meta.icon;
                const pct = (count / maxTipo) * 100;
                return (
                  <div key={tipo}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="flex items-center gap-1.5">
                        <Icon size={14} className="text-slate-500" />
                        {meta.label}
                      </span>
                      <span className="text-slate-500 font-medium">{count}</span>
                    </div>
                    <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${meta.color}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="card p-5">
          <SectionTitle>Alertas operativas</SectionTitle>
          <div className="space-y-2 mt-3">
            {stats.vencidos_sla > 0 && (
              <AlertRow
                icon={IconAlertTriangle}
                tone="rose"
                title={`${stats.vencidos_sla} caso${stats.vencidos_sla > 1 ? 's' : ''} vencidos SLA`}
                desc="Requieren atención inmediata"
              />
            )}
            {stats.proximos_vencer > 0 && (
              <AlertRow
                icon={IconClock}
                tone="amber"
                title={`${stats.proximos_vencer} próximos a vencer`}
                desc="En las próximas 48 horas"
              />
            )}
            {stats.vencidos_sla === 0 && stats.proximos_vencer === 0 && (
              <AlertRow
                icon={IconFileSearch}
                tone="emerald"
                title="Todo en término"
                desc="No hay alertas activas"
              />
            )}
          </div>
        </div>
      </div>

      {/* Productividad por operador */}
      <div className="card p-5">
        <SectionTitle>Productividad por operador</SectionTitle>
        <div className="mt-4 space-y-2.5">
          {(stats.por_operador || []).length === 0 && (
            <div className="text-sm text-slate-400">Sin datos aún</div>
          )}
          {(stats.por_operador || []).map((op) => {
            const max = Math.max(1, ...stats.por_operador.map((o) => o.cantidad));
            const pct = (op.cantidad / max) * 100;
            const initials = (op.nombre || '').split(' ').filter(Boolean).slice(0, 2).map((s) => s[0]).join('').toUpperCase();
            return (
              <div key={op.id} className="flex items-center gap-3 text-xs">
                <div className="w-7 h-7 rounded-full bg-isl-50 text-isl-800 flex items-center justify-center font-medium">
                  {initials}
                </div>
                <div className="flex-1 truncate">{op.nombre}</div>
                <div className="w-32 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-isl-500" style={{ width: `${pct}%` }} />
                </div>
                <div className="w-10 text-right text-slate-500">{op.cantidad}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function SectionTitle({ children }) {
  return <h3 className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">{children}</h3>;
}

function MetricCard({ label, value, delta, deltaUp, alert, isText }) {
  return (
    <div className={`card p-4 ${alert ? 'border-rose-200' : ''}`}>
      <div className={`text-xs ${alert ? 'text-rose-700' : 'text-slate-500'}`}>{label}</div>
      <div className={`mt-1 ${isText ? 'text-xl' : 'text-2xl'} font-semibold ${alert ? 'text-rose-700' : 'text-slate-900'}`}>
        {value}
      </div>
      {delta && (
        <div className={`mt-1 text-[11px] flex items-center gap-1 ${
          alert ? 'text-rose-700' : deltaUp ? 'text-emerald-600' : 'text-slate-500'
        }`}>
          {deltaUp && <IconTrendingUp size={12} />}
          {delta}
        </div>
      )}
    </div>
  );
}

function AlertRow({ icon: Icon, tone, title, desc }) {
  const tones = {
    rose: 'bg-rose-50 text-rose-800 border-rose-100',
    amber: 'bg-amber-50 text-amber-800 border-amber-100',
    emerald: 'bg-emerald-50 text-emerald-800 border-emerald-100',
  };
  return (
    <div className={`flex items-start gap-2.5 p-2.5 rounded-md border text-xs ${tones[tone]}`}>
      <Icon size={16} className="flex-shrink-0 mt-0.5" />
      <div>
        <div className="font-medium">{title}</div>
        <div className="opacity-80">{desc}</div>
      </div>
    </div>
  );
}
