import {
  IconCar, IconBus, IconPill, IconStethoscope, IconWheelchair, IconHome,
} from '@tabler/icons-react';
import { ESTADO_LABELS, TIPO_LABELS, slaStatus, slaTextoRelativo } from '../utils/format';

/**
 * Badge de estado del workflow.
 */
export function EstadoBadge({ estado }) {
  const meta = ESTADO_LABELS[estado] || { label: estado, bg: 'bg-slate-100', text: 'text-slate-700' };
  return (
    <span className={`tag ${meta.bg} ${meta.text}`}>
      {meta.label}
    </span>
  );
}

/**
 * Punto de semáforo SLA + texto relativo opcional.
 */
export function SlaIndicator({ reintegro, withText = false }) {
  const status = slaStatus(reintegro);

  const dotClass = {
    rojo: 'bg-sla-alert',
    amarillo: 'bg-sla-warn',
    verde: 'bg-sla-ok',
    na: 'bg-slate-300',
  }[status];

  const textClass = {
    rojo: 'text-rose-700 font-medium',
    amarillo: 'text-amber-700',
    verde: 'text-slate-500',
    na: 'text-slate-400',
  }[status];

  if (!withText) {
    return <span className={`inline-block w-2 h-2 rounded-full ${dotClass}`} />;
  }

  return (
    <span className={`inline-flex items-center gap-1.5 text-xs ${textClass}`}>
      <span className={`w-2 h-2 rounded-full ${dotClass}`} />
      {slaTextoRelativo(reintegro)}
    </span>
  );
}

/**
 * Mapa de íconos por tipo (resuelve el string del backend a un componente).
 */
const TIPO_ICONS = {
  traslado_remis: IconCar,
  traslado_transporte_publico: IconBus,
  medicacion: IconPill,
  ortopedia: IconWheelchair,
  prestacion_medica: IconStethoscope,
  alojamiento: IconHome,
};

/**
 * Etiqueta de tipo con ícono.
 */
export function TipoBadge({ tipo, size = 13 }) {
  const Icon = TIPO_ICONS[tipo] || IconCar;
  const meta = TIPO_LABELS[tipo] || { label: tipo };
  return (
    <span className="inline-flex items-center gap-1.5 text-xs">
      <Icon size={size} className="text-slate-500 flex-shrink-0" />
      <span>{meta.label}</span>
    </span>
  );
}
