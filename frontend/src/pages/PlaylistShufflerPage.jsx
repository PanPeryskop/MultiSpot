import { useState } from 'react'
import { Shuffle, Loader2, ExternalLink } from 'lucide-react'
import { ToastContext } from '../App'
import styles from './FeaturePage.module.css'
import PlaylistPicker from '../components/PlaylistPicker'

export default function PlaylistShufflerPage() {
  const [selectedPlaylist, setSelectedPlaylist] = useState(null)
  const [manualUrl, setManualUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const submit = async () => {
    setLoading(true)
    setResult(null)
    const targetUrl = manualUrl.trim() || (selectedPlaylist ? selectedPlaylist.url : null)
    if (!targetUrl) return
    
    try {
      const r = await fetch('/api/playlist-shuffler', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playlist_url: targetUrl }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Something went wrong')
      setResult(d)
      ToastContext.push('Playlist shuffled successfully!', 'success')
      setSelectedPlaylist(null)
      setManualUrl('')
    } catch (e) {
      ToastContext.push(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className={`${styles.page} page-enter`}>
      <header className={styles.header}>
        <h1 className={styles.title}>Playlist Shuffler</h1>
        <p className={styles.subtitle}>
          Select a playlist below to true-shuffle it. We'll reconstruct the playlist in a perfectly randomized order so Spotify stops playing the same 10 songs.
        </p>
      </header>

      <div className={styles.form}>
        <div className={styles.field}>
          <label className="label">Manual Playlist URL</label>
          <input
            className="input"
            type="url"
            placeholder="https://open.spotify.com/playlist/..."
            value={manualUrl}
            onChange={e => {
              setManualUrl(e.target.value)
              if (e.target.value) setSelectedPlaylist(null)
            }}
          />
        </div>
        
        <div style={{ textAlign: 'center', fontWeight: 'bold', fontSize: 13, margin: '8px 0', color: 'var(--text-secondary)' }}>OR</div>

        <div className={styles.field}>
          <label className="label">Select from your Library</label>
          <PlaylistPicker 
            multi={false} 
            selected={selectedPlaylist ? [selectedPlaylist] : []} 
            onChange={v => {
              setSelectedPlaylist(v[0] || null)
              if (v[0]) setManualUrl('')
            }} 
          />
        </div>

        <button
          className="btn btn-primary"
          onClick={submit}
          disabled={loading || (!selectedPlaylist && !manualUrl.trim())}
          style={{ alignSelf: 'flex-start' }}
        >
          {loading ? <Loader2 size={18} className="spin" /> : <Shuffle size={18} />}
          {loading ? 'Shuffling…' : 'Shuffle Playlist'}
        </button>
      </div>

      {result && (
        <div className={`${styles.result} slide-up`}>
          <h2 className={styles.resultTitle}>Shuffled & Ready</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>Successfully shuffled <strong style={{color:'var(--text)'}}>{result.track_count}</strong> tracks.</p>
          <a href={result.playlist_url} target="_blank" rel="noreferrer" className="btn btn-secondary">
            <ExternalLink size={18} /> Open in Spotify
          </a>
        </div>
      )}
    </main>
  )
}
