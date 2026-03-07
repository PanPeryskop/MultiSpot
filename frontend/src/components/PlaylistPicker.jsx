import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, Check } from 'lucide-react'
import styles from './PlaylistPicker.module.css'

export default function PlaylistPicker({ multi = false, selected = [], onChange }) {
  const [playlists, setPlaylists] = useState([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const limit = 5

  useEffect(() => {
    setLoading(true)
    fetch(`/api/playlists?limit=${limit}&offset=${offset}`, { credentials: 'include' })
      .then(r => r.json())
      .then(d => { setPlaylists(d.playlists); setTotal(d.total) })
      .finally(() => setLoading(false))
  }, [offset])

  const toggle = (pl) => {
    if (!multi) {
      onChange([pl])
      return
    }
    const exists = selected.find(s => s.url === pl.url)
    if (exists) {
      onChange(selected.filter(s => s.url !== pl.url))
    } else {
      onChange([...selected, pl])
    }
  }

  const pages = Math.ceil(total / limit)
  const page = Math.floor(offset / limit)

  return (
    <div className={styles.picker}>
      <div className={styles.header}>
        <span className={styles.title}>Your Playlists</span>
        {multi && <span className={styles.title} style={{ color: 'var(--text-secondary)' }}>{selected.length} Selected</span>}
      </div>
      
      <div className={styles.list}>
        {loading ? (
          <div className={styles.status}>Loading...</div>
        ) : playlists.length === 0 ? (
          <div className={styles.status}>No playlists found</div>
        ) : (
          playlists.map(pl => {
            const isSelected = selected.some(s => s.url === pl.url)
            return (
              <div 
                key={pl.id} 
                className={`${styles.item} ${isSelected ? styles.itemSelected : ''}`}
                onClick={() => toggle(pl)}
              >
                {pl.image ? (
                  <img src={pl.image} alt="" className={styles.image} />
                ) : (
                  <div className={styles.imagePlaceholder}>?</div>
                )}
                <div className={styles.info}>
                  <div className={styles.name}>{pl.name}</div>
                  <div className={styles.details}>{pl.tracks_total} Tracks</div>
                </div>
                {isSelected && <Check size={20} color="var(--green)" style={{ flexShrink: 0 }} />}
              </div>
            )
          })
        )}
      </div>

      {pages > 1 && (
        <div className={styles.controls}>
          <div className={styles.pages}>PAGE {page + 1} OF {pages}</div>
          <div className={styles.buttons}>
            <button className="btn btn-icon" onClick={() => setOffset(o => o - limit)} disabled={page === 0}>
              <ChevronLeft size={18} />
            </button>
            <button className="btn btn-icon" onClick={() => setOffset(o => o + limit)} disabled={page >= pages - 1}>
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
