import { useState } from 'react'
import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { ArrowUpRight, Menu, Sparkles, X } from 'lucide-react'
import { useAuth } from './contexts/AuthContext'
import { AuthPage, DashboardPage, HistoryPage, LandingPage, AnalyzePage, ResultsPage, ProductsPage, SavedPage, ProfilePage, PrivacyPage } from './pages/Pages'
import AssistantWidget from './AssistantWidget'

function Navigation() {
  const { user, signOut } = useAuth()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const links = user ? [['Overview', '/app'], ['Analyze', '/analyze'], ['Products', '/products'], ['History', '/history']] : [['How it works', '/#how'], ['Safety', '/#safety'], ['Products', '/#products']]
  return <header className="topbar"><Link className="brand" to="/"><span className="brand-mark"><Sparkles size={19} /></span><span>derma<span>care</span><small>AI SKIN JOURNAL</small></span></Link>
    <button className="menu-toggle icon-button" aria-label="Toggle navigation" onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button>
    <nav className={open ? 'nav-links open' : 'nav-links'}>{links.map(([label, to]) => <Link key={to} className={location.pathname === to ? 'active' : ''} to={to} onClick={() => setOpen(false)}>{label}</Link>)}
      {user ? <><Link to="/saved" onClick={() => setOpen(false)}>Saved</Link><Link to="/profile" onClick={() => setOpen(false)} aria-label="Profile">{user.full_name.split(' ')[0]}</Link><button className="nav-signout" onClick={() => { signOut(); setOpen(false) }}>Sign out</button></> : <><Link className="nav-login" to="/login">Log in</Link><Link className="button button-dark nav-cta" to="/register">Get started <ArrowUpRight size={16} /></Link></>}
    </nav>
  </header>
}

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="page-loading">Opening your skin journal...</div>
  return user ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  const [assistantOpen, setAssistantOpen] = useState(false)
  return <><Navigation /><main><Routes>
    <Route path="/" element={<LandingPage />} />
    <Route path="/login" element={<AuthPage />} /><Route path="/register" element={<AuthPage register />} />
    <Route path="/app" element={<Protected><DashboardPage /></Protected>} />
    <Route path="/analyze" element={<Protected><AnalyzePage /></Protected>} />
    <Route path="/assistant" element={<Navigate to="/" replace />} />
    <Route path="/results/:id" element={<Protected><ResultsPage /></Protected>} />
    <Route path="/products" element={<Protected><ProductsPage /></Protected>} />
    <Route path="/saved" element={<Protected><SavedPage /></Protected>} />
    <Route path="/history" element={<Protected><HistoryPage /></Protected>} />
    <Route path="/profile" element={<Protected><ProfilePage /></Protected>} />
    <Route path="/privacy" element={<Protected><PrivacyPage /></Protected>} />
    <Route path="*" element={<div className="empty-page"><span className="eyebrow">404 / NOT FOUND</span><h1>This page has wandered off.</h1><Link className="button button-dark" to="/">Back to the beginning</Link></div>} />
  </Routes></main><footer className="site-footer"><span>© 2026 DermaCare AI</span><span>Careful observations. No diagnoses.</span><Link to="/privacy">Privacy & data</Link></footer><AssistantWidget open={assistantOpen} onOpenChange={setAssistantOpen} /></>
}