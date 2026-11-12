import { useEffect, useRef, useState } from 'react'
import { Search, X, Dices } from 'lucide-react'
import { api } from '../api'
import styles from './GenrePicker.module.css'

export default function GenrePicker({ value, onChange }) {
  const [query, setQuery] = useState('')
  const [options, setOptions] = useState([])
  const [open, setOpen] = useState(false)
  const box = useRef(null)

  useEffect(() => {
    const controller = new AbortController()
    const id = setTimeout(() => {
      api(`/api/genres?limit=24&q=${encodeURIComponent(query)}`, { signal: controller.signal })
        .then(d => setOptions(d.genres || []))
        .catch(() => {})
    }, 180)
    return () => {
      clearTimeout(id)
      controller.abort()
    }
  }, [query])

  useEffect(() => {
    const close = (e) => {
      if (box.current && !box.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  const pick = (genre) => {
    onChange(genre)
    setQuery('')
    setOpen(false)
  }

  if (value) {
    return (
      <div className={`${styles.chosen} slide-up`}>
        <span className={styles.chosenLabel}>Genre</span>
        <span className={styles.chosenName}>{value}</span>
        <button type="button" className={styles.clear} onClick={() => onChange(null)} aria-label="Clear genre">
          <X size={16} />
        </button>
      </div>
    )
  }

  return (
    <div className={styles.picker} ref={box}>
      <div className={styles.inputRow}>
        <Search size={18} className={styles.icon} />
        <input
          className="input"
          style={{ paddingLeft: 44, width: '100%' }}
          placeholder="Any genre (leave empty for full chaos)"
          value={query}
          onFocus={() => setOpen(true)}
          onChange={e => { setQuery(e.target.value); setOpen(true) }}
        />
        <button
          type="button"
          className={`btn btn-ghost ${styles.dice}`}
          onClick={() => options.length && pick(options[Math.floor(Math.random() * options.length)])}
          title="Random genre"
        >
          <Dices size={18} />
        </button>
      </div>
      {open && options.length > 0 && (
        <div className={`${styles.menu} fade-in`}>
          {options.map(g => (
            <button type="button" key={g} className={styles.option} onClick={() => pick(g)}>
              {g}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
