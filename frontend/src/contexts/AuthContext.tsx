import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { authApi } from '../services/api'
import type { User } from '../types'

type AuthValue = { user: User | null; loading: boolean; signIn: (email: string, password: string) => Promise<void>; signUp: (name: string, email: string, password: string) => Promise<void>; signOut: () => void }
const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    if (!localStorage.getItem('dermacare-token')) { setLoading(false); return }
    authApi.me().then(setUser).catch(() => localStorage.removeItem('dermacare-token')).finally(() => setLoading(false))
  }, [])
  const signIn = async (email: string, password: string) => setUser(await authApi.login(email, password))
  const signUp = async (name: string, email: string, password: string) => setUser(await authApi.register(name, email, password))
  const signOut = () => { localStorage.removeItem('dermacare-token'); setUser(null) }
  return <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}