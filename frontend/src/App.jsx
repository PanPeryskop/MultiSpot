import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState, useCallback } from 'react'
import LoginPage from './pages/LoginPage'
import CallbackPage from './pages/CallbackPage'
import DashboardPage from './pages/DashboardPage'
import RandomHubPage from './pages/RandomHubPage'
import TrackToPlaylistPage from './pages/TrackToPlaylistPage'
import QueueSetterPage from './pages/QueueSetterPage'
import PlaylistShufflerPage from './pages/PlaylistShufflerPage'
import MagicRecommenderPage from './pages/MagicRecommenderPage'
import TimeMachinePage from './pages/TimeMachinePage'
import TrackStatsPage from './pages/TrackStatsPage'
import StatsPage from './pages/StatsPage'
import FusionCenterPage from './pages/FusionCenterPage'
import RewindPage from './pages/RewindPage'
import ReleaseRadarPage from './pages/ReleaseRadarPage'
import PlaylistXrayPage from './pages/PlaylistXrayPage'
import AutopilotPage from './pages/AutopilotPage'
import Navbar from './components/Navbar'
import Toast from './components/Toast'
import { ToastContext } from './toast'


function App() {
  const [user, setUser] = useState(undefined)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    ToastContext.push = (msg, type = 'info') => {
      setToast({ msg, type, key: Date.now() })
    }
  }, [])

  const checkAuth = useCallback(() => {
    return fetch('/auth/me', { credentials: 'include' })
      .then(r => r.json())
      .then(d => setUser(d.authenticated ? d : null))
      .catch(() => setUser(null))
  }, [])

  useEffect(() => {
    checkAuth()
    window._refreshAuth = checkAuth
    window._logout = async () => {
      try {
        await fetch('/auth/logout', { method: 'POST', credentials: 'include' })
      } catch (err) {
        console.error('Logout error:', err)
      } finally {
        setUser(null)
      }
    }
  }, [checkAuth])

  if (user === undefined) return null

  const authed = (el) => user ? el : <Navigate to="/" replace />

  return (
    <BrowserRouter>
      {user && <Navbar user={user} />}
      <Routes>
        <Route path="/" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
        <Route path="/dashboard" element={authed(<DashboardPage />)} />
        <Route path="/random-hub" element={authed(<RandomHubPage />)} />
        <Route path="/track-to-playlist" element={authed(<TrackToPlaylistPage />)} />
        <Route path="/queue-setter" element={authed(<QueueSetterPage />)} />
        <Route path="/playlist-shuffler" element={authed(<PlaylistShufflerPage />)} />
        <Route path="/magic-recommender" element={authed(<MagicRecommenderPage />)} />
        <Route path="/fusion-center" element={authed(<FusionCenterPage />)} />
        <Route path="/time-machine" element={authed(<TimeMachinePage />)} />
        <Route path="/track-stats" element={authed(<TrackStatsPage />)} />
        <Route path="/stats" element={authed(<StatsPage />)} />
        <Route path="/rewind" element={authed(<RewindPage />)} />
        <Route path="/release-radar" element={authed(<ReleaseRadarPage />)} />
        <Route path="/playlist-xray" element={authed(<PlaylistXrayPage />)} />
        <Route path="/autopilot" element={authed(<AutopilotPage />)} />
        <Route path="/callback" element={<CallbackPage />} />
        <Route path="*" element={<Navigate to={user ? '/dashboard' : '/'} replace />} />
      </Routes>
      {toast && <Toast key={toast.key} message={toast.msg} type={toast.type} />}
    </BrowserRouter>
  )
}

export default App
