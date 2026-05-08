import { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { IconShieldCheck, IconAlertCircle, IconLoader2 } from '@tabler/icons-react';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/dashboard" replace />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Error al iniciar sesión';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  // Atajo demo
  const fillDemo = (mail, pwd) => {
    setEmail(mail);
    setPassword(pwd);
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Panel izquierdo: branding */}
      <div className="hidden lg:flex bg-gradient-to-br from-isl-800 to-isl-900 text-white p-12 flex-col justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-white/15 flex items-center justify-center">
            <IconShieldCheck size={22} />
          </div>
          <div>
            <div className="font-semibold">Reintegros ART</div>
            <div className="text-xs text-isl-100">Sistema integral de gestión</div>
          </div>
        </div>

        <div className="space-y-6 max-w-md">
          <h1 className="text-3xl font-semibold leading-tight">
            Centralizá la operatoria de reintegros
          </h1>
          <p className="text-isl-100 text-sm leading-relaxed">
            Reemplazá planillas por un sistema con trazabilidad completa,
            cálculos automáticos, control de SLA y experiencia operativa simple.
          </p>
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/15">
            <div>
              <div className="text-2xl font-semibold">9</div>
              <div className="text-xs text-isl-100">Estados de workflow</div>
            </div>
            <div>
              <div className="text-2xl font-semibold">5</div>
              <div className="text-xs text-isl-100">Perfiles de usuario</div>
            </div>
            <div>
              <div className="text-2xl font-semibold">4</div>
              <div className="text-xs text-isl-100">Tipos de reintegro</div>
            </div>
          </div>
        </div>

        <div className="text-xs text-isl-100">
          Innovación en Servicios Laborales · ISL
        </div>
      </div>

      {/* Panel derecho: form */}
      <div className="flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-9 h-9 rounded-md bg-isl-700 flex items-center justify-center">
              <IconShieldCheck size={20} className="text-white" />
            </div>
            <div className="font-semibold">Reintegros ART</div>
          </div>

          <h2 className="text-2xl font-semibold mb-1">Iniciar sesión</h2>
          <p className="text-sm text-slate-500 mb-8">
            Accedé con tu cuenta corporativa
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label-field">Email</label>
              <input
                type="email"
                required
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                placeholder="usuario@isl.com.ar"
              />
            </div>

            <div>
              <label className="label-field">Contraseña</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="flex items-start gap-2 p-3 rounded-md bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                <IconAlertCircle size={16} className="flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full py-2.5">
              {loading ? (
                <>
                  <IconLoader2 size={16} className="animate-spin" /> Ingresando...
                </>
              ) : (
                'Ingresar'
              )}
            </button>
          </form>

          {/* Atajos de demo */}
          <div className="mt-8 pt-6 border-t border-slate-200">
            <div className="text-xs text-slate-500 mb-3">Usuarios de prueba</div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                onClick={() => fillDemo('admin@isl.com.ar', 'admin1234')}
                className="px-3 py-2 rounded-md border border-slate-200 hover:bg-slate-50 text-left"
              >
                <div className="font-medium">Admin</div>
                <div className="text-slate-500 truncate">admin@isl.com.ar</div>
              </button>
              <button
                onClick={() => fillDemo('supervisor@isl.com.ar', 'super1234')}
                className="px-3 py-2 rounded-md border border-slate-200 hover:bg-slate-50 text-left"
              >
                <div className="font-medium">Supervisor</div>
                <div className="text-slate-500 truncate">supervisor@isl.com.ar</div>
              </button>
              <button
                onClick={() => fillDemo('operador@isl.com.ar', 'oper1234')}
                className="px-3 py-2 rounded-md border border-slate-200 hover:bg-slate-50 text-left"
              >
                <div className="font-medium">Operador</div>
                <div className="text-slate-500 truncate">operador@isl.com.ar</div>
              </button>
              <button
                onClick={() => fillDemo('auditor@isl.com.ar', 'audit1234')}
                className="px-3 py-2 rounded-md border border-slate-200 hover:bg-slate-50 text-left"
              >
                <div className="font-medium">Auditor</div>
                <div className="text-slate-500 truncate">auditor@isl.com.ar</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
