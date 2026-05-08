import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ReintegrosListado from './pages/ReintegrosListado';
import Placeholder from './components/Placeholder';

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/reintegros" element={<ReintegrosListado />} />
          <Route path="/reintegros/nuevo" element={
            <Placeholder title="Nuevo reintegro" description="Próxima iteración: wizard de carga con upload de PDF y extracción automática." />
          } />
          <Route path="/reintegros/:id" element={
            <Placeholder title="Detalle del reintegro" description="Próxima iteración: workflow visual, documentos, acciones y trazabilidad." />
          } />
          <Route path="/auditoria" element={
            <Placeholder title="Auditoría" description="Próxima iteración: consulta de logs con filtros." />
          } />
          <Route path="/usuarios" element={
            <Placeholder title="Gestión de usuarios" description="Próxima iteración: ABM completo con perfiles." />
          } />
          <Route path="/parametros" element={
            <Placeholder title="Parámetros del sistema" description="Próxima iteración: configuración dinámica (valor/km, topes, motivos, SLA)." />
          } />
        </Route>

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  );
}
