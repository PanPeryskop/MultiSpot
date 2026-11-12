import { useState, useEffect } from 'react'
import styles from './NowPlaying.module.css'

export default function NowPlaying() {
  const [data, setData] = useState(null)

  useEffect(() => {
    const fetch_ = () => {
      if (document.hidden) return
      fetch('/api/now-playing', { credentials: 'include' })
        .then(r => (r.ok ? r.json() : { playing: false }))
        .then(d => setData(d.playing ? d : null))
        .catch(() => {})
    }

    fetch_()
    const id = setInterval(fetch_, 8000)
    return () => clearInterval(id)
  }, [])

  if (!data) return null

  const { track } = data
  const progress = track.duration_ms ? Math.min(100, Math.round((track.progress_ms / track.duration_ms) * 100)) : 0

  return (
    <div className={styles.container}>
      {track.image && <img src={track.image} alt={track.album} className={styles.cover} />}
      <div className={styles.info}>
        <span className={styles.name}>{track.name}</span>
        <span className={styles.artist}>{track.artists.join(', ')}</span>
        <div className={styles.bar}>
          <div className={styles.barFill} style={{ width: `${progress}%` }} />
        </div>
      </div>
    </div>
  )
}
