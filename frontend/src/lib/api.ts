import axios from 'axios';
import type { AxiosInstance } from 'axios';

// Create axios instance with base configuration
const axiosInstance: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add authentication token
// TODO: Enable when authentication is implemented
// axiosInstance.interceptors.request.use(
//   (config) => {
//     const token = localStorage.getItem('auth_token');
//     if (token) {
//       config.headers.Authorization = `Bearer ${token}`;
//     }
//     return config;
//   },
//   (error) => {
//     return Promise.reject(error);
//   }
// );

// Response interceptor - Handle errors
// TODO: Enable when authentication is implemented
// axiosInstance.interceptors.response.use(
//   (response: AxiosResponse) => {
//     return response;
//   },
//   (error: AxiosError) => {
//     // Handle 401 Unauthorized - redirect to login
//     if (error.response?.status === 401) {
//       localStorage.removeItem('auth_token');
//       window.location.href = '/login';
//     }
//     return Promise.reject(error);
//   }
// );

// HTTP method wrappers
export const get = async <T = unknown>(url: string, params?: Record<string, unknown>): Promise<T> => {
  const response = await axiosInstance.get<T>(url, params ? { params } : undefined);
  return response.data;
};

export const post = async <T = unknown>(url: string, data?: Record<string, unknown>): Promise<T> => {
  const response = await axiosInstance.post<T>(url, data);
  return response.data;
};

export const put = async <T = unknown>(url: string, data?: Record<string, unknown>): Promise<T> => {
  const response = await axiosInstance.put<T>(url, data);
  return response.data;
};

export const patch = async <T = unknown>(url: string, data?: Record<string, unknown>): Promise<T> => {
  const response = await axiosInstance.patch<T>(url, data);
  return response.data;
};

export const del = async <T = unknown>(url: string): Promise<T> => {
  const response = await axiosInstance.delete<T>(url);
  return response.data;
};

// Export axios instance for advanced usage
export default axiosInstance;
