import { createContext, useContext, useEffect, useState } from 'react';
import { authApi } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const raw = localStorage.getItem('user');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  // Al montar: si hay token, validar contra /me
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }
    authApi.me()
      .then((u) => {
        setUser(u);
        localStorage.setItem('user', JSON.stringify(u));
      })
      .catch(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const data = await authApi.login(email, password);
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
  };

  // Helpers de permisos (espejo del backend en app/core/constants.py)
  const PERMISOS = {
    admin: ['*'],
    supervisor: [
      'users:read',
      'reintegro:read', 'reintegro:create', 'reintegro:update',
      'reintegro:approve', 'reintegro:reject',
      'audit:read', 'params:read', 'params:write', 'dashboard:read',
    ],
    operador: [
      'reintegro:read', 'reintegro:create', 'reintegro:update',
      'documento:upload', 'dashboard:read',
    ],
    auditor_medico: [
      'reintegro:read', 'reintegro:audit',
      'reintegro:approve', 'reintegro:reject', 'reintegro:observe',
      'audit:read', 'dashboard:read',
    ],
    consulta: ['reintegro:read', 'dashboard:read'],
  };

  const can = (accion) => {
    if (!user) return false;
    const perms = PERMISOS[user.role] || [];
    return perms.includes('*') || perms.includes(accion);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, can }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth fuera de AuthProvider');
  return ctx;
}
