import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react';

export default function Pagination({ page, pageSize, total, onChange }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const desde = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const hasta = Math.min(page * pageSize, total);

  // Páginas a mostrar: actual ± 1, primera, última, con elipsis
  const buildPages = () => {
    const pages = new Set([1, totalPages, page - 1, page, page + 1]);
    return [...pages]
      .filter((p) => p >= 1 && p <= totalPages)
      .sort((a, b) => a - b);
  };

  const pages = buildPages();

  return (
    <div className="flex items-center justify-between mt-3 text-xs">
      <span className="text-slate-500">
        Mostrando {desde}–{hasta} de {total}
      </span>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onChange(page - 1)}
          disabled={page <= 1}
          className="p-1.5 rounded-md border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <IconChevronLeft size={14} />
        </button>

        {pages.map((p, i) => {
          const prev = pages[i - 1];
          const showEllipsisBefore = prev && p - prev > 1;
          return (
            <span key={p} className="flex items-center gap-1">
              {showEllipsisBefore && <span className="text-slate-400 px-1">…</span>}
              <button
                onClick={() => onChange(p)}
                className={`min-w-[28px] h-7 px-2 rounded-md text-xs ${
                  p === page
                    ? 'bg-isl-700 text-white font-medium'
                    : 'border border-slate-200 hover:bg-slate-50'
                }`}
              >
                {p}
              </button>
            </span>
          );
        })}

        <button
          onClick={() => onChange(page + 1)}
          disabled={page >= totalPages}
          className="p-1.5 rounded-md border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <IconChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}
