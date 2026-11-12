import { useState } from 'react'
import { Radio, Loader2, Link2 } from 'lucide-react'
import { ToastContext } from '../toast'
import { api } from '../api'
import GenrePicker from '../components/GenrePicker'
import ResultCard from '../components/ResultCard'
import featureStyles from './FeaturePage.module.css'
import styles from './RandomHubPage.module.css'

export default function RandomHubPage() {
  const [count, setCount] = useState(20)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [action, setAction] = useState('queue')
  const [genre, setGenre] = useState(null)
  const [playlistName, setPlaylistName] = useState('')

  const submit = async () => {
    setLoading(true)
    setResult(null)
    const endpoint = action === 'queue' ? '/api/random-hub/queue' : '/api/random-hub/playlist'
    const body = { count, genre, playlist_name: action === 'playlist' ? playlistName || null : null }
    try {
      const d = await api(endpoint, { method: 'POST', body })
      setResult({ ...d, action, genre })
      ToastContext.push(action === 'queue' ? `Queued ${d.added} tracks` : `Created playlist with ${d.track_count} tracks`, 'success')
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
          Leave the genre empty and every track comes from a different random genre out of 6000+. Pick one genre to spin up a station that sticks to it.
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

        <div className={featureStyles.field}>
          <label className="label">Genre (optional)</label>
          <GenrePicker value={genre} onChange={setGenre} />
        </div>

        {action === 'playlist' && (
          <div className={`${featureStyles.field} slide-up`}>
            <label className="label">Playlist Name</label>
            <input
              type="text"
              className="input"
              value={playlistName}
              placeholder={genre ? `${genre} Roulette` : 'Random Hub'}
              onChange={e => setPlaylistName(e.target.value)}
            />
          </div>
        )}

        <div className={featureStyles.field}>
          <label className="label">Number of Tracks ({count})</label>
          <div className={featureStyles.sliderContainer}>
            <input
              type="range"
              min="1"
              max={action === 'queue' ? 100 : 200}
              value={count}
              onChange={e => setCount(Number(e.target.value))}
              className={featureStyles.slider}
            />
            <span className={featureStyles.sliderValue}>{count}</span>
          </div>
        </div>

        <button className="btn btn-primary" onClick={submit} disabled={loading} style={{ alignSelf: 'flex-start' }}>
          {loading ? <Loader2 size={18} className="spin" /> : action === 'queue' ? <Radio size={18} /> : <Link2 size={18} />}
          {loading ? 'Rolling the dice…' : action === 'queue' ? 'Inject Tracks' : 'Create Playlist'}
        </button>
      </div>

      {result && (
        <ResultCard
          title={result.action === 'queue' ? 'Injection Complete' : 'Playlist Created'}
          tracks={result.tracks || []}
          total={result.action === 'queue' ? result.added : result.track_count}
          url={result.playlist_url}
        >
          {result.action === 'queue' ? (
            <>Added <strong>{result.added}</strong> tracks to your queue{result.errors > 0 && `, ${result.errors} skipped`}.</>
          ) : (
            <>Saved <strong>{result.track_count}</strong> tracks{result.genre ? <> of <strong>{result.genre}</strong></> : ''} to a new playlist.</>
          )}
        </ResultCard>
      )}
    </main>
  )
}
