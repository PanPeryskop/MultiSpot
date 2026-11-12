import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'

export default function CallbackPage() {
  const navigate = useNavigate()
  const [error, setError] = useState(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('error')) return params.get('error')
    if (!params.get('code') || !params.get('state')) return 'Missing code or state from Spotify'
    return null
  })
  const hasCalled = useRef(false)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    const state = params.get('state')
    if (!code || !state || params.get('error')) return

    if (hasCalled.current) return
    hasCalled.current = true

    fetch('/auth/exchange', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, state }),
    })
      .then(r => r.json())
      .then(async d => {
        if (d.authenticated) {
          if (window._refreshAuth) await window._refreshAuth()
          navigate('/dashboard', { replace: true })
        } else {
          setError(d.detail || 'Authentication failed')
        }
      })
      .catch(() => setError('Failed to connect to server'))
  }, [navigate])

  if (error) {
    return (
      <main style={{ minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
        <p style={{ color: 'var(--red)', fontWeight: 600 }}>Login failed: {error}</p>
        <a href="/" className="btn btn-ghost">Go back</a>
      </main>
    )
  }

  return (
    <main style={{ minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
      <Loader2 size={32} className="spin" style={{ color: 'var(--green)' }} />
      <p style={{ color: 'var(--text-secondary)' }}>Logging you in…</p>
    </main>
  )
}
