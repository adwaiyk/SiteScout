import axios from 'axios';

// Create a configured Axios instance
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000', // Your FastAPI backend
});

// 1. REQUEST INTERCEPTOR: Automatically attach the token to every outgoing request
api.interceptors.request.use(
  (config) => {
    // Only run on the client side
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

// 2. RESPONSE INTERCEPTOR: Globally catch 401 errors and force logout
api.interceptors.response.use(
  (response) => response, // If the response is good, just pass it through
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn("Session expired. Logging out...");
      
      if (typeof window !== 'undefined') {
        // Erase the dead token
        localStorage.removeItem('token');
        
        // Brute-force redirect back to login
        window.location.replace('/login');
      }
    }
    return Promise.reject(error);
  }
);

export default api;