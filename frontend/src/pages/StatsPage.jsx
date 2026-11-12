import { useState, useEffect } from 'react'
import { BarChart3, Loader2, Clock, ExternalLink, Users } from 'lucide-react'
import { ToastContext } from '../toast'
import { api, compact, formatDuration } from '../api'
import featureStyles from './FeaturePage.module.css'
import styles from './StatsPage.module.css'

export default function StatsPage() {
  const [timeRange, setTimeRange] = useState('medium_term')
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({ tracks: null, artists: null, genres: null, tagged: 0, totalArtists: 0 })

  useEffect(() => {
    let alive = true
    Promise.all([
      api(`/api/top-tracks?limit=50&time_range=${timeRange}`),
      api(`/api/top-artists?limit=50&time_range=${timeRange}`),
      api(`/api/top-genres?limit=20&time_range=${timeRange}`),
    ])
      .then(([dTracks, dArtists, dGenres]) => {
        if (!alive) return
        setStats({ tracks: dTracks.tracks, artists: dArtists.artists, genres: dGenres.genres, tagged: dGenres.artists_tagged, totalArtists: dGenres.artists_total })
      })
      .catch(e => alive && ToastContext.push(e.message, 'error'))
      .finally(() => alive && setLoading(false))
    return () => { alive = false }
  }, [timeRange])

  const changeRange = (value) => {
    if (value === timeRange) return
    setLoading(true)
    setTimeRange(value)
  }

  const getPopularityColor = (pop) => {
    if (pop === null || pop === undefined) return 'var(--text-secondary)'
    if (pop >= 80) return 'var(--green)'
    if (pop >= 50) return 'var(--yellow)'
    return 'var(--red)'
  }

  return (
    <main className={`${featureStyles.page} page-enter`} style={{ maxWidth: 1200 }}>
      <header className={featureStyles.header}>
        <h1 className={featureStyles.title}>Stats Hub</h1>
        <p className={featureStyles.subtitle}>
          Dive deep into your listening habits. Explore your top tracks, top artists, and musical DNA breakdown.
        </p>
      </header>

      <div className={styles.statsControls}>
        <div className={styles.tabsContainer}>
          {['overview', 'tracks', 'artists'].map(tab => (
            <button 
              key={tab}
              className={`btn ${styles.tabBtn}`}
              style={{ 
                background: activeTab === tab ? 'var(--green)' : 'var(--surface)',
                color: activeTab === tab ? 'var(--black)' : 'var(--text)',
                borderColor: 'var(--black)',
                textTransform: 'capitalize'
              }}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className={featureStyles.field} style={{ margin: 0 }}>
          <label className="label">Time Period</label>
          <select className={`input ${styles.timeSelect}`} value={timeRange} onChange={e => changeRange(e.target.value)}>
            <option value="short_term">Past Month</option>
            <option value="medium_term">Past 6 Months</option>
            <option value="long_term">All Time</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}><Loader2 size={48} className="spin" style={{ color: 'var(--green)' }} /></div>
      ) : (
        <div className="fade-in">
          {activeTab === 'overview' && stats.tracks && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 40 }}>
              
              <div className={styles.overviewGrid}>
                <div className={styles.overviewCard}>
                  <h3 className={`${styles.overviewCardHeader} ${styles.artistHeader}`}>Top Artist</h3>
                  {stats.artists.length > 0 && (
                     <div className={styles.overviewContent}>
                       {stats.artists[0].image ? <img src={stats.artists[0].image} alt="" className={styles.overviewImg} /> : <div className={styles.overviewImg} />}
                       <div>
                         <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--green)' }}>{stats.artists[0].name}</div>
                         {stats.artists[0].popularity !== null && stats.artists[0].popularity !== undefined && <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>★ {stats.artists[0].popularity} Popularity</div>}
                       </div>
                     </div>
                  )}
                </div>

                <div className={styles.overviewCard}>
                  <h3 className={`${styles.overviewCardHeader} ${styles.trackHeader}`}>Top Track</h3>
                   {stats.tracks.length > 0 && (
                     <div className={styles.overviewContent}>
                       {stats.tracks[0].image ? <img src={stats.tracks[0].image} alt="" className={styles.overviewImg} /> : <div className={styles.overviewImg} />}
                       <div style={{ flex: 1, minWidth: 0 }}>
                         <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--yellow)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{stats.tracks[0].name}</div>
                         <div style={{ fontSize: 16, color: 'var(--text)' }}>{stats.tracks[0].artists.join(', ')}</div>
                       </div>
                     </div>
                  )}
                </div>
              </div>

              <div>
                <h3 style={{ fontSize: 24, fontWeight: 800, textTransform: 'uppercase', marginBottom: 24, display: 'flex', alignItems: 'center', gap: 12 }}>
                  <BarChart3 size={24} color="var(--purple)" /> DNA Breakdown (Top Genres)
                </h3>
                {stats.genres.length === 0 ? (
                  <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Spotify has stopped tagging most artists with genres, so there is nothing to break down for this period.</p>
                ) : (
                  <>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                      {stats.genres.map((g, idx) => (
                        <div key={g.name} style={{ display: 'flex', alignItems: 'center', background: 'var(--surface)', border: '2px solid var(--black)', fontSize: 14 }}>
                          <div style={{ background: 'var(--purple)', color: 'var(--black)', fontWeight: 800, padding: '8px 12px', borderRight: '2px solid var(--black)' }}>#{idx + 1}</div>
                          <div style={{ padding: '8px 16px', fontWeight: 600, textTransform: 'uppercase' }}>{g.name}</div>
                          <div style={{ padding: '8px 12px', color: 'var(--text-secondary)', borderLeft: '2px solid var(--black)' }}>×{g.count}</div>
                        </div>
                      ))}
                    </div>
                    {stats.totalArtists > 0 && stats.tagged < stats.totalArtists && (
                      <p style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 16 }}>Based on {stats.tagged} of your top {stats.totalArtists} artists. Spotify no longer lists genres for the rest.</p>
                    )}
                  </>
                )}
              </div>

            </div>
          )}

          {activeTab === 'tracks' && stats.tracks && (
            <div className={styles.tracksGrid}>
              {stats.tracks.map((t, idx) => (
                <div key={t.id} style={{ display: 'flex', flexDirection: 'column', background: 'var(--surface-2)', border: '2px solid var(--border-dim)', transition: 'var(--transition)', overflow: 'hidden' }} onMouseOver={e => Object.assign(e.currentTarget.style, { borderColor: 'var(--green)', transform: 'translate(-2px,-2px)', boxShadow: '6px 6px 0 var(--green)' })} onMouseOut={e => Object.assign(e.currentTarget.style, { borderColor: 'var(--border-dim)', transform: 'none', boxShadow: 'none' })}>
                  <div style={{ padding: 16, display: 'flex', gap: 16, borderBottom: '2px solid var(--border-dim)' }}>
                    <div style={{ position: 'relative' }}>
                      <div style={{ position: 'absolute', top: -8, left: -8, width: 24, height: 24, background: 'var(--green)', color: 'var(--black)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: 13, border: '2px solid var(--black)', zIndex: 1 }}>{idx + 1}</div>
                      {t.image ? <img src={t.image} alt="" style={{ width: 64, height: 64, border: '2px solid var(--black)', objectFit: 'cover' }} /> : <div style={{ width: 64, height: 64, background: 'var(--black)' }} />}
                    </div>
                    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                      <div style={{ fontSize: 16, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: 'var(--text)', marginBottom: 4 }}>{t.name}</div>
                      <div style={{ fontSize: 13, color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{t.artists.join(', ')}</div>
                    </div>
                  </div>
                  <div style={{ padding: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--surface)', fontSize: 13 }}>
                    <div style={{ display: 'flex', gap: 12 }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-secondary)' }}><Clock size={14} /> {formatDuration(t.duration_ms)}</span>
                      {t.popularity !== null && t.popularity !== undefined && <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: getPopularityColor(t.popularity), fontWeight: 'bold' }}>★ {t.popularity}</span>}
                      {t.explicit && <span style={{ color: 'var(--red)', fontWeight: 'bold' }}>EXP</span>}
                    </div>
                    <a href={t.url} target="_blank" rel="noreferrer" style={{ color: 'var(--text)', display: 'flex', alignItems: 'center' }}>
                      <ExternalLink size={16} />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'artists' && stats.artists && (
            <div className={styles.artistsGrid}>
               {stats.artists.map((a, idx) => (
                 <div key={a.id} style={{ background: 'var(--surface-2)', border: '2px solid var(--border-dim)', padding: 24, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', transition: 'var(--transition)' }} onMouseOver={e => Object.assign(e.currentTarget.style, { borderColor: 'var(--yellow)', transform: 'translate(-2px,-2px)', boxShadow: '6px 6px 0 var(--yellow)' })} onMouseOut={e => Object.assign(e.currentTarget.style, { borderColor: 'var(--border-dim)', transform: 'none', boxShadow: 'none' })}>
                   <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--yellow)', marginBottom: 16 }}>#{idx + 1}</div>
                   <div style={{ position: 'relative', marginBottom: 16 }}>
                     {a.image ? <img src={a.image} alt="" style={{ width: 120, height: 120, borderRadius: '50%', border: '4px solid var(--black)', objectFit: 'cover' }} /> : <div style={{ width: 120, height: 120, borderRadius: '50%', background: 'var(--black)' }} />}
                   </div>
                   <h4 style={{ fontSize: 18, fontWeight: 700, margin: '0 0 8px 0', color: 'var(--text)' }}>{a.name}</h4>
                   <div style={{ display: 'flex', gap: 16, fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
                     {a.followers !== null && a.followers !== undefined && <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Users size={14} /> {compact(a.followers)}</span>}
                     {a.popularity !== null && a.popularity !== undefined && <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: getPopularityColor(a.popularity), fontWeight: 'bold' }}>★ {a.popularity}</span>}
                   </div>
                   <a href={a.url} target="_blank" rel="noreferrer" className="btn" style={{ width: '100%', justifyContent: 'center', background: 'var(--surface)', border: '2px solid var(--black)' }}>View Spotify <ExternalLink size={14} /></a>
                 </div>
               ))}
            </div>
          )}
        </div>
      )}
    </main>
  )
}
