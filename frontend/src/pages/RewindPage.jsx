import { useEffect, useState } from 'react'
import { History, Loader2 } from 'lucide-react'
import { ToastContext } from '../toast'
import { api } from '../api'
import ResultCard from '../components/ResultCard'
import styles from './FeaturePage.module.css'

const SOURCES = [
  { value: 'recent', label: 'Recently played', hint: 'Your last 50 plays' },
  { value: 'short_term', label: 'Last 4 weeks', hint: 'Current heavy rotation' },
  { value: 'medium_term', label: 'Last 6 months', hint: 'This season of you' },
  { value: 'long_term', label: 'All time', hint: 'Your forever favourites' },
]

export default function RewindPage() {
  const [source, setSource] = useState('short_term')
  const [count, setCount] = useState(50)
  const [name, setName] = useState('')
  const [preview, setPreview] = useState([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    if (source === 'recent') {
      api('/api/fusion-suggestions')
        .then(d => setPreview((d.recent_tracks || []).slice(0, 6)))
        .catch(() => setPreview([]))
      return
    }
    api(`/api/top-tracks?limit=6&time_range=${source}`)
      .then(d => setPreview(d.tracks || []))
      .catch(() => setPreview([]))
  }, [source])

  const submit = async () => {
    setLoading(true)
    setResult(null)
    try {
      const d = await api('/api/rewind', { method: 'POST', body: { source, count, playlist_name: name || null } })
      setResult(d)
      ToastContext.push('Rewind saved!', 'success')
    } catch (e) {
      ToastContext.push(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const current = SOURCES.find(s => s.value === source)

  return (
    <main className={`${styles.page} page-enter`}>
      <header className={styles.header}>
        <h1 className={styles.title}>Rewind</h1>
        <p className={styles.subtitle}>Freeze a moment of your listening into a playlist: what you played today, this month, this year or ever.</p>
      </header>

      <div className={styles.form}>
        <div className={styles.field}>
          <label className="label">Snapshot</label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10 }}>
            {SOURCES.map(s => (
              <button
                key={s.value}
                type="button"
                onClick={() => setSource(s.value)}
                className={`btn ${s.value === source ? 'btn-primary' : 'btn-ghost'}`}
                style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 4, textAlign: 'left', transform: s.value === source ? 'translate(-2px,-2px)' : 'none' }}
              >
                <span>{s.label}</span>
                <span style={{ fontSize: 10, opacity: 0.7, textTransform: 'none', letterSpacing: 0 }}>{s.hint}</span>
              </button>
            ))}
          </div>
        </div>

        {preview.length > 0 && (
          <div key={source} className="fade-in" style={{ display: 'flex', gap: 8, overflow: 'hidden' }}>
            {preview.map(t => (
              t.image ? <img key={t.id} src={t.image} alt={t.name} title={`${t.name} - ${t.artists.join(', ')}`} style={{ width: 64, height: 64, objectFit: 'cover', border: '2px solid var(--border-dim)' }} /> : null
            ))}
          </div>
        )}

        <div className={styles.field}>
          <label className="label">Playlist Name</label>
          <input className="input" value={name} placeholder={`Rewind: ${current.label}`} onChange={e => setName(e.target.value)} />
        </div>

        {source !== 'recent' && (
          <div className={styles.field}>
            <label className="label">Tracks ({count})</label>
            <div className={styles.sliderContainer}>
              <input type="range" min="10" max="100" step="5" value={count} onChange={e => setCount(Number(e.target.value))} className={styles.slider} />
              <span className={styles.sliderValue}>{count}</span>
            </div>
          </div>
        )}

        <button className="btn btn-primary" onClick={submit} disabled={loading} style={{ alignSelf: 'flex-start' }}>
          {loading ? <Loader2 size={18} className="spin" /> : <History size={18} />}
          {loading ? 'Rewinding…' : 'Save Snapshot'}
        </button>
      </div>

      {result && (
        <ResultCard title="Snapshot Saved" tracks={result.tracks} total={result.track_count} url={result.playlist_url} accent="var(--purple)">
          <strong>{result.track_count}</strong> tracks from <strong>{current.label.toLowerCase()}</strong>.
        </ResultCard>
      )}
    </main>
  )
}
