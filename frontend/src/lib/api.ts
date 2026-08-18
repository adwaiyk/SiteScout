import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 60000, // 60s timeout for pipeline calls
});

api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle network errors
    if (!error.response) {
      console.error("Network error — backend may be unreachable.");
      return Promise.reject(error);
    }

    // Handle 401 (expired token)
    if (error.response.status === 401) {
      console.warn("Session expired. Logging out...");
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        localStorage.removeItem('userName');
        localStorage.removeItem('userEmail');
        window.location.replace('/login');
      }
    }

    return Promise.reject(error);
  }
);

export default api;