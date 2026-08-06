/**
 * Axios API client with interceptors.
 * - Sends cookies (HttpOnly refresh token) with every request via withCredentials
 * - Attaches in-memory Bearer access token to requests
 * - On 401, silently refreshes the access token using the refresh cookie
 * - Queues concurrent requests during a refresh so each is retried once
 * - Correlation ID header
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { storageService } from './storageService';

const API_BASE_URL = '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true, // send/receive the HttpOnly refresh cookie
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

/**
 * Handler invoked when the session cannot be recovered (refresh failed).
 * The app registers a router-aware handler so we can clear state and navigate
 * to /login WITHOUT a full page reload (which would wipe in-memory state and
 * cause flicker). Falls back to a hard redirect if nothing is registered.
 */
type SessionExpiredHandler = () => void;
let onSessionExpired: SessionExpiredHandler = () => {
  window.location.href = '/login';
};

export const setSessionExpiredHandler = (handler: SessionExpiredHandler): void => {
  onSessionExpired = handler;
};

/** Perform a silent refresh using the HttpOnly cookie. Returns the new access token. */
export const refreshAccessToken = async (): Promise<string> => {
  const { data } = await axios.post(
    `${API_BASE_URL}/auth/refresh`,
    {},
    { withCredentials: true }
  );
  const token = data.access_token as string;
  storageService.setAccessToken(token);
  return token;
};

// Request interceptor: attach token + correlation ID
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = storageService.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    config.headers['X-Correlation-ID'] = crypto.randomUUID();
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 with a single shared refresh
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Never try to refresh the refresh call itself, and only retry once.
    const isAuthRefreshCall = originalRequest?.url?.includes('/auth/refresh');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthRefreshCall) {
      if (isRefreshing) {
        // Wait for the in-flight refresh, then retry this request.
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(apiClient(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const accessToken = await refreshAccessToken();
        processQueue(null, accessToken);
        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        storageService.clearAccessToken();
        onSessionExpired();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
