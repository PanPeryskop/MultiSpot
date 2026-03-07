import { useState } from 'react'
import { BarChart2, Loader2, Music2, ExternalLink, Calendar, Disc, Users, Clock, Star } from 'lucide-react'
import { ToastContext } from '../App'
import featureStyles from './FeaturePage.module.css'
import styles from './TrackStatsPage.module.css'

export default function TrackStatsPage() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const submit = async () => {
    setLoading(true)
    setResult(null)
    try {
      const r = await fetch(`/api/track-stats?track_url=${encodeURIComponent(url)}`, {
        credentials: 'include'
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Something went wrong')
      setResult(d)
    } catch (e) {
      ToastContext.push(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const formatDuration = (ms) => {
    const minutes = Math.floor(ms / 60000)
    const seconds = ((ms % 60000) / 1000).toFixed(0)
    return minutes + ":" + (seconds < 10 ? '0' : '') + seconds
  }

  return (
    <main className={`${featureStyles.page} page-enter`}>
      <header className={featureStyles.header}>
        <h1 className={featureStyles.title}>Track Stats</h1>
        <p className={featureStyles.subtitle}>Analyze a Spotify track to view detailed statistics, popularity metrics, and artist information.</p>
      </header>
      <div className={featureStyles.form}>
        <div className={featureStyles.field}>
          <label className="label">Spotify Track URL</label>
          <input
            className="input"
            type="url"
            placeholder="https://open.spotify.com/track/..."
            value={url}
            onChange={e => setUrl(e.target.value)}
          />
        </div>
        <button className="btn btn-primary" onClick={submit} disabled={loading || !url} style={{ alignSelf: 'flex-start' }}>
          {loading ? <Loader2 size={18} className="spin" /> : <BarChart2 size={18} />}
          {loading ? 'Analyzing…' : 'Analyze Track'}
        </button>
      </div>
      {result && (
        <div className="slide-up" style={{ marginTop: 40, width: '100%', maxWidth: 640 }}>
          <div className={styles.mainCard}>
            {result.album.image ? (
              <img src={result.album.image} alt="Album Art" className={styles.albumImage} />
            ) : (
              <div className={styles.albumPlaceholder} />
            )}
            <div className={styles.trackDetails}>
              <div className={styles.trackLabel}>Track</div>
              <h2 className={styles.trackName}>{result.track.name}</h2>
              <div className={styles.trackMetrics}>
                <span className={styles.metricBadge}><Clock size={16} color="var(--green)" /> {formatDuration(result.track.duration_ms)}</span>
                <span className={styles.metricBadge}><Star size={16} color="var(--yellow)" /> {result.track.popularity} Popularity</span>
                {result.track.explicit && <span className={styles.metricBadge}><strong style={{ color: 'var(--red)' }}>EXPLICIT</strong></span>}
              </div>
            </div>
          </div>
          <div className={styles.subGrid}>
            <div className={styles.subCard}>
              <h3 className={styles.subCardHeader}><Disc size={18} /> Album Details</h3>
              <p style={{ margin: '0 0 8px 0', fontSize: 14 }}><strong>{result.album.name}</strong></p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 13, color: 'var(--text-secondary)' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Calendar size={14} /> Released: {result.album.release_date}</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Music2 size={14} /> Total Tracks: {result.album.total_tracks}</span>
                {result.album.label && <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span style={{fontWeight: 'bold'}}>LBL</span> {result.album.label}</span>}
              </div>
            </div>
            <div className={styles.subCard}>
              <h3 className={styles.subCardHeader}><Users size={18} /> Artists ({result.artists.length})</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {result.artists.map((artist, idx) => (
                  <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <div style={{ fontWeight: 700, fontSize: 15 }}>{artist.name}</div>
                    <div style={{ display: 'flex', gap: 12, fontSize: 12, color: 'var(--text-secondary)' }}>
                      <span>Popularity: {artist.popularity}</span>
                      <span>Followers: {artist.followers.toLocaleString()}</span>
                    </div>
                    {artist.genres && artist.genres.length > 0 && (
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{artist.genres.slice(0, 3).join(', ')}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}
