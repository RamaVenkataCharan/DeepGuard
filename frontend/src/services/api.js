import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

// Event listeners for global network & API reachable telemetry
const networkSubscribers = new Set();

const notifySubscribers = (status) => {
  networkSubscribers.forEach((callback) => callback(status));
};

export const subscribeNetworkStatus = (callback) => {
  networkSubscribers.add(callback);
  return () => networkSubscribers.delete(callback);
};

export const checkApiHealth = async () => {
  try {
    // Ping dashboard stats endpoint with low timeout
    await axios.get(`${API_URL}/dashboard/stats`, { timeout: 4000 });
    notifySubscribers({ reachable: true });
    return true;
  } catch (err) {
    notifySubscribers({ reachable: false, error: err });
    return false;
  }
};

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000, // 10s request timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT access token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token rotation and retry with backoff for 5xx/network errors
api.interceptors.response.use(
  (response) => {
    notifySubscribers({ reachable: true });
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;

    // 1. Handle token rotation on 401 Unauthorized
    if (status === 401 && !originalRequest._retry && !originalRequest.url?.includes('/auth/refresh')) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/auth/refresh`, {}, {
            headers: { Authorization: `Bearer ${refreshToken}` },
            timeout: 5000,
          });
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // 2. Suppress retries for 4xx errors (Bad Request, Forbidden, Not Found)
    if (status && status >= 400 && status < 500) {
      notifySubscribers({ reachable: true });
      return Promise.reject(error);
    }

    // 3. Retry with exponential backoff for transient failures (Network Error, Timeout, 5xx)
    const maxRetries = 3;
    originalRequest._retryCount = originalRequest._retryCount || 0;

    if (originalRequest._retryCount < maxRetries) {
      originalRequest._retryCount += 1;
      const backoffDelay = Math.pow(2, originalRequest._retryCount - 1) * 1000; // 1s, 2s, 4s

      console.warn(
        `[DeepGuard API Retry] Transient failure (${error.message}). Retrying request ${originalRequest.url} (Attempt ${originalRequest._retryCount}/${maxRetries}) in ${backoffDelay}ms...`
      );

      notifySubscribers({ reachable: false, message: `Retrying request (${originalRequest._retryCount}/${maxRetries})...` });

      await new Promise((resolve) => setTimeout(resolve, backoffDelay));
      return api(originalRequest);
    }

    // Final failure after retries
    notifySubscribers({ reachable: false, error: error.message });
    return Promise.reject(error);
  }
);

export default api;
