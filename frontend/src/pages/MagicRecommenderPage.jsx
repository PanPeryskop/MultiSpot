import { useState, useEffect } from 'react'
import { Wand2, Loader2 } from 'lucide-react'
import { ToastContext } from '../toast'
import { api } from '../api'
import ResultCard from '../components/ResultCard'
import featureStyles from './FeaturePage.module.css'
import styles from './MagicRecommenderPage.module.css'

export default function MagicRecommenderPage() {
  const [name, setName] = useState('')
  const [count, setCount] = useState(30)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [topTracks, setTopTracks] = useState([])
  const [topLoading, setTopLoading] = useState(true)

  useEffect(() => {
    api('/api/top-tracks?limit=12&time_range=short_term')
      .then(d => setTopTracks(d.tracks || []))
      .catch(() => setTopTracks([]))
      .finally(() => setTopLoading(false))
  }, [])

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)
    try {
      const d = await api('/api/magic-recommender', {
        method: 'POST',
        body: { playlist_name: name || 'Magic Mix', track_count: count },
      })
      setResult(d)
      ToastContext.push('Magic mix generated!', 'success')
    } catch (err) {
      ToastContext.push(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className={`${featureStyles.page} page-enter`}>
      <header className={featureStyles.header}>
        <h1 className={featureStyles.title}>Magic Mix</h1>
        <p className={featureStyles.subtitle}>
          We pick a handful of your favourite artists and tracks, find what their fans play next to them and leave out what you already have on repeat. Every cast is different.
        </p>
      </header>

      <form onSubmit={submit} className={featureStyles.form}>
        <div className={featureStyles.field}>
          <label className="label">New Playlist Name</label>
          <input className="input" placeholder="Magic Mix" value={name} onChange={e => setName(e.target.value)} />
        </div>

        <div className={featureStyles.field}>
          <label className="label">Number of Tracks ({count})</label>
          <div className={featureStyles.sliderContainer}>
            <input type="range" min="5" max="100" value={count} onChange={e => setCount(Number(e.target.value))} className={featureStyles.slider} />
            <span className={featureStyles.sliderValue}>{count}</span>
          </div>
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading} style={{ alignSelf: 'flex-start' }}>
          {loading ? <Loader2 size={18} className="spin" /> : <Wand2 size={18} />}
          {loading ? 'Brewing…' : 'Cast Magic'}
        </button>
      </form>

      {result && (
        <ResultCard title="Magic Manifested" tracks={result.tracks} total={result.track_count} url={result.playlist_url} accent="#00b4d8">
          <strong>{result.track_count}</strong> fresh tracks.
          {result.seeds?.length > 0 && <> Seeded from <strong>{result.seeds.join(', ')}</strong>.</>}
        </ResultCard>
      )}

      <div style={{ marginTop: 80 }}>
        <h3 className="label" style={{ marginBottom: 24, borderBottom: '2px solid var(--border-dim)', paddingBottom: 12 }}>Your heavy rotation (last 4 weeks)</h3>
        {topLoading ? (
          <div style={{ color: 'var(--text-secondary)' }}>Loading top tracks...</div>
        ) : topTracks.length === 0 ? (
          <div style={{ color: 'var(--text-secondary)' }}>Not much recent history. We will lean on your recently played tracks.</div>
        ) : (
          <div className={`${styles.tracksGrid} stagger`}>
            {topTracks.map(t => (
              <a key={t.id} href={t.url} target="_blank" rel="noreferrer" className={styles.trackCard}>
                {t.image ? <img src={t.image} alt="" className={styles.trackImage} /> : <div className={styles.trackImagePlaceholder} />}
                <div className={styles.trackInfo}>
                  <div className={styles.trackName}>{t.name}</div>
                  <div className={styles.trackArtist}>{t.artists.join(', ')}</div>
                </div>
              </a>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
