import { useState } from 'react'
import { Radio, Loader2, Link2 } from 'lucide-react'
import { ToastContext } from '../App'
import featureStyles from './FeaturePage.module.css'
import styles from './RandomHubPage.module.css'

export default function RandomHubPage() {
  const [count, setCount] = useState(15)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [action, setAction] = useState('queue')
  const [playlistName, setPlaylistName] = useState('Random Hub Collection')

  const submit = async () => {
    setLoading(true)
    setResult(null)
    const endpoint = action === 'queue' ? '/api/random-hub/queue' : '/api/random-hub/playlist'
    const bodyArgs = action === 'queue' ? { count } : { count, playlist_name: playlistName }

    try {
      const r = await fetch(endpoint, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyArgs),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Something went wrong')
      setResult({ ...d, action })
      if (action === 'queue') {
         ToastContext.push(`Queued ${d.added} tracks`, 'success')
      } else {
         ToastContext.push(`Created playlist with ${d.track_count} tracks`, 'success')
      }
    } catch (e) {
      ToastContext.push(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className={`${featureStyles.page} page-enter`} style={{ maxWidth: 1000 }}>
      <header className={featureStyles.header}>
        <h1 className={featureStyles.title}>Random Hub</h1>
        <p className={featureStyles.subtitle}>
          Discover new music. We pull random tracks across all of Spotify's genre classifications and let you inject them into your queue or spin up a new playlist.
        </p>
      </header>

      <div className={featureStyles.form}>
        
        <div className={featureStyles.field}>
          <label className="label">Destination</label>
          <div className={styles.radioGroup}>
            <label className={styles.radioLabel}>
              <input type="radio" name="action" checked={action === 'queue'} onChange={() => setAction('queue')} />
              <span>Add to Queue</span>
            </label>
            <label className={styles.radioLabel}>
              <input type="radio" name="action" checked={action === 'playlist'} onChange={() => setAction('playlist')} />
              <span>Create Playlist</span>
            </label>
          </div>
        </div>

        {action === 'playlist' && (
           <div className={`${featureStyles.field} slide-up`}>
             <label className="label">Playlist Name</label>
             <input type="text" className="input" value={playlistName} onChange={e => setPlaylistName(e.target.value)} />
           </div>
        )}

        <div className={featureStyles.field}>
          <label className="label">Number of Tracks ({count})</label>
          <div className={featureStyles.sliderContainer}>
            <input
              type="range"
              min="1" max="100"
              value={count}
              onChange={e => setCount(Number(e.target.value))}
              className={featureStyles.slider}
            />
            <span className={featureStyles.sliderValue}>{count}</span>
          </div>
        </div>

        <button
          className="btn btn-primary"
          onClick={submit}
          disabled={loading}
          style={{ alignSelf: 'flex-start' }}
        >
          {loading ? <Loader2 size={18} className="spin" /> : action === 'queue' ? <Radio size={18} /> : <Link2 size={18} />}
          {loading ? 'Working…' : action === 'queue' ? 'Inject Tracks' : 'Create Playlist'}
        </button>
      </div>

      {result && (
        <div className={`${featureStyles.result} slide-up`}>
          <h2 className={styles.resultTitle}>{result.action === 'queue' ? 'Injection Complete' : 'Playlist Created'}</h2>
          <p style={{ color: 'var(--text-secondary)' }}>
            {result.action === 'queue' ? (
                <>Added <strong style={{color:'var(--text)'}}>{result.added}</strong> tracks to your queue.</>
            ) : (
                <>Generated a playlist with <strong style={{color:'var(--text)'}}>{result.track_count}</strong> tracks.</>
            )}
            {result.errors > 0 && ` (Skipped ${result.errors} due to API issues)`}
          </p>
          {result.action === 'playlist' && result.playlist_url && (
            <a href={result.playlist_url} target="_blank" rel="noreferrer" className="btn btn-primary" style={{ marginTop: 16, display: 'inline-flex' }}>
              Open in Spotify
            </a>
          )}
        </div>
      )}
    </main>
  )
}
