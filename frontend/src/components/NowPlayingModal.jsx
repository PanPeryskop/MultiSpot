import { useEffect, useState, useRef } from 'react'
import { Play, Pause, SkipForward, SkipBack, X } from 'lucide-react'
import styles from './NowPlayingModal.module.css'

export default function NowPlayingModal({ onClose }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const modalRef = useRef(null)

  const fetchState = () => {
    fetch('/api/now-playing', { credentials: 'include' })
      .then(r => r.json())
      .then(d => setData(d.playing ? d : null))
      .catch(() => {})
  }

  useEffect(() => {
    fetchState()
    const id = setInterval(fetchState, 3000)
    return () => clearInterval(id)
  }, [])

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
      await fetch(endpoint, { method: 'POST', credentials: 'include' })
      setTimeout(fetchState, 500)
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
  const progress = Math.round((track.progress_ms / track.duration_ms) * 100)

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
      </div>
    </div>
  )
}
