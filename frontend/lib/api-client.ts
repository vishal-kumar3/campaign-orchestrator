import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export function isApiError(error: unknown, status?: number): error is ApiError {
  return error instanceof ApiError && (status === undefined || error.status === status)
}

function createAxiosClient(getToken: () => Promise<string | null>): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE,
    headers: { 'Content-Type': 'application/json' },
  })

  client.interceptors.request.use(async (config) => {
    const token = await getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  client.interceptors.response.use(
    (response) => response,
    (error) => {
      const status = error.response?.status ?? 0
      const body = error.response?.data
      const message =
        typeof body === 'object' && body && 'detail' in body
          ? String((body as { detail: unknown }).detail)
          : typeof body === 'string'
            ? body
            : error.message
      return Promise.reject(new ApiError(message, status, body))
    },
  )

  return client
}

export function createApiClient(getToken: () => Promise<string | null>) {
  const client = createAxiosClient(getToken)

  return {
    async get<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
      const { data } = await client.get<T>(path, config)
      return data
    },
    async post<T>(path: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
      const headers =
        body instanceof FormData
          ? { ...config?.headers, 'Content-Type': undefined }
          : config?.headers
      const { data } = await client.post<T>(path, body, { ...config, headers })
      return data
    },
    async patch<T>(path: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
      const { data } = await client.patch<T>(path, body, config)
      return data
    },
    async delete<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
      const { data } = await client.delete<T>(path, config)
      return data
    },
  }
}

export type ApiClient = ReturnType<typeof createApiClient>
