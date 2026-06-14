import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { auth } from '@clerk/nextjs/server'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'

async function createClient(): Promise<AxiosInstance> {
  const { getToken } = await auth()
  const token = await getToken()

  const client = axios.create({
    baseURL: API_BASE,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  client.interceptors.response.use(
    (response) => response,
    (error) => {
      const status = error.response?.status ?? 'error'
      const body = error.response?.data ?? error.message
      return Promise.reject(
        new Error(`API ${status}: ${typeof body === 'string' ? body : JSON.stringify(body)}`)
      )
    },
  )

  return client
}

export const api = {
  async get<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const { data } = await (await createClient()).get<T>(path, config)
    return data
  },

  async post<T>(path: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const { data } = await (await createClient()).post<T>(path, body, config)
    return data
  },

  async patch<T>(path: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const { data } = await (await createClient()).patch<T>(path, body, config)
    return data
  },

  async put<T>(path: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const { data } = await (await createClient()).put<T>(path, body, config)
    return data
  },

  async delete<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const { data } = await (await createClient()).delete<T>(path, config)
    return data
  },
}
