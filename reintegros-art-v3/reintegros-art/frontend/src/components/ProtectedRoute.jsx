import { Navigate, useLocation } from 'react-router-dom';
import { IconLoader2 } from '@tabler/icons-react';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-400">
        <IconLoader2 className="animate-spin mr-2" size={18} /> Verificando sesión...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
