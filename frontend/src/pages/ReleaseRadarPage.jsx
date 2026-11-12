import { useEffect, useState } from 'react'
import { Radar, Loader2, ListPlus, RefreshCw } from 'lucide-react'
import { ToastContext } from '../toast'
import { api } from '../api'
import ResultCard from '../components/ResultCard'
import featureStyles from './FeaturePage.module.css'
import styles from './NewFeatures.module.css'

const WINDOWS = [7, 14, 30]

export default function ReleaseRadarPage() {
  const [days, setDays] = useState(14)
  const [data, setData] = useState(null)
  const [scanning, setScanning] = useState(true)
  const [saving, setSaving] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    let alive = true
    api(`/api/release-radar?days=${days}`)
      .then(d => alive && setData(d))
      .catch(e => alive && ToastContext.push(e.message, 'error'))
      .finally(() => alive && setScanning(false))
    return () => { alive = false }
  }, [days])

  const pick = (value) => {
    if (value === days) return
    setScanning(true)
    setData(null)
    setDays(value)
  }

  const save = async () => {
    setSaving(true)
    setResult(null)
    try {
      setResult(await api('/api/release-radar', { method: 'POST', body: { days } }))
      ToastContext.push('Release Radar saved!', 'success')
    } catch (e) {
      ToastContext.push(e.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  const releases = data?.releases || []

  return (
    <main className={`${featureStyles.page} page-enter`} style={{ maxWidth: 1000 }}>
      <header className={featureStyles.header}>
        <h1 className={featureStyles.title}>Release Radar</h1>
        <p className={featureStyles.subtitle}>
          Fresh singles and albums from the artists you follow and play the most. Save them as a playlist or let Autopilot refresh it every Friday.
        </p>
      </header>

      <div className={styles.toolbar}>
        <div className={styles.segmented}>
          {WINDOWS.map(w => (
            <button key={w} className={w === days ? styles.segOn : ''} onClick={() => pick(w)}>
              Last {w} days
            </button>
          ))}
        </div>
        <button className="btn btn-primary" onClick={save} disabled={saving || scanning || releases.length === 0}>
          {saving ? <Loader2 size={18} className="spin" /> : <ListPlus size={18} />}
          {saving ? 'Saving…' : 'Save as playlist'}
        </button>
      </div>

      {scanning ? (
        <div className={styles.scanning}>
          <Radar size={42} className={styles.radarIcon} />
          <span>Scanning your artists…</span>
        </div>
      ) : releases.length === 0 ? (
        <div className={styles.empty}>
          <RefreshCw size={28} />
          <span>Nothing new from your {data?.artists_checked || 0} artists in the last {days} days.</span>
        </div>
      ) : (
        <>
          <p className={styles.meta}>{releases.length} releases from {data.artists_checked} artists</p>
          <div className={`${styles.releaseGrid} stagger`}>
            {releases.map(r => (
              <a key={r.id} href={r.url} target="_blank" rel="noreferrer" className={styles.release}>
                <div className={styles.releaseArt}>
                  {r.image ? <img src={r.image} alt="" loading="lazy" /> : <div />}
                  <span className={`${styles.badge} ${r.album_type === 'album' ? styles.badgeAlbum : ''}`}>{r.album_type}</span>
                </div>
                <div className={styles.releaseName}>{r.name}</div>
                <div className={styles.releaseSub}>{r.artists.join(', ')}</div>
                <div className={styles.releaseDate}>{r.release_date}{r.total_tracks > 1 ? ` · ${r.total_tracks} tracks` : ''}</div>
              </a>
            ))}
          </div>
        </>
      )}

      {result && (
        <ResultCard title="Radar Saved" tracks={result.tracks} total={result.track_count} url={result.playlist_url} accent="#ff8a3d">
          <strong>{result.track_count}</strong> new tracks from the last {days} days.
        </ResultCard>
      )}
    </main>
  )
}
