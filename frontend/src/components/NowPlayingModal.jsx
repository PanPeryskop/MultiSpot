import { useEffect, useState, useRef } from 'react'
import { Play, Pause, SkipForward, SkipBack, X, Sparkles, Loader2 } from 'lucide-react'
import { ToastContext } from '../toast'
import { api } from '../api'
import styles from './NowPlayingModal.module.css'

const formatTime = (ms) => {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

function SeekBar({ position, duration, onSeek }) {
  const bar = useRef(null)
  const [drag, setDrag] = useState(null)

  const fractionAt = (clientX) => {
    const rect = bar.current.getBoundingClientRect()
    return Math.min(1, Math.max(0, (clientX - rect.left) / rect.width))
  }

  const down = (e) => {
    if (!duration) return
    e.currentTarget.setPointerCapture(e.pointerId)
    setDrag(fractionAt(e.clientX))
  }

  const move = (e) => {
    if (drag === null) return
    setDrag(fractionAt(e.clientX))
  }

  const up = (e) => {
    if (drag === null) return
    const fraction = fractionAt(e.clientX)
    setDrag(null)
    onSeek(Math.round(fraction * duration))
  }

  const shown = drag !== null ? drag * duration : position
  const pct = duration ? Math.min(100, (shown / duration) * 100) : 0

  return (
    <div className={styles.progressContainer}>
      <div
        ref={bar}
        className={`${styles.seek} ${drag !== null ? styles.seeking : ''}`}
        onPointerDown={down}
        onPointerMove={move}
        onPointerUp={up}
        onPointerCancel={() => setDrag(null)}
        role="slider"
        aria-label="Seek"
        aria-valuemin={0}
        aria-valuemax={Math.round(duration / 1000)}
        aria-valuenow={Math.round(shown / 1000)}
      >
        <div className={styles.seekTrack}>
          <div className={styles.progressFill} style={{ width: `${pct}%`, transition: drag !== null ? 'none' : undefined }} />
        </div>
        <div className={styles.seekThumb} style={{ left: `${pct}%` }} />
      </div>
      <div className={styles.timeRow}>
        <span className={drag !== null ? styles.timeActive : ''}>{formatTime(shown)}</span>
        <span>{formatTime(duration)}</span>
      </div>
    </div>
  )
}

export default function NowPlayingModal({ onClose }) {
  const [data, setData] = useState(null)
  const [base, setBase] = useState({ ms: 0, at: 0 })
  const [now, setNow] = useState(0)
  const [queue, setQueue] = useState([])
  const [loading, setLoading] = useState(false)
  const [conjuring, setConjuring] = useState(false)
  const modalRef = useRef(null)

  const fetchState = () => {
    api('/api/now-playing')
      .then(d => {
        setData(d.playing ? d : null)
        if (d.playing) setBase({ ms: d.track.progress_ms, at: Date.now() })
      })
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
    const poll = setInterval(fetchState, 3000)
    const tick = setInterval(() => setNow(Date.now()), 250)
    return () => {
      clearInterval(poll)
      clearInterval(tick)
    }
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

  const seek = async (ms) => {
    setBase({ ms, at: Date.now() })
    try {
      await api('/api/playback-seek', { method: 'POST', body: { position_ms: ms } })
      setTimeout(fetchState, 600)
    } catch (e) {
      ToastContext.push(e.message, 'error')
      fetchState()
    }
  }

  const moreLikeThis = async () => {
    setConjuring(true)
    try {
      const d = await api('/api/more-like-this', { method: 'POST', body: { count: 15 } })
      ToastContext.push(`Added ${d.added} tracks like ${d.seed?.name} after your queue`, 'success')
      fetchQueue()
    } catch (e) {
      ToastContext.push(e.message, 'error')
    } finally {
      setConjuring(false)
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
  const elapsed = is_playing && base.at ? Math.max(0, now - base.at) : 0
  const position = Math.min(track.duration_ms || 0, base.ms + elapsed)

  return (
    <div className={styles.overlay}>
      <div className={styles.modal} ref={modalRef}>
        <button className={styles.closeBtn} onClick={onClose} aria-label="Close">
          <X size={24} />
        </button>

        <div className={styles.artworkContainer}>
          {track.image ? (
            <img key={track.id} src={track.image} alt={track.album} className={`${styles.artwork} ${styles.artworkIn}`} />
          ) : (
            <div className={styles.artworkPlaceholder} />
          )}
        </div>

        <div className={styles.trackInfo} key={`info-${track.id}`}>
          <h2 className={styles.trackName}>{track.name}</h2>
          <p className={styles.artistName}>{track.artists.join(', ')}</p>
        </div>

        <SeekBar position={position} duration={track.duration_ms} onSeek={seek} />

        <div className={styles.controls}>
          <button className={styles.controlBtn} onClick={() => handleAction('/api/playback/previous')} disabled={loading}>
            <SkipBack size={28} />
          </button>
          <button
            className={`${styles.controlBtn} ${styles.playPauseBtn}`}
            onClick={() => handleAction(is_playing ? '/api/playback/pause' : '/api/playback/play')}
            disabled={loading}
          >
            {is_playing ? <Pause size={32} /> : <Play size={32} style={{ marginLeft: 4 }} />}
          </button>
          <button className={styles.controlBtn} onClick={() => handleAction('/api/playback/skip')} disabled={loading}>
            <SkipForward size={28} />
          </button>
        </div>

        {track.type !== 'episode' && (
          <button className={`btn btn-ghost ${styles.moreBtn}`} onClick={moreLikeThis} disabled={conjuring}>
            {conjuring ? <Loader2 size={16} className="spin" /> : <Sparkles size={16} />}
            {conjuring ? 'Finding similar…' : 'More like this'}
          </button>
        )}

        {queue.length > 0 && (
          <div className={styles.upNext}>
            <div className={styles.upNextTitle}>Up next</div>
            {queue.slice(0, 20).map((t, i) => (
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
