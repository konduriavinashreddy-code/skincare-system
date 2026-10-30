import axios from 'axios'
import type { Analysis, ApiResult, Product, User } from '../types'

export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api', withCredentials: false })
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('dermacare-token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const authApi = {
  async login(email: string, password: string) {
    const { data } = await api.post<ApiResult<{ access_token: string; user: User }>>('/auth/login', { email, password })
    localStorage.setItem('dermacare-token', data.data.access_token)
    return data.data.user
  },
  async register(full_name: string, email: string, password: string) {
    const { data } = await api.post<ApiResult<{ access_token: string; user: User }>>('/auth/register', { full_name, email, password })
    localStorage.setItem('dermacare-token', data.data.access_token)
    return data.data.user
  },
  async me() { return (await api.get<ApiResult<User>>('/auth/me')).data.data },
}

export const skinApi = {
  async analyze(file: File) {
    const form = new FormData(); form.append('file', file)
    return (await api.post<ApiResult<Analysis>>('/skin/analyze', form)).data.data
  },
  async history() { return (await api.get<ApiResult<Analysis[]>>('/skin/history')).data.data },
  async recommendations(id: number) { return (await api.get<ApiResult<Product[]>>(`/recommendations/${id}`)).data.data },
  async profile() { return (await api.get<ApiResult<Record<string, unknown>>>('/profile')).data.data },
  async updateProfile(payload: Record<string, unknown>) { return (await api.put<ApiResult<Record<string, unknown>>>('/profile', payload)).data.data },
}

export const productApi = {
  async list(params: Record<string, string | boolean> = {}) { return (await api.get<ApiResult<Product[]>>('/products', { params })).data.data },
  async saved() { return (await api.get<ApiResult<Product[]>>('/products/saved')).data.data },
  async save(id: number, saved: boolean) { return api.request({ url: `/products/${id}/save`, method: saved ? 'DELETE' : 'POST' }) },
  async deleteHistory() { return api.delete('/privacy/history') },
}

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) return error.response?.data?.error?.message || error.message || 'The service could not be reached.'
  return 'Something went wrong. Please try again.'
}