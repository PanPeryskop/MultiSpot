import { useEffect, useState, useRef } from 'react'
import { Play, Pause, SkipForward, SkipBack, X } from 'lucide-react'
import { ToastContext } from '../toast'
import { api } from '../api'
import styles from './NowPlayingModal.module.css'

export default function NowPlayingModal({ onClose }) {
  const [data, setData] = useState(null)
  const [queue, setQueue] = useState([])
  const [loading, setLoading] = useState(false)
  const modalRef = useRef(null)

  const fetchState = () => {
    api('/api/now-playing')
      .then(d => setData(d.playing ? d : null))
      .catch(() => {})
  }

  const fetchQueue = () => {
    api('/api/queue')
      .then(d => setQueue(d.queue || []))
      .catch(() => setQueue([]))
  }

  useEffect(() => {
    fetchState()
    fetchQueue()
    const id = setInterval(fetchState, 3000)
    return () => clearInterval(id)
  }, [])

  const trackId = data?.track?.id
  useEffect(() => {
    if (trackId) fetchQueue()
  }, [trackId])

  useEffect(() => {
    const handler = (e) => {
      if (modalRef.current && !modalRef.current.contains(e.target)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onClose])

  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  const handleAction = async (endpoint) => {
    setLoading(true)
    try {
      await api(endpoint, { method: 'POST' })
      setTimeout(fetchState, 500)
    } catch (e) {
      ToastContext.push(e.message, 'error')
    } finally {
      setTimeout(() => setLoading(false), 800)
    }
  }

  if (!data) {
    return (
      <div className={styles.overlay}>
        <div className={styles.modal} ref={modalRef}>
          <button className={styles.closeBtn} onClick={onClose}><X size={24} /></button>
          <div className={styles.emptyState}>Nothing is playing right now.</div>
        </div>
      </div>
    )
  }

  const { track, is_playing } = data
  const progress = track.duration_ms ? Math.min(100, Math.round((track.progress_ms / track.duration_ms) * 100)) : 0

  const formatTime = (ms) => {
    const totalSeconds = Math.floor(ms / 1000)
    const minutes = Math.floor(totalSeconds / 60)
    const seconds = totalSeconds % 60
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  return (
    <div className={styles.overlay}>
      <div className={styles.modal} ref={modalRef}>
        <button className={styles.closeBtn} onClick={onClose} aria-label="Close">
          <X size={24} />
        </button>
        
        <div className={styles.artworkContainer}>
          {track.image ? (
            <img src={track.image} alt={track.album} className={styles.artwork} />
          ) : (
            <div className={styles.artworkPlaceholder} />
          )}
        </div>

        <div className={styles.trackInfo}>
          <h2 className={styles.trackName}>{track.name}</h2>
          <p className={styles.artistName}>{track.artists.join(', ')}</p>
        </div>

        <div className={styles.progressContainer}>
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: `${progress}%` }} />
          </div>
          <div className={styles.timeRow}>
            <span>{formatTime(track.progress_ms)}</span>
            <span>{formatTime(track.duration_ms)}</span>
          </div>
        </div>

        <div className={styles.controls}>
          <button 
            className={styles.controlBtn} 
            onClick={() => handleAction('/api/playback/previous')}
            disabled={loading}
          >
            <SkipBack size={28} />
          </button>
          
          <button 
            className={`${styles.controlBtn} ${styles.playPauseBtn}`} 
            onClick={() => handleAction(is_playing ? '/api/playback/pause' : '/api/playback/play')}
            disabled={loading}
          >
            {is_playing ? <Pause size={32} /> : <Play size={32} style={{ marginLeft: 4 }} />}
          </button>

          <button 
            className={styles.controlBtn} 
            onClick={() => handleAction('/api/playback/skip')}
            disabled={loading}
          >
            <SkipForward size={28} />
          </button>
        </div>

        {queue.length > 0 && (
          <div className={styles.upNext}>
            <div className={styles.upNextTitle}>Up next</div>
            {queue.slice(0, 8).map((t, i) => (
              <div key={`${t.id}-${i}`} className={styles.upNextRow} style={{ animationDelay: `${0.04 * i}s` }}>
                {t.image ? <img src={t.image} alt="" /> : <div className={styles.upNextCover} />}
                <div className={styles.upNextMeta}>
                  <span className={styles.upNextName}>{t.name}</span>
                  <span className={styles.upNextArtist}>{t.artists.join(', ')}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
