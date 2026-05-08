import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Inyectar token en cada request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Manejar 401 globalmente: limpiar y redirigir a login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      // evitar loop si ya estamos en /login
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

// ----- Auth -----
export const authApi = {
  login: (email, password) =>
    api.post('/auth/login', { email, password }).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
};

// ----- Reintegros -----
export const reintegrosApi = {
  list: (params) => api.get('/reintegros', { params }).then((r) => r.data),
  get: (id) => api.get(`/reintegros/${id}`).then((r) => r.data),
  create: (data) => api.post('/reintegros', data).then((r) => r.data),
  update: (id, data) => api.patch(`/reintegros/${id}`, data).then((r) => r.data),
  cambiarEstado: (id, data) =>
    api.post(`/reintegros/${id}/estado`, data).then((r) => r.data),
  dashboard: () => api.get('/reintegros/stats/dashboard').then((r) => r.data),
  uploadDocumento: (id, file, tipo = 'otro', procesar = true) => {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('tipo', tipo);
    fd.append('procesar', procesar);
    return api.post(`/reintegros/${id}/documentos`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data);
  },
  analizarPdf: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return api.post('/reintegros/analizar-pdf', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data);
  },
};

// ----- Trabajadores / Siniestros -----
export const trabajadoresApi = {
  list: (q) => api.get('/trabajadores', { params: { q } }).then((r) => r.data),
  create: (data) => api.post('/trabajadores', data).then((r) => r.data),
};

export const siniestrosApi = {
  list: (q) => api.get('/siniestros', { params: { q } }).then((r) => r.data),
  get: (id) => api.get(`/siniestros/${id}`).then((r) => r.data),
  create: (data) => api.post('/siniestros', data).then((r) => r.data),
};

// ----- Usuarios -----
export const usersApi = {
  list: () => api.get('/users').then((r) => r.data),
  create: (data) => api.post('/users', data).then((r) => r.data),
  update: (id, data) => api.patch(`/users/${id}`, data).then((r) => r.data),
  remove: (id) => api.delete(`/users/${id}`).then((r) => r.data),
};

// ----- Audit -----
export const auditApi = {
  list: (params) => api.get('/audit', { params }).then((r) => r.data),
};

// ----- Parametros -----
export const parametrosApi = {
  list: (categoria) => api.get('/parametros', { params: { categoria } }).then((r) => r.data),
  upsert: (clave, data) => api.put(`/parametros/${clave}`, data).then((r) => r.data),
};
