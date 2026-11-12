import { useState } from 'react'
import { BarChart2, Loader2, Music2, ExternalLink, Calendar, Disc, Users, Clock, Star, Hash, AudioLines, ListOrdered } from 'lucide-react'
import { ToastContext } from '../toast'
import { api, compact, formatDuration, isSpotifyLink } from '../api'
import featureStyles from './FeaturePage.module.css'
import styles from './TrackStatsPage.module.css'

function Meter({ value, color = 'var(--green)' }) {
  if (value === null || value === undefined) return null
  return (
    <div className={styles.meter}>
      <div className={styles.meterFill} style={{ width: `${value}%`, background: color }} />
    </div>
  )
}

export default function TrackStatsPage() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const analyze = async (target = url) => {
    if (!isSpotifyLink(target, 'track')) {
      ToastContext.push('Paste a Spotify track link', 'error')
      return
    }
    setLoading(true)
    setResult(null)
    try {
      setResult(await api(`/api/track-stats?track_url=${encodeURIComponent(target.trim())}`))
    } catch (e) {
      ToastContext.push(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const useNowPlaying = async () => {
    try {
      const d = await api('/api/now-playing')
      if (!d.playing || !d.track?.url || d.track.type === 'episode') {
        ToastContext.push('Nothing is playing right now', 'error')
        return
      }
      setUrl(d.track.url)
      analyze(d.track.url)
    } catch (e) {
      ToastContext.push(e.message, 'error')
    }
  }

  const track = result?.track
  const album = result?.album
  const year = album?.release_date?.slice(0, 4)

  return (
    <main className={`${featureStyles.page} page-enter`}>
      <header className={featureStyles.header}>
        <h1 className={featureStyles.title}>Track X-Ray</h1>
        <p className={featureStyles.subtitle}>Release info, album context, popularity and the artists behind any track.</p>
      </header>
      <div className={featureStyles.form}>
        <div className={featureStyles.field}>
          <label className="label">Spotify Track URL</label>
          <input
            className="input"
            type="text"
            placeholder="https://open.spotify.com/track/..."
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && analyze()}
          />
        </div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={() => analyze()} disabled={loading || !url}>
            {loading ? <Loader2 size={18} className="spin" /> : <BarChart2 size={18} />}
            {loading ? 'Scanning…' : 'X-Ray It'}
          </button>
          <button className="btn btn-ghost" onClick={useNowPlaying} disabled={loading}>
            <AudioLines size={18} /> What's playing
          </button>
        </div>
      </div>

      {result && (
        <div className="slide-up" style={{ marginTop: 40, width: '100%' }}>
          <div className={styles.mainCard}>
            {album.image ? <img src={album.image} alt="" className={styles.albumImage} /> : <div className={styles.albumPlaceholder} />}
            <div className={styles.trackDetails}>
              <div className={styles.trackLabel}>{album.album_type || 'Track'}{year ? ` · ${year}` : ''}</div>
              <h2 className={styles.trackName}>{track.name}</h2>
              <div className={styles.trackMetrics}>
                <span className={styles.metricBadge}><Clock size={16} color="var(--green)" /> {formatDuration(track.duration_ms)}</span>
                {track.popularity !== null && track.popularity !== undefined && (
                  <span className={styles.metricBadge}><Star size={16} color="var(--yellow)" /> {track.popularity} / 100</span>
                )}
                {track.album_position && (
                  <span className={styles.metricBadge}><ListOrdered size={16} /> Track {track.album_position} of {album.total_tracks}</span>
                )}
                {track.explicit && <span className={styles.metricBadge}><strong style={{ color: 'var(--red)' }}>EXPLICIT</strong></span>}
                {track.playable === false && <span className={styles.metricBadge}><strong style={{ color: 'var(--red)' }}>NOT IN YOUR MARKET</strong></span>}
              </div>
              <Meter value={track.popularity} color="var(--yellow)" />
              {track.url && (
                <a href={track.url} target="_blank" rel="noreferrer" className={styles.openLink}>
                  Open in Spotify <ExternalLink size={14} />
                </a>
              )}
            </div>
          </div>

          <div className={styles.subGrid}>
            <div className={styles.subCard}>
              <h3 className={styles.subCardHeader}><Disc size={18} /> Album</h3>
              <p className={styles.albumName}>{album.name}</p>
              <div className={styles.facts}>
                <span><Calendar size={14} /> {album.release_date || 'Unknown date'}</span>
                <span><Music2 size={14} /> {album.total_tracks ?? '?'} tracks{album.duration_ms ? ` · ${formatDuration(album.duration_ms)}` : ''}</span>
                {album.label && <span><strong>LBL</strong> {album.label}</span>}
                {track.isrc && <span><Hash size={14} /> {track.isrc}</span>}
                {album.copyright && <span className={styles.muted}>© {album.copyright.replace(/^[©℗]\s*/, '')}</span>}
              </div>
              {album.tracks?.length > 0 && (
                <ol className={styles.tracklist}>
                  {album.tracks.map(t => (
                    <li key={`${t.number}-${t.name}`} className={t.current ? styles.currentTrack : ''}>
                      <span className={styles.trackNo}>{t.number}</span>
                      <span className={styles.trackTitle}>{t.name}</span>
                      <span className={styles.trackLen}>{formatDuration(t.duration_ms)}</span>
                    </li>
                  ))}
                </ol>
              )}
            </div>

            <div className={styles.subCard}>
              <h3 className={styles.subCardHeader}><Users size={18} /> Artists ({result.artists.length})</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                {result.artists.map(artist => (
                  <div key={artist.id} className={styles.artist}>
                    <div className={styles.artistHead}>
                      {artist.image ? <img src={artist.image} alt="" className={styles.artistImage} /> : <div className={styles.artistImage} />}
                      <div style={{ minWidth: 0 }}>
                        <a href={artist.url} target="_blank" rel="noreferrer" className={styles.artistName}>{artist.name}</a>
                        <div className={styles.artistStats}>
                          {artist.followers !== null && artist.followers !== undefined && <span>{compact(artist.followers)} followers</span>}
                          {artist.popularity !== null && artist.popularity !== undefined && <span>★ {artist.popularity}</span>}
                          {artist.albums_total !== null && artist.albums_total !== undefined && <span>{artist.albums_total} albums</span>}
                          {artist.singles_total !== null && artist.singles_total !== undefined && <span>{artist.singles_total} singles</span>}
                        </div>
                      </div>
                    </div>
                    <Meter value={artist.popularity} />
                    {artist.genres?.length > 0 && (
                      <div className={styles.genres}>
                        {artist.genres.slice(0, 5).map(g => <span key={g} className="tag tag-green">{g}</span>)}
                      </div>
                    )}
                    {artist.top_tracks?.length > 0 && (
                      <div className={styles.topTracks}>
                        <span className="label">Most played</span>
                        {artist.top_tracks.map((t, i) => (
                          <a key={t.url} href={t.url} target="_blank" rel="noreferrer" className={`${styles.topTrack} ${t.current ? styles.currentTrack : ''}`}>
                            <span className={styles.trackNo}>{i + 1}</span>
                            {t.image && <img src={t.image} alt="" />}
                            <span className={styles.trackTitle}>{t.name}</span>
                          </a>
                        ))}
                      </div>
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
