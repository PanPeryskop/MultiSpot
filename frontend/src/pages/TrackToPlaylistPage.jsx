import { useState } from 'react'
import { Music2, Loader2, ExternalLink } from 'lucide-react'
import { ToastContext } from '../App'
import styles from './FeaturePage.module.css'

export default function TrackToPlaylistPage() {
  const [url, setUrl] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)
    try {
      const r = await fetch('/api/track-to-playlist', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ track_url: url, playlist_name: name || 'Track Recommendations' }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Something went wrong')
      setResult(d)
      ToastContext.push('Playlist generated!', 'success')
      setUrl('')
      setName('')
    } catch (err) {
      ToastContext.push(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className={`${styles.page} page-enter`}>
      <header className={styles.header}>
        <h1 className={styles.title}>Track to Playlist</h1>
        <p className={styles.subtitle}>
          Seed a full playlist from a single track. We'll find 100 perfectly matching songs based on its acoustic fingerprint and create a new playlist for you.
        </p>
      </header>

      <form onSubmit={submit} className={styles.form}>
        <div className={styles.field}>
          <label className="label">Seed Track URL</label>
          <input
            type="url"
            className="input"
            placeholder="https://open.spotify.com/track/..."
            value={url}
            onChange={e => setUrl(e.target.value)}
            required
          />
        </div>
        
        <div className={styles.field}>
          <label className="label">New Playlist Name (Optional)</label>
          <input
            type="text"
            className="input"
            placeholder="Track Recommendations"
            value={name}
            onChange={e => setName(e.target.value)}
          />
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !url}
          style={{ alignSelf: 'flex-start' }}
        >
          {loading ? <Loader2 size={18} className="spin" /> : <Music2 size={18} />}
          {loading ? 'Generating…' : 'Generate Playlist'}
        </button>
      </form>

      {result && (
        <div className={`${styles.result} slide-up`}>
          <h2 className={styles.resultTitle}>Playlist Created</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>Successfully generated <strong style={{color:'var(--text)'}}>{result.track_count}</strong> tracks.</p>
          <a href={result.playlist_url} target="_blank" rel="noreferrer" className="btn btn-secondary">
            <ExternalLink size={18} /> Open in Spotify
          </a>
        </div>
      )}
    </main>
  )
}
