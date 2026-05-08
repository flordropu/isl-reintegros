import { IconTool } from '@tabler/icons-react';

export default function Placeholder({ title, description }) {
  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="card p-12 text-center">
        <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center mx-auto mb-4">
          <IconTool size={22} />
        </div>
        <h2 className="text-lg font-semibold mb-2">{title}</h2>
        <p className="text-sm text-slate-500">
          {description || 'Esta vista se implementará en la próxima iteración.'}
        </p>
      </div>
    </div>
  );
}
