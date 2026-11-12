import { useState } from 'react'
import { Music2, Loader2, AudioLines } from 'lucide-react'
import { ToastContext } from '../toast'
import { api, isSpotifyLink } from '../api'
import ResultCard from '../components/ResultCard'
import styles from './FeaturePage.module.css'

export default function TrackToPlaylistPage() {
  const [url, setUrl] = useState('')
  const [name, setName] = useState('')
  const [count, setCount] = useState(50)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const useNowPlaying = async () => {
    try {
      const d = await api('/api/now-playing')
      if (!d.playing || d.track?.type === 'episode' || !d.track?.url) {
        ToastContext.push('Nothing is playing right now', 'error')
        return
      }
      setUrl(d.track.url)
    } catch (e) {
      ToastContext.push(e.message, 'error')
    }
  }

  const submit = async (e) => {
    e.preventDefault()
    if (!isSpotifyLink(url, 'track')) {
      ToastContext.push('Paste a Spotify track link', 'error')
      return
    }
    setLoading(true)
    setResult(null)
    try {
      const d = await api('/api/track-to-playlist', {
        method: 'POST',
        body: { track_url: url.trim(), playlist_name: name || null, track_count: count },
      })
      setResult(d)
      ToastContext.push('Radio ready!', 'success')
    } catch (err) {
      ToastContext.push(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className={`${styles.page} page-enter`}>
      <header className={styles.header}>
        <h1 className={styles.title}>Track Radio</h1>
        <p className={styles.subtitle}>
          Drop one track. We dig through thousands of listener playlists that feature it, find the songs that keep showing up next to it, and build a radio around the seed.
        </p>
      </header>

      <form onSubmit={submit} className={styles.form}>
        <div className={styles.field}>
          <label className="label">Seed Track URL</label>
          <input
            type="text"
            className="input"
            placeholder="https://open.spotify.com/track/..."
            value={url}
            onChange={e => setUrl(e.target.value)}
            required
          />
          <button type="button" className="btn btn-ghost" style={{ alignSelf: 'flex-start' }} onClick={useNowPlaying}>
            <AudioLines size={16} /> Use what's playing
          </button>
        </div>

        <div className={styles.field}>
          <label className="label">New Playlist Name (Optional)</label>
          <input
            type="text"
            className="input"
            placeholder="<Track> Radio"
            value={name}
            onChange={e => setName(e.target.value)}
          />
        </div>

        <div className={styles.field}>
          <label className="label">Length ({count} Tracks)</label>
          <div className={styles.sliderContainer}>
            <input type="range" min="10" max="100" step="5" value={count} onChange={e => setCount(Number(e.target.value))} className={styles.slider} />
            <span className={styles.sliderValue}>{count}</span>
          </div>
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading || !url} style={{ alignSelf: 'flex-start' }}>
          {loading ? <Loader2 size={18} className="spin" /> : <Music2 size={18} />}
          {loading ? 'Tuning in…' : 'Build Radio'}
        </button>
      </form>

      {result && (
        <ResultCard title="Radio Ready" tracks={result.tracks} total={result.track_count} url={result.playlist_url} accent="#6c63ff">
          <strong>{result.track_count}</strong> tracks built around <strong>{result.seed?.name}</strong> by {result.seed?.artists}.
        </ResultCard>
      )}
    </main>
  )
}
