import { useState, useEffect } from 'react'
import { Wand2, Loader2, ExternalLink } from 'lucide-react'
import { ToastContext } from '../App'
import featureStyles from './FeaturePage.module.css'
import styles from './MagicRecommenderPage.module.css'

export default function MagicRecommenderPage() {
  const [name, setName] = useState('')
  const [count, setCount] = useState(25)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  
  const [topTracks, setTopTracks] = useState([])
  const [topLoading, setTopLoading] = useState(true)

  useEffect(() => {
    fetch('/api/top-tracks?limit=12')
      .then(r => r.json())
      .then(d => { if (d.tracks) setTopTracks(d.tracks) })
      .finally(() => setTopLoading(false))
  }, [])

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)
    try {
      const r = await fetch('/api/magic-recommender', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playlist_name: name || 'Magic Mix', track_count: count }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Something went wrong')
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
        <h1 className={featureStyles.title}>Magic Recommender</h1>
        <p className={featureStyles.subtitle}>
          One click to generate a custom playlist based on your recent heavy rotation. We extract the essence of your top tracks and find the perfect follow-ups.
        </p>
      </header>

      <form onSubmit={submit} className={featureStyles.form}>
        <div className={featureStyles.field}>
          <label className="label">New Playlist Name</label>
          <input
            className="input"
            placeholder="Magic Mix"
            value={name}
            onChange={e => setName(e.target.value)}
          />
        </div>

        <div className={featureStyles.field}>
          <label className="label">Number of Tracks ({count})</label>
          <div className={featureStyles.sliderContainer}>
            <input
              type="range"
              min="5" max="100"
              value={count}
              onChange={e => setCount(Number(e.target.value))}
              className={featureStyles.slider}
            />
            <span className={featureStyles.sliderValue}>{count}</span>
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || topTracks.length === 0}
          style={{ alignSelf: 'flex-start' }}
        >
          {loading ? <Loader2 size={18} className="spin" /> : <Wand2 size={18} />}
          {loading ? 'Generating…' : 'Cast Magic'}
        </button>
      </form>

      {result && (
        <div className={`${featureStyles.result} slide-up`}>
          <h2 className={featureStyles.resultTitle}>Magic Manifested</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>Successfully generated <strong style={{color:'var(--text)'}}>{result.track_count}</strong> tracks into a new playlist.</p>
          <a href={result.playlist_url} target="_blank" rel="noreferrer" className="btn btn-secondary">
            <ExternalLink size={18} /> Open in Spotify
          </a>
        </div>
      )}

      <div style={{ marginTop: 80 }}>
        <h3 className="label" style={{ marginBottom: 24, borderBottom: '2px solid var(--border-dim)', paddingBottom: 12 }}>Your Current Seed Material (Top Tracks)</h3>
        {topLoading ? (
          <div style={{ color: 'var(--text-secondary)' }}>Loading top tracks...</div>
        ) : topTracks.length === 0 ? (
          <div style={{ color: 'var(--text-secondary)' }}>Not enough listening history.</div>
        ) : (
          <div className={styles.tracksGrid}>
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
