/**
 * Formatea un número como moneda argentina.
 */
export function formatMoney(value) {
  if (value == null) return '-';
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Formatea una fecha ISO a dd/mm/yyyy.
 */
export function formatDate(iso, withTime = false) {
  if (!iso) return '-';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const dd = String(d.getDate()).padStart(2, '0');
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const yy = d.getFullYear();
  if (!withTime) return `${dd}/${mm}/${yy}`;
  const hh = String(d.getHours()).padStart(2, '0');
  const mi = String(d.getMinutes()).padStart(2, '0');
  return `${dd}/${mm}/${yy} ${hh}:${mi}`;
}

/**
 * Devuelve color/etiqueta del SLA según fecha de vencimiento y estado.
 * Retorna 'verde' | 'amarillo' | 'rojo' | 'na'.
 */
export function slaStatus(reintegro) {
  const terminales = ['pagado', 'rechazado', 'liquidado', 'aprobado'];
  if (terminales.includes(reintegro?.estado)) return 'na';
  if (!reintegro?.fecha_vencimiento_sla) return 'verde';

  const ahora = new Date();
  const vence = new Date(reintegro.fecha_vencimiento_sla);
  const diffMs = vence - ahora;
  const diffH = diffMs / (1000 * 60 * 60);

  if (diffH < 0) return 'rojo';
  if (diffH < 48) return 'amarillo';
  return 'verde';
}

export function slaTextoRelativo(reintegro) {
  if (!reintegro?.fecha_vencimiento_sla) return '-';
  const ahora = new Date();
  const vence = new Date(reintegro.fecha_vencimiento_sla);
  const diffMs = vence - ahora;
  const diffH = Math.round(diffMs / (1000 * 60 * 60));
  if (diffH < 0) {
    const dias = Math.ceil(-diffH / 24);
    return dias <= 1 ? `Vencido ${(-diffH)}h` : `Vencido ${dias}d`;
  }
  if (diffH < 48) return `${diffH}hs`;
  return `${Math.round(diffH / 24)}d`;
}

/**
 * Mapea estado del workflow → tag CSS y label legible.
 */
export const ESTADO_LABELS = {
  ingresado: { label: 'Ingresado', bg: 'bg-slate-100', text: 'text-slate-700' },
  pendiente_documentacion: { label: 'Pend. doc.', bg: 'bg-amber-100', text: 'text-amber-800' },
  en_validacion: { label: 'En validación', bg: 'bg-brand-50', text: 'text-brand-700' },
  en_auditoria: { label: 'En auditoría', bg: 'bg-purple-100', text: 'text-purple-800' },
  observado: { label: 'Observado', bg: 'bg-amber-100', text: 'text-amber-800' },
  aprobado: { label: 'Aprobado', bg: 'bg-emerald-100', text: 'text-emerald-800' },
  rechazado: { label: 'Rechazado', bg: 'bg-rose-100', text: 'text-rose-800' },
  liquidado: { label: 'Liquidado', bg: 'bg-teal-100', text: 'text-teal-800' },
  pagado: { label: 'Pagado', bg: 'bg-teal-200', text: 'text-teal-900' },
};

export const TIPO_LABELS = {
  traslado_remis: { label: 'Traslado remis', icon: 'IconCar' },
  traslado_transporte_publico: { label: 'Traslado público', icon: 'IconBus' },
  medicacion: { label: 'Medicación', icon: 'IconPill' },
  ortopedia: { label: 'Ortopedia', icon: 'IconWheelchair' },
  prestacion_medica: { label: 'Prestación médica', icon: 'IconStethoscope' },
  alojamiento: { label: 'Alojamiento', icon: 'IconHome' },
};

export const ROLE_LABELS = {
  admin: 'Administrador',
  supervisor: 'Supervisor',
  operador: 'Operador',
  auditor_medico: 'Auditor médico',
  consulta: 'Consulta',
};
