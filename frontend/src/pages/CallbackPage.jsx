import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'

export default function CallbackPage() {
  const navigate = useNavigate()
  const [error, setError] = useState(null)
  const hasCalled = useRef(false)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    const state = params.get('state')
    const err = params.get('error')

    if (err || !code || !state) {
      setError(err || 'Missing code or state from Spotify')
      return
    }

    if (hasCalled.current) return
    hasCalled.current = true

    fetch('/auth/exchange', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, state }),
    })
      .then(r => r.json())
      .then(d => {
        if (d.authenticated) {
          if (window._refreshAuth) window._refreshAuth()
          navigate('/dashboard', { replace: true })
        } else {
          setError(d.detail || 'Authentication failed')
        }
      })
      .catch(() => setError('Failed to connect to server'))
  }, [])

  if (error) {
    return (
      <main style={{ minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
        <p style={{ color: 'var(--color-error)', fontWeight: 600 }}>Login failed: {error}</p>
        <a href="/" className="btn btn-ghost">Go back</a>
      </main>
    )
  }

  return (
    <main style={{ minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
      <Loader2 size={32} className="spin" style={{ color: 'var(--color-green)' }} />
      <p style={{ color: 'var(--color-text-secondary)' }}>Logging you in…</p>
    </main>
  )
}
