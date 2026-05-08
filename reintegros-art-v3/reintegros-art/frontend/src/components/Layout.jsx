import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  IconShieldCheck, IconLayoutDashboard, IconFileInvoice, IconPlus,
  IconUsers, IconSettings, IconClipboardList, IconLogout, IconBell,
} from '@tabler/icons-react';
import { useAuth } from '../context/AuthContext';
import { ROLE_LABELS } from '../utils/format';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: IconLayoutDashboard },
  { to: '/reintegros', label: 'Reintegros', icon: IconFileInvoice },
  { to: '/reintegros/nuevo', label: 'Nuevo reintegro', icon: IconPlus, perm: 'reintegro:create' },
  { to: '/auditoria', label: 'Auditoría', icon: IconClipboardList, perm: 'audit:read' },
  { to: '/usuarios', label: 'Usuarios', icon: IconUsers, adminOnly: true },
  { to: '/parametros', label: 'Parámetros', icon: IconSettings, perm: 'params:read' },
];

export default function Layout() {
  const { user, logout, can } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const visibleItems = navItems.filter((it) => {
    if (it.adminOnly) return user?.role === 'admin';
    if (it.perm) return can(it.perm);
    return true;
  });

  const initials = (user?.nombre_completo || '')
    .split(' ').filter(Boolean).slice(0, 2).map((s) => s[0]).join('').toUpperCase();

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-60 bg-white border-r border-slate-200 flex flex-col">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-isl-700 flex items-center justify-center">
            <IconShieldCheck size={18} className="text-white" />
          </div>
          <div>
            <div className="text-sm font-semibold leading-tight">Reintegros</div>
            <div className="text-[10px] text-slate-500 leading-tight">Sistema ART</div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-3 space-y-0.5">
          {visibleItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/dashboard'}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? 'bg-isl-50 text-isl-800 font-medium'
                    : 'text-slate-600 hover:bg-slate-50'
                }`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-3 py-3 border-t border-slate-200">
          <div className="flex items-center gap-2.5 px-2 py-2">
            <div className="w-8 h-8 rounded-full bg-isl-50 text-isl-800 flex items-center justify-center text-xs font-medium">
              {initials || '?'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium truncate">{user?.nombre_completo}</div>
              <div className="text-[10px] text-slate-500">{ROLE_LABELS[user?.role] || user?.role}</div>
            </div>
            <button
              onClick={handleLogout}
              className="text-slate-400 hover:text-slate-700 p-1"
              title="Cerrar sesión"
            >
              <IconLogout size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between">
          <div className="text-sm text-slate-500">
            {user?.region ? `Región: ${user.region}` : 'Vista general'}
          </div>
          <div className="flex items-center gap-3">
            <button className="relative text-slate-500 hover:text-slate-700 p-1.5 rounded-md hover:bg-slate-100">
              <IconBell size={18} />
              <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-rose-500" />
            </button>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 overflow-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
