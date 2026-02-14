/**
 * MergenLite — API Client
 * =======================
 * Central Axios instance for all backend calls.
 *
 * Features:
 *  - Base URL from VITE_API_URL env var
 *  - 60s timeout (pipelines can be slow)
 *  - Request / response logging in dev
 *  - Global error normalisation
 *  - Auth header injection (Basic auth)
 */

import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

// ---------------------------------------------------------------------------
// Instance
// ---------------------------------------------------------------------------
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 60_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ---------------------------------------------------------------------------
// Auth (optional — reads from localStorage)
// ---------------------------------------------------------------------------
function getAuthHeader(): string | null {
  const creds = localStorage.getItem('mergenlite_auth') // "user:pass" base64
  return creds ? `Basic ${creds}` : null
}

// ---------------------------------------------------------------------------
// Request interceptor
// ---------------------------------------------------------------------------
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  // Inject auth if available
  const auth = getAuthHeader()
  if (auth && config.headers) {
    config.headers.Authorization = auth
  }

  if (import.meta.env.DEV) {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.params ?? '')
  }
  return config
})

// ---------------------------------------------------------------------------
// Response interceptor
// ---------------------------------------------------------------------------
api.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log(`[API] ✓ ${response.status} ${response.config.url}`)
    }
    return response
  },
  (error: AxiosError) => {
    const status = error.response?.status
    const detail = (error.response?.data as any)?.detail

    // Normalise error message
    const message =
      detail ||
      error.response?.statusText ||
      error.message ||
      'Unknown error'

    if (import.meta.env.DEV) {
      console.error(`[API] ✗ ${status ?? '?'} ${error.config?.url}`, message)
    }

    // Attach friendly message for consumers
    ; (error as any).friendlyMessage = message

    return Promise.reject(error)
  },
)

// ---------------------------------------------------------------------------
// Helper: set / clear credentials
// ---------------------------------------------------------------------------
export function setCredentials(username: string, password: string) {
  const encoded = btoa(`${username}:${password}`)
  localStorage.setItem('mergenlite_auth', encoded)
}

export function clearCredentials() {
  localStorage.removeItem('mergenlite_auth')
}

export default api
